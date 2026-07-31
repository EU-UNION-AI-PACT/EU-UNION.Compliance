"""PDF renderer for stateless compliance validation reports.

Produces a compact, print-friendly A4 report from a validation dict and
attaches an ES256 signature (JWS-compact over the SHA-256 of the report
canonical JSON) so downstream auditors can verify integrity.

No I/O to disk — the caller receives a byte buffer.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
from datetime import datetime, timezone
from typing import Any

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import (
    decode_dss_signature,
)
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from services.signer_singleton import SignerSingleton

_AMBER = colors.HexColor("#f59e0b")
_NAVY = colors.HexColor("#0b1120")
_MUTED = colors.HexColor("#6b7280")
_OK = colors.HexColor("#059669")
_FAIL = colors.HexColor("#dc2626")
_WARN = colors.HexColor("#d97706")


def _b64u(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _canonical(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


async def sign_report(report: dict[str, Any]) -> dict[str, Any]:
    """Return a JWS-compact ES256 signature envelope over the report."""
    signer = await SignerSingleton.instance()
    canon = _canonical(report)
    digest = hashlib.sha256(canon).hexdigest()

    header = {"alg": "ES256", "typ": "compliance-report+jws", "kid": signer.kid}
    header_b64 = _b64u(_canonical(header))
    payload_b64 = _b64u(canon)
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")

    priv = signer.private_key
    der = priv.sign(signing_input, ec.ECDSA(hashes.SHA256()))
    r, s = decode_dss_signature(der)
    raw_sig = r.to_bytes(32, "big") + s.to_bytes(32, "big")
    sig_b64 = _b64u(raw_sig)
    jws = f"{header_b64}.{payload_b64}.{sig_b64}"

    return {
        "digest_sha256": digest,
        "algorithm": "ES256",
        "kid": signer.kid,
        "jws": jws,
        "signed_at": datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z"),
    }


def _status_color(status: str) -> colors.Color:
    if status == "PASS":
        return _OK
    if status == "PASS_WITH_WARNINGS":
        return _WARN
    if status == "FAIL":
        return _FAIL
    return _MUTED


def render_report_pdf(report: dict[str, Any], signature: dict[str, Any]) -> bytes:
    """Render a signed A4 PDF for a validation report."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        title="PNIA Compliance Report",
        author="PNIA Stateless Compliance Engine",
        leftMargin=1.6 * cm,
        rightMargin=1.6 * cm,
        topMargin=1.6 * cm,
        bottomMargin=1.6 * cm,
    )
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle(
        "h1", parent=styles["Title"], fontSize=18, spaceAfter=6, textColor=_NAVY
    )
    subtitle = ParagraphStyle(
        "sub",
        parent=styles["Normal"],
        fontSize=9,
        textColor=_MUTED,
        spaceAfter=12,
        fontName="Courier",
    )
    body = ParagraphStyle(
        "body", parent=styles["Normal"], fontSize=9, leading=12, textColor=_NAVY
    )
    mono = ParagraphStyle(
        "mono",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=8,
        leading=10,
        textColor=_NAVY,
    )
    label = ParagraphStyle(
        "label",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        textColor=_MUTED,
    )
    section_title = ParagraphStyle(
        "st",
        parent=styles["Heading2"],
        fontSize=11,
        textColor=_AMBER,
        spaceBefore=10,
        spaceAfter=6,
    )

    story: list = []

    fw = report.get("framework", {})
    if isinstance(fw, str):
        fw = {"code": fw}
    story.append(Paragraph("PNIA · Stateless Compliance Report", h1))
    story.append(
        Paragraph(
            f"Engine: {report.get('engine', 'PNIA')} · Evaluated: {report.get('evaluated_at', '—')}",
            subtitle,
        )
    )

    # Framework block
    story.append(Paragraph("Framework", section_title))
    fw_rows = [
        [Paragraph("Code", label), Paragraph(str(fw.get("code", "—")), mono)],
        [Paragraph("Name", label), Paragraph(str(fw.get("name", "—")), body)],
        [Paragraph("Regulator", label), Paragraph(str(fw.get("regulator", "—")), body)],
        [Paragraph("Jurisdiction", label), Paragraph(str(fw.get("jurisdiction", "—")), body)],
        [Paragraph("Category", label), Paragraph(str(fw.get("category", "—")), body)],
        [Paragraph("Source", label), Paragraph(str(fw.get("source", "—")), mono)],
        [Paragraph("Mode", label), Paragraph(str(report.get("mode", "—")), mono)],
    ]
    t = Table(fw_rows, colWidths=[3.2 * cm, 14 * cm])
    t.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e5e7eb")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f9fafb")),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(t)

    # Verdict
    story.append(Paragraph("Verdict", section_title))
    status = str(report.get("status", "—"))
    score = report.get("score", "—")
    counts = report.get("counts", {}) or {}
    _color_hex = {
        "PASS": "#059669",
        "PASS_WITH_WARNINGS": "#d97706",
        "FAIL": "#dc2626",
    }.get(status, "#6b7280")
    verdict_rows = [
        [
            Paragraph("Status", label),
            Paragraph(
                f'<font color="{_color_hex}"><b>{status}</b></font>',
                body,
            ),
            Paragraph("Score", label),
            Paragraph(f"{score} / 100", body),
        ],
        [
            Paragraph("Rules total", label),
            Paragraph(str(counts.get("rules_total", "—")), body),
            Paragraph("Required covered", label),
            Paragraph(
                f"{counts.get('covered_required', 0)} / {counts.get('required_total', 0)}",
                body,
            ),
        ],
        [
            Paragraph("Missing required", label),
            Paragraph(str(counts.get("missing_required", 0)), body),
            Paragraph("Recommended warnings", label),
            Paragraph(str(counts.get("recommended_warnings", 0)), body),
        ],
    ]
    t = Table(verdict_rows, colWidths=[3.2 * cm, 4.8 * cm, 3.6 * cm, 5.6 * cm])
    t.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e5e7eb")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(t)

    # Missing required
    missing = report.get("missing", []) or []
    if missing:
        story.append(Paragraph("Missing (required)", section_title))
        rows = [
            [Paragraph("Field", label), Paragraph("Statement of reasons (DSA Art. 17)", label)]
        ]
        for m in missing:
            rows.append(
                [
                    Paragraph(str(m.get("field", "")), mono),
                    Paragraph(str(m.get("hint", "")), body),
                ]
            )
        t = Table(rows, colWidths=[5 * cm, 12.2 * cm])
        t.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e5e7eb")),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#fef2f2")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(t)

    warnings = report.get("warnings", []) or []
    if warnings:
        story.append(Paragraph("Recommended", section_title))
        rows = [
            [Paragraph("Field", label), Paragraph("Hint", label)],
        ]
        for w in warnings:
            rows.append(
                [
                    Paragraph(str(w.get("field", "")), mono),
                    Paragraph(str(w.get("hint", "")), body),
                ]
            )
        t = Table(rows, colWidths=[5 * cm, 12.2 * cm])
        t.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e5e7eb")),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#fffbeb")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(t)

    covered = report.get("covered", []) or []
    if covered:
        story.append(Paragraph("Covered", section_title))
        chips = ", ".join(str(c.get("field", "")) for c in covered)
        story.append(Paragraph(chips, mono))

    # Signature block
    story.append(Spacer(1, 0.6 * cm))
    story.append(Paragraph("Cryptographic signature (ES256)", section_title))
    sig_rows = [
        [Paragraph("Algorithm", label), Paragraph(signature.get("algorithm", "ES256"), mono)],
        [Paragraph("kid", label), Paragraph(signature.get("kid", ""), mono)],
        [Paragraph("digest SHA-256", label), Paragraph(signature.get("digest_sha256", ""), mono)],
        [Paragraph("signed_at", label), Paragraph(signature.get("signed_at", ""), mono)],
        [Paragraph("JWS", label), Paragraph(signature.get("jws", ""), mono)],
    ]
    t = Table(sig_rows, colWidths=[3.2 * cm, 14 * cm])
    t.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e5e7eb")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f9fafb")),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(t)

    footer = ParagraphStyle(
        "footer",
        parent=styles["Normal"],
        fontSize=7,
        textColor=_MUTED,
        alignment=1,
    )
    story.append(Spacer(1, 0.4 * cm))
    story.append(
        Paragraph(
            "PNIA Stateless Compliance Engine · No database · EU AI Act Art. 12 record-keeping · "
            "DMA open API · DSA Art. 17 statement of reasons · GDPR data-minimisation.",
            footer,
        )
    )

    doc.build(story)
    return buf.getvalue()
