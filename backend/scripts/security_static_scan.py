"""CI Gate 3 — static scan for hardcoded secrets / mock_ residue."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
EXCLUDE_DIRS = {"__pycache__", ".git", "node_modules", "dist", "build"}
EXCLUDE_NAMES = {".env"}
# Any 40+ char high-entropy string that looks like a base64 secret assignment.
PATTERNS = [
    re.compile(r"MASTER_KEY\s*=\s*['\"][A-Za-z0-9+/=]{40,}['\"]"),
    re.compile(r"['\"]sk-[A-Za-z0-9]{20,}['\"]"),  # OpenAI-style
    re.compile(r"mock_[a-zA-Z_]+"),
    re.compile(r"TODO:security", re.IGNORECASE),
    re.compile(r"password\s*=\s*['\"][^'\"]{6,}['\"]", re.IGNORECASE),
]


def scan_file(p: Path) -> list[tuple[int, str, str]]:
    hits: list[tuple[int, str, str]] = []
    try:
        text = p.read_text(errors="ignore")
    except Exception:
        return hits
    for i, line in enumerate(text.splitlines(), 1):
        for pat in PATTERNS:
            if pat.search(line):
                hits.append((i, pat.pattern, line.strip()))
    return hits


def main() -> int:
    failed = False
    for p in ROOT.rglob("*"):
        if p.is_dir():
            continue
        if any(part in EXCLUDE_DIRS for part in p.parts):
            continue
        if p.name in EXCLUDE_NAMES:
            continue
        if p.suffix not in (".py",):
            continue
        for lineno, pat, line in scan_file(p):
            print(f"[FAIL] {p}:{lineno} ({pat}) → {line}")
            failed = True
    if failed:
        return 1
    print("[OK] no hardcoded secrets, mock_, or TODO:security markers found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
