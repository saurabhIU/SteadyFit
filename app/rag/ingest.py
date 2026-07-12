"""Ingestion: structure-aware chunking -> embeddings -> Postgres/pgvector."""
import json
from pathlib import Path

import psycopg
from pgvector.psycopg import register_vector
from langchain_text_splitters import (MarkdownHeaderTextSplitter,
                                      RecursiveCharacterTextSplitter)
from langchain_openai import OpenAIEmbeddings
from app.config import settings

TABLE = "documents"
EMBED_DIM = 1536

headers = [("#", "h1"), ("##", "h2"), ("###", "h3")]
md_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers)
# ~750 tokens ≈ 3000 chars; overlap ~100 tokens ≈ 400 chars
char_splitter = RecursiveCharacterTextSplitter(chunk_size=3000, chunk_overlap=400)


def chunk_document(text: str, source: str) -> list[dict]:
    """Markdown-header first pass keeps whole workout days / recipes together."""
    chunks = []
    for doc in md_splitter.split_text(text):
        for piece in char_splitter.split_text(doc.page_content):
            chunks.append({"text": piece, "source": source, "meta": doc.metadata})
    return chunks


def ingest(path: str, doc_type: str = "program"):
    text = Path(path).read_text(errors="ignore")   # TODO: pypdf for PDFs
    chunks = chunk_document(text, source=Path(path).name)
    embedder = OpenAIEmbeddings(model="text-embedding-3-small",
                                api_key=settings.openai_api_key)
    vectors = embedder.embed_documents([c["text"] for c in chunks])
    with psycopg.connect(settings.database_url) as conn:
        register_vector(conn)
        # Re-ingesting the same file replaces its chunks (old Qdrant code upserted)
        conn.execute(f"DELETE FROM {TABLE} WHERE source = %s", (Path(path).name,))
        with conn.cursor() as cur:
            cur.executemany(
                f"INSERT INTO {TABLE} (text, source, meta, doc_type, embedding) "
                f"VALUES (%s, %s, %s, %s, %s)",
                [(c["text"], c["source"], json.dumps(c["meta"]), doc_type, v)
                 for c, v in zip(chunks, vectors)],
            )
    return len(chunks)
