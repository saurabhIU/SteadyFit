"""Ingestion: structure-aware chunking -> embeddings -> Postgres/pgvector."""
import json
from pathlib import Path

import psycopg
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import (MarkdownHeaderTextSplitter,
                                      RecursiveCharacterTextSplitter)
from pgvector.psycopg import register_vector

from app.config import settings

TABLE = "documents"
EMBED_DIM = 1536

headers = [("#", "h1"), ("##", "h2"), ("###", "h3")]
md_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers)
# ~750 tokens ≈ 3000 chars; overlap ~100 tokens ≈ 400 chars
char_splitter = RecursiveCharacterTextSplitter(chunk_size=3000, chunk_overlap=400)


def read_document(path: Path) -> str:
    """Load text from Markdown/plain text or PDF."""
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        parts: list[str] = []
        for i, page in enumerate(reader.pages):
            text = (page.extract_text() or "").strip()
            if text:
                # Fake H2 headers so the markdown splitter keeps page units when useful
                parts.append(f"## Page {i + 1}\n\n{text}")
        if not parts:
            raise ValueError(f"No extractable text in PDF: {path.name}")
        return "\n\n".join(parts)
    return path.read_text(errors="ignore")


def chunk_document(text: str, source: str) -> list[dict]:
    """Markdown-header first pass keeps whole workout days / recipes together."""
    chunks = []
    for doc in md_splitter.split_text(text):
        for piece in char_splitter.split_text(doc.page_content):
            chunks.append({"text": piece, "source": source, "meta": doc.metadata})
    return chunks


def ingest(path: str, doc_type: str = "program") -> int:
    file_path = Path(path)
    text = read_document(file_path)
    chunks = chunk_document(text, source=file_path.name)
    if not chunks:
        raise ValueError(f"No chunks produced from {file_path.name}")
    embedder = OpenAIEmbeddings(model="text-embedding-3-small",
                                api_key=settings.openai_api_key)
    vectors = embedder.embed_documents([c["text"] for c in chunks])
    with psycopg.connect(settings.database_url) as conn:
        register_vector(conn)
        # Re-ingesting the same file replaces its chunks (old Qdrant code upserted)
        conn.execute(f"DELETE FROM {TABLE} WHERE source = %s", (file_path.name,))
        with conn.cursor() as cur:
            cur.executemany(
                f"INSERT INTO {TABLE} (text, source, meta, doc_type, embedding) "
                f"VALUES (%s, %s, %s, %s, %s)",
                [(c["text"], c["source"], json.dumps(c["meta"]), doc_type, v)
                 for c, v in zip(chunks, vectors)],
            )
    return len(chunks)
