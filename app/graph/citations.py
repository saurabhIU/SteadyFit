"""Helpers to collect KB / Memory citation metadata for the UI."""
from __future__ import annotations

import re

KB_TAG_RE = re.compile(r"\[KB:\s*(.+?)\s*[—-]\s*(.+?)\]")
MEMORY_TAG_RE = re.compile(
    r"\[Memory:\s*week of\s*(\d{4}-\d{2}-\d{2})\]",
    re.IGNORECASE,
)


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
            start = match.end()
            snippet = re.sub(r"\s+", " ", (text[start:start + 240] or "")).strip()
            out.append({
                "source_file": source_file,
                "section": section,
                "kb_id": None,
                "snippet": snippet[:240],
                "tag": f"[KB: {source_file} — {section}]",
                "kind": "kb",
            })
        for match in MEMORY_TAG_RE.finditer(text or ""):
            week = match.group(1)
            source_file = f"week_{week}"
            section = f"week of {week}"
            key = (source_file, section)
            if key in seen:
                continue
            seen.add(key)
            start = match.end()
            snippet = re.sub(r"\s+", " ", (text[start:start + 240] or "")).strip()
            out.append({
                "source_file": source_file,
                "section": section,
                "kb_id": None,
                "snippet": snippet[:240],
                "tag": f"[Memory: week of {week}]",
                "kind": "memory",
            })
    return out


def merge_citations(*groups: list[dict]) -> list[dict]:
    """Merge one or more citation lists, de-dupe by (source_file, section)."""
    seen: set[tuple[str | None, str | None]] = set()
    out: list[dict] = []
    for group in groups:
        for c in group or []:
            key = (c.get("source_file"), c.get("section"))
            if key in seen:
                continue
            seen.add(key)
            out.append(c)
    return out
