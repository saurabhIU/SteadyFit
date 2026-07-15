"""Helpers to collect KB citation metadata for the UI."""
from __future__ import annotations

import re

KB_TAG_RE = re.compile(r"\[KB:\s*(.+?)\s*[—-]\s*(.+?)\]")


def citations_from_texts(texts: list[str]) -> list[dict]:
    seen: set[tuple[str, str]] = set()
    out: list[dict] = []
    for text in texts:
        for match in KB_TAG_RE.finditer(text or ""):
            source_file = match.group(1).strip()
            section = match.group(2).strip()
            key = (source_file, section)
            if key in seen:
                continue
            seen.add(key)
            # Pull a short snippet after the tag when present
            start = match.end()
            snippet = re.sub(r"\s+", " ", (text[start:start + 240] or "")).strip()
            out.append({
                "source_file": source_file,
                "section": section,
                "kb_id": None,
                "snippet": snippet[:240],
                "tag": f"[KB: {source_file} — {section}]",
            })
    return out


def merge_citations(existing: list[dict], new: list[dict]) -> list[dict]:
    seen = {(c.get("source_file"), c.get("section")) for c in existing}
    out = list(existing)
    for c in new:
        key = (c.get("source_file"), c.get("section"))
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
    return out
