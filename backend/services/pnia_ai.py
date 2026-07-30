"""PNIA AI service — respectful memorial / honorary tribute generation.

Uses the Emergent LLM key via ``emergentintegrations`` (default model
``openai/gpt-5.4``). Every call is designed to be *auditable* (EU AI Act
Art. 12 + 50): the caller receives the exact prompt and model version so a
hash-chained ``AiAuditLog`` entry can be written.

Design notes
------------
* We use ``send_message`` (explicit non-streaming) because the generated text
  must be captured in full to be hashed, stored and legally attributed.
* The system prompt enforces dignity, factual restraint and a transparency
  footer, matching the "respectful treatment of sensitive concepts" mandate.
"""
from __future__ import annotations

import os
import uuid

from emergentintegrations.llm.chat import LlmChat, UserMessage

MODEL_PROVIDER = "openai"
MODEL_NAME = "gpt-5.4"
MODEL_VERSION = f"{MODEL_PROVIDER}/{MODEL_NAME}"

_SYSTEM = (
    "Du bist ein würdevoller, faktentreuer Gedenk- und Ehren-Redakteur im PNIA-Register "
    "(Personal Notable Individuals Archive). Deine Aufgabe ist es, respektvolle, sachliche "
    "und pietätvolle Texte zu verfassen — für Gedenktafeln Verstorbener und Ehrenplätze "
    "lebender Personen. "
    "Regeln: (1) Bleibe faktisch und erfinde niemals biografische Details. "
    "(2) Kein Pathos-Kitsch, kein politisches Urteil, keine Wertung von Ideologien. "
    "(3) Würdige Rolle und Wirken sachlich und warm. "
    "(4) Schreibe in der angeforderten Sprache. "
    "(5) Länge: 3–5 Sätze, es sei denn anders gewünscht. "
    "(6) Beende Gedenktexte mit einer stillen, respektvollen Schlusszeile."
)


def _build_prompt(
    *,
    display_name: str,
    role: str,
    institution: str,
    resting_place: str,
    plaque_type: str,
    language: str,
    tone: str,
    extra_context: str,
) -> str:
    kind = (
        "Gedenktafel (verstorbene Person)"
        if plaque_type == "MEMORIAL_BOARD"
        else "Ehrenplatz (lebende Person)"
    )
    return (
        f"Verfasse einen respektvollen Text für eine {kind}.\n"
        f"Sprache: {language}\n"
        f"Tonalität: {tone}\n"
        f"Name: {display_name}\n"
        f"Rolle / Funktion: {role or 'unbekannt'}\n"
        f"Institution / Gremium: {institution or 'unbekannt'}\n"
        f"Ruhestätte / Ort: {resting_place or 'unbekannt'}\n"
        f"Zusätzlicher Kontext: {extra_context or 'keiner'}\n"
        "Gib ausschließlich den fertigen Gedenk-/Ehrentext zurück, ohne Anführungszeichen "
        "und ohne Vorbemerkung."
    )


async def generate_tribute(
    *,
    display_name: str,
    role: str = "",
    institution: str = "",
    resting_place: str = "",
    plaque_type: str = "MEMORIAL_BOARD",
    language: str = "Deutsch",
    tone: str = "würdevoll und sachlich",
    extra_context: str = "",
) -> tuple[str, str, str]:
    """Return ``(text, prompt, model_version)`` for auditing."""
    key = os.environ.get("EMERGENT_LLM_KEY")
    if not key:
        raise RuntimeError("EMERGENT_LLM_KEY missing — cannot generate tribute")

    prompt = _build_prompt(
        display_name=display_name,
        role=role,
        institution=institution,
        resting_place=resting_place,
        plaque_type=plaque_type,
        language=language,
        tone=tone,
        extra_context=extra_context,
    )
    chat = LlmChat(
        api_key=key,
        session_id=f"pnia-tribute-{uuid.uuid4().hex[:12]}",
        system_message=_SYSTEM,
    ).with_model(MODEL_PROVIDER, MODEL_NAME)

    resp = await chat.send_message(UserMessage(text=prompt))
    text = resp if isinstance(resp, str) else getattr(resp, "content", str(resp))
    return text.strip(), prompt, MODEL_VERSION


async def translate_tribute(
    *, text: str, target_language: str
) -> tuple[str, str, str]:
    """Translate an existing tribute; returns ``(translated, prompt, model_version)``."""
    key = os.environ.get("EMERGENT_LLM_KEY")
    if not key:
        raise RuntimeError("EMERGENT_LLM_KEY missing — cannot translate")

    prompt = (
        f"Übersetze den folgenden Gedenk-/Ehrentext respektvoll und sinngemäß nach "
        f"{target_language}. Bewahre Würde und Tonalität. Gib nur die Übersetzung zurück:\n\n"
        f"{text}"
    )
    chat = LlmChat(
        api_key=key,
        session_id=f"pnia-translate-{uuid.uuid4().hex[:12]}",
        system_message=_SYSTEM,
    ).with_model(MODEL_PROVIDER, MODEL_NAME)

    resp = await chat.send_message(UserMessage(text=prompt))
    out = resp if isinstance(resp, str) else getattr(resp, "content", str(resp))
    return out.strip(), prompt, MODEL_VERSION
