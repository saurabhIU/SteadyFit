"use client";

import { useState } from "react";
import Link from "next/link";
import { ApiError, uploadDocument } from "@/lib/api";

export function UploadPanel() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleUpload() {
    if (!file || loading) return;
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const data = await uploadDocument(file);
      setResult(`Ingested ${data.ingested_chunks} chunks from ${file.name}.`);
      setFile(null);
    } catch (err) {
      const message =
        err instanceof ApiError
          ? `Upload failed (${err.status}): ${err.message}`
          : "Could not reach the backend — is it running on port 8000?";
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto w-full max-w-3xl px-5 py-6">
      <div className="mb-6">
        <p className="font-mono text-[10px] font-bold uppercase tracking-wider text-lift">
          knowledge base
        </p>
        <h2 className="mt-1 text-xl font-semibold text-ink">Upload your docs</h2>
        <p className="mt-1 text-sm text-steel">
          Add your training program, recipes, or notes. The knowledge agent uses them for
          personal RAG answers.
        </p>
      </div>

      <div className="rounded-lg border border-line bg-white/60 p-5">
        <label className="block font-mono text-[11px] uppercase tracking-wider text-steel">
          file (.md, .txt, .pdf)
          <input
            type="file"
            accept=".md,.txt,.pdf,text/markdown,text/plain,application/pdf"
            className="mt-2 block w-full text-sm text-ink file:mr-3 file:rounded file:border-0 file:bg-lift file:px-3 file:py-1.5 file:text-sm file:font-medium file:text-white"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
        </label>

        <div className="mt-4 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={handleUpload}
            disabled={!file || loading}
            className="rounded bg-lift px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            {loading ? "ingesting…" : "upload & ingest"}
          </button>
          <Link
            href="/chat"
            className="rounded border border-line px-4 py-2 text-sm text-ink hover:bg-paper"
          >
            back to chat
          </Link>
        </div>

        {result ? (
          <p className="mt-4 rounded border border-emerald-300/50 bg-emerald-50 px-3 py-2 text-sm text-emerald-900">
            {result}
          </p>
        ) : null}
        {error ? (
          <p className="mt-4 rounded border border-lift/40 bg-lift/10 px-3 py-2 text-sm text-ink">
            {error}
          </p>
        ) : null}
      </div>

      <p className="mt-4 font-mono text-[11px] text-steel">
        Tip: try asking &quot;What does my program say about deload week?&quot; in chat after
        uploading your program.
      </p>
    </div>
  );
}
