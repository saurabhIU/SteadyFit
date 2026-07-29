"use client";

import { useCallback, useRef, useState } from "react";
import { FileText, Upload } from "lucide-react";
import { ApiError, uploadDocument } from "@/lib/api";
import { useProfile } from "@/lib/profile";
import { cn } from "@/lib/utils";

type UploadedFile = {
  id: string;
  name: string;
  status: "uploading" | "done" | "error";
  detail?: string;
};

const ACCEPT = ".md,.txt,.pdf,text/markdown,text/plain,application/pdf";

export function UploadPanel() {
  const { userId, ready } = useProfile();
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [error, setError] = useState<string | null>(null);

  const ingestFile = useCallback(
    async (file: File) => {
      if (!ready || !userId) {
        setError("Profile still loading — wait a moment and try again.");
        return;
      }
      const id = crypto.randomUUID();
      setFiles((prev) => [
        { id, name: file.name, status: "uploading" },
        ...prev,
      ]);
      setError(null);

      try {
        // Pass userId explicitly — never rely on a stale module default
        // (demo-veteran) if ProfileProvider hasn't synced yet.
        const data = await uploadDocument(file, { userId });
        setFiles((prev) =>
          prev.map((f) =>
            f.id === id
              ? {
                  ...f,
                  status: "done",
                  detail: `${data.ingested_chunks} chunks indexed for ${userId}`,
                }
              : f,
          ),
        );
      } catch (err) {
        const message =
          err instanceof ApiError
            ? `Upload failed (${err.status}): ${err.message}`
            : "Could not reach the backend — is it running on port 8000?";
        setFiles((prev) =>
          prev.map((f) => (f.id === id ? { ...f, status: "error", detail: message } : f)),
        );
        setError(message);
      }
    },
    [ready, userId],
  );

  function handleFiles(fileList: FileList | null) {
    if (!fileList?.length) return;
    void ingestFile(fileList[0]);
    if (inputRef.current) inputRef.current.value = "";
  }

  return (
    <div className="content-width space-y-6 py-6">
      <div>
        <h2 className="text-lg font-semibold text-navy-text">Update your library</h2>
        <p className="mt-1 text-sm text-navy-muted">
          Add a program, recipes, or notes — the knowledge agent will use them in chat.
        </p>
        <p className="mt-2 font-mono text-[11px] text-navy-muted/80">
          {ready
            ? `Uploading for profile: ${userId}`
            : "Loading profile…"}
        </p>
      </div>

      <div
        role="button"
        tabIndex={0}
        onClick={() => {
          if (!ready) return;
          inputRef.current?.click();
        }}
        onKeyDown={(e) => {
          if (!ready) return;
          if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
        }}
        onDragEnter={(e) => {
          e.preventDefault();
          if (ready) setDragActive(true);
        }}
        onDragOver={(e) => {
          e.preventDefault();
          if (ready) setDragActive(true);
        }}
        onDragLeave={(e) => {
          e.preventDefault();
          setDragActive(false);
        }}
        onDrop={(e) => {
          e.preventDefault();
          setDragActive(false);
          if (ready) handleFiles(e.dataTransfer.files);
        }}
        className={cn(
          "flex cursor-pointer flex-col items-center justify-center gap-3 rounded-2xl border border-dashed px-6 py-14 transition-colors",
          !ready && "pointer-events-none opacity-50",
          dragActive
            ? "border-sage bg-sage/10"
            : "border-beige-border bg-beige/40 hover:border-sage/40 hover:bg-beige/60",
        )}
      >
        <Upload className="size-8 text-sage" aria-hidden />
        <div className="text-center">
          <p className="text-sm font-medium text-card-text">
            Drop a file here, or click to browse
          </p>
          <p className="mt-1 font-mono text-[11px] text-card-text/50">
            .md · .txt · .pdf
          </p>
        </div>
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPT}
          className="hidden"
          disabled={!ready}
          onChange={(e) => handleFiles(e.target.files)}
        />
      </div>

      {error ? (
        <p className="text-sm text-red-300/90" role="alert">
          {error}
        </p>
      ) : null}

      {files.length > 0 ? (
        <ul className="space-y-2">
          {files.map((f) => (
            <li
              key={f.id}
              className="flex items-start gap-3 rounded-xl border border-beige-border bg-beige px-3 py-2.5"
            >
              <FileText className="mt-0.5 size-4 shrink-0 text-sage" aria-hidden />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-card-text">{f.name}</p>
                <p className="font-mono text-[11px] text-card-text/55">
                  {f.status === "uploading"
                    ? "Indexing…"
                    : f.status === "done"
                      ? f.detail
                      : f.detail || "Failed"}
                </p>
              </div>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
