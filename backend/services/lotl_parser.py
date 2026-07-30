"""ETSI TS 119 612 (EU List of Trusted Lists) XML parser — minimal but real.

Focus: extract SchemeInformation, TSL sequence number, next update date, and
service digital identities (certificates + subject/key info).

The XML uses namespaces we handle explicitly; no local-name() hacks.
"""
from __future__ import annotations

import base64
import hashlib
from datetime import datetime
from typing import Any

from lxml import etree

NS = {
    "tsl": "http://uri.etsi.org/02231/v2#",
    "ds": "http://www.w3.org/2000/09/xmldsig#",
    "ecc": "http://uri.etsi.org/02231/v2/additionaltypes#",
}


def _text(elem, xpath: str) -> str | None:
    node = elem.find(xpath, namespaces=NS)
    return node.text.strip() if node is not None and node.text else None


def parse_lotl_xml(xml: str) -> dict[str, Any]:
    root = etree.fromstring(xml.encode() if isinstance(xml, str) else xml)
    scheme_info = root.find("tsl:SchemeInformation", namespaces=NS)
    if scheme_info is None:
        raise ValueError("SchemeInformation element missing")
    territory = _text(scheme_info, "tsl:SchemeTerritory") or "??"
    seq_number = int(_text(scheme_info, "tsl:TSLSequenceNumber") or "0")
    issue_date_raw = _text(scheme_info, "tsl:ListIssueDateTime") or ""
    next_update_raw = (
        _text(scheme_info, "tsl:NextUpdate/tsl:dateTime")
        or _text(scheme_info, "tsl:NextUpdate")
        or ""
    )
    # scheme operator name — pick first
    op_names = scheme_info.findall(
        "tsl:SchemeOperatorName/tsl:Name", namespaces=NS
    )
    op = op_names[0].text.strip() if op_names else "unknown"

    anchors: list[dict[str, Any]] = []
    for tsp in root.findall(".//tsl:TrustServiceProvider", namespaces=NS):
        tsp_name_nodes = tsp.findall("tsl:TSPInformation/tsl:TSPName/tsl:Name", namespaces=NS)
        tsp_name = tsp_name_nodes[0].text.strip() if tsp_name_nodes else "unknown"
        for svc in tsp.findall(".//tsl:TSPService", namespaces=NS):
            svc_name_nodes = svc.findall(
                "tsl:ServiceInformation/tsl:ServiceName/tsl:Name", namespaces=NS
            )
            svc_name = svc_name_nodes[0].text.strip() if svc_name_nodes else "unknown"
            svc_type = _text(svc, "tsl:ServiceInformation/tsl:ServiceTypeIdentifier") or ""
            # Digital identities — X509Certificate
            for cert_b64 in svc.findall(
                ".//tsl:DigitalId/tsl:X509Certificate", namespaces=NS
            ):
                der = base64.b64decode((cert_b64.text or "").strip())
                fp = hashlib.sha256(der).hexdigest()
                anchors.append(
                    {
                        "tsp_name": tsp_name,
                        "service_name": svc_name,
                        "service_type": svc_type,
                        "der_b64": base64.b64encode(der).decode(),
                        "fingerprint_sha256": fp,
                        "country_code": territory,
                    }
                )
    return {
        "territory": territory,
        "scheme_operator": op,
        "sequence_number": seq_number,
        "issue_date": issue_date_raw,
        "next_update": next_update_raw,
        "anchor_count": len(anchors),
        "anchors": anchors,
    }


def utc_iso_or_none(raw: str) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
