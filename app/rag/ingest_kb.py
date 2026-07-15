"""Curated Knowledge Base ingestion — section-aware chunking + metadata upsert.

  uv run python -m app.rag.ingest_kb data/knowledge_base/
"""
from __future__ import annotations

import argparse
import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

import psycopg
import yaml
from langchain_openai import OpenAIEmbeddings
from pgvector.psycopg import register_vector

from app.config import openai_api_key, settings
from app.rag.ingest import TABLE

logger = logging.getLogger("steadyfit.ingest_kb")

VOLUME_DOC_TYPE = {
    "Volume1-ExerciseLibrary": "kb_exercise",
    "Volume2-PopulationGuides": "kb_guide",
    "Volume3-WorkoutTemplates": "kb_template",
    "Volume4-MuscleEncyclopedia": "kb_science",
    "Volume6-ExerciseScience": "kb_science",
    "Volume7-NutritionScience": "kb_science",
}

# ~1200 tokens ≈ 4800 characters
MAX_SECTION_CHARS = 4800
YAML_FENCE_RE = re.compile(r"```yaml\s*(.*?)```", re.DOTALL | re.IGNORECASE)
H2_SPLIT_RE = re.compile(r"(?=^##\s+)", re.MULTILINE)
H3_SPLIT_RE = re.compile(r"(?=^###\s+)", re.MULTILINE)


@dataclass
class KbChunk:
    text: str
    doc_type: str
    source_file: str
    section: str
    kb_id: str | None = None
    muscle_primary: list[str] = field(default_factory=list)
    equipment: list[str] = field(default_factory=list)
    modality: list[str] = field(default_factory=list)
    difficulty: str | None = None
    contraindications: list[str] = field(default_factory=list)


def as_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            if isinstance(item, str) and item.strip():
                out.append(item.strip())
            elif item is not None:
                out.append(str(item))
        return out
    return [str(value)]


def parse_yaml_block(section: str) -> dict | None:
    """Extract and safe_load the first ```yaml block; skip on error."""
    match = YAML_FENCE_RE.search(section)
    if not match:
        return None
    raw = match.group(1).strip()
    try:
        data = yaml.safe_load(raw)
    except Exception as exc:
        logger.warning("malformed yaml skipped: %s", exc)
        return None
    return data if isinstance(data, dict) else None


def _heading_from_block(block: str, default: str = "") -> str:
    first = block.strip().splitlines()[0] if block.strip() else default
    return re.sub(r"^#+\s*", "", first).strip()


def split_on_h2(md: str) -> list[tuple[str, str]]:
    parts = [p for p in H2_SPLIT_RE.split(md) if p.strip()]
    out: list[tuple[str, str]] = []
    for part in parts:
        if not part.lstrip().startswith("##"):
            # preamble before first ## — skip or keep as intro
            continue
        heading = _heading_from_block(part)
        out.append((heading, part.strip()))
    return out


def split_on_h3(section: str) -> list[tuple[str, str]]:
    parts = [p for p in H3_SPLIT_RE.split(section) if p.strip()]
    out: list[tuple[str, str]] = []
    # Keep leading ## prose before first ### as its own chunk if present
    for part in parts:
        heading = _heading_from_block(part)
        if part.lstrip().startswith("###") or part.lstrip().startswith("##"):
            out.append((heading, part.strip()))
    return out or [(_heading_from_block(section), section.strip())]


def maybe_split_h3(heading: str, body: str) -> list[tuple[str, str]]:
    if len(body) <= MAX_SECTION_CHARS:
        return [(heading, body)]
    if "###" not in body:
        return [(heading, body)]
    return split_on_h3(body)


def doc_type_for(path: Path) -> str | None:
    for part in path.parts:
        if part in VOLUME_DOC_TYPE:
            return VOLUME_DOC_TYPE[part]
    return None


def chunk_kb_markdown(path: Path) -> list[KbChunk]:
    """One ## section = one chunk (or ### subchunks if oversized). No recursive splitter."""
    doc_type = doc_type_for(path)
    if not doc_type:
        return []
    text = path.read_text(errors="ignore")
    chunks: list[KbChunk] = []
    for heading, section in split_on_h2(text):
        for section_heading, section_text in maybe_split_h3(heading, section):
            meta = parse_yaml_block(section_text) or {}
            kb_id = meta.get("id")
            if kb_id is not None:
                kb_id = str(kb_id)
            chunks.append(KbChunk(
                text=section_text,
                doc_type=doc_type,
                source_file=path.name,
                section=section_heading,
                kb_id=kb_id,
                muscle_primary=as_list(meta.get("muscle_primary")),
                equipment=as_list(meta.get("equipment")),
                modality=as_list(meta.get("modality") or meta.get("equipment_modality")),
                difficulty=(
                    str(meta["difficulty"]) if meta.get("difficulty")
                    else (str(meta["level"]) if meta.get("level") else None)
                ),
                contraindications=as_list(meta.get("contraindications")),
            ))
    return chunks


def upsert_chunks(chunks: list[KbChunk], vectors: list[list[float]]) -> int:
    with psycopg.connect(settings.database_url) as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            for chunk, vec in zip(chunks, vectors):
                meta = {"section": chunk.section}
                if chunk.kb_id:
                    cur.execute(
                        f"DELETE FROM {TABLE} WHERE doc_type = %s AND kb_id = %s AND source_file = %s",
                        (chunk.doc_type, chunk.kb_id, chunk.source_file),
                    )
                else:
                    cur.execute(
                        f"DELETE FROM {TABLE} WHERE doc_type = %s AND source_file = %s "
                        f"AND meta->>'section' = %s AND kb_id IS NULL",
                        (chunk.doc_type, chunk.source_file, chunk.section),
                    )
                cur.execute(
                    f"""
                    INSERT INTO {TABLE} (
                        text, source, meta, doc_type, embedding,
                        kb_id, muscle_primary, equipment, modality,
                        difficulty, contraindications, source_file
                    ) VALUES (
                        %s, %s, %s::jsonb, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s
                    )
                    """,
                    (
                        chunk.text,
                        chunk.source_file,
                        json.dumps(meta),
                        chunk.doc_type,
                        vec,
                        chunk.kb_id,
                        chunk.muscle_primary or None,
                        chunk.equipment or None,
                        chunk.modality or None,
                        chunk.difficulty,
                        chunk.contraindications or None,
                        chunk.source_file,
                    ),
                )
        conn.commit()
    return len(chunks)


def ingest_kb_tree(root: Path) -> dict[str, int]:
    """Ingest all Volume*.md under root. Returns counts by volume folder."""
    md_files = sorted(
        p for p in root.rglob("*.md")
        if doc_type_for(p) and p.name.lower() != "readme.md"
    )
    counts: dict[str, int] = {}
    if not md_files:
        return counts

    embedder = OpenAIEmbeddings(model="text-embedding-3-small", api_key=openai_api_key)
    for path in md_files:
        chunks = chunk_kb_markdown(path)
        if not chunks:
            continue
        vectors = embedder.embed_documents([c.text for c in chunks])
        n = upsert_chunks(chunks, vectors)
        vol = next((p for p in path.parts if p.startswith("Volume")), path.parent.name)
        counts[vol] = counts.get(vol, 0) + n
        print(f"  {path.relative_to(root)}: {n} chunks")
    return counts


def main(argv: list[str] | None = None) -> None:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Ingest SteadyFit curated KB into pgvector")
    parser.add_argument(
        "root",
        nargs="?",
        default="data/knowledge_base",
        help="Path to knowledge_base folder",
    )
    args = parser.parse_args(argv)
    root = Path(args.root)
    if not root.is_dir():
        raise SystemExit(f"Not a directory: {root}")
    print(f"Ingesting KB from {root}…")
    counts = ingest_kb_tree(root)
    total = sum(counts.values())
    print("—")
    for vol, n in sorted(counts.items()):
        print(f"{vol}: {n}")
    print(f"Total chunks: {total}")


if __name__ == "__main__":
    main()
