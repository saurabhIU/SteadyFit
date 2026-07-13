"use client";

import { useCallback, useRef, useState } from "react";
import { FileText, Upload } from "lucide-react";
import { ApiError, uploadDocument } from "@/lib/api";
import { cn } from "@/lib/utils";

type UploadedFile = {
  id: string;
  name: string;
  status: "uploading" | "done" | "error";
  detail?: string;
};

const ACCEPT = ".md,.txt,.pdf,text/markdown,text/plain,application/pdf";

export function UploadPanel() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [error, setError] = useState<string | null>(null);

  const ingestFile = useCallback(async (file: File) => {
    const id = crypto.randomUUID();
    setFiles((prev) => [
      { id, name: file.name, status: "uploading" },
      ...prev,
    ]);
    setError(null);

    try {
      const data = await uploadDocument(file);
      setFiles((prev) =>
        prev.map((f) =>
          f.id === id
            ? {
                ...f,
                status: "done",
                detail: `${data.ingested_chunks} chunks indexed`,
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
  }, []);

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
      </div>

      <div
        role="button"
        tabIndex={0}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
        }}
        onDragEnter={(e) => {
          e.preventDefault();
          setDragActive(true);
        }}
        onDragOver={(e) => {
          e.preventDefault();
          setDragActive(true);
        }}
        onDragLeave={(e) => {
          e.preventDefault();
          setDragActive(false);
        }}
        onDrop={(e) => {
          e.preventDefault();
          setDragActive(false);
          handleFiles(e.dataTransfer.files);
        }}
        className={cn(
          "flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed px-6 py-14 text-center transition-colors duration-150 ease-out",
          dragActive
            ? "border-sage bg-beige"
            : "border-beige-border/50 bg-beige/90 hover:border-beige-border hover:bg-beige",
        )}
      >
        <div className="mb-4 flex size-12 items-center justify-center rounded-xl border border-beige-border bg-beige">
          <Upload className="size-5 text-card-text/50" strokeWidth={1.5} />
        </div>
        <p className="text-sm font-medium text-card-text">
          Drag a file here, or click to browse
        </p>
        <p className="mt-1.5 font-mono text-xs text-card-text/50">
          .md · .txt · .pdf
        </p>
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPT}
          className="sr-only"
          onChange={(e) => handleFiles(e.target.files)}
        />
      </div>

      {error ? (
        <p className="rounded-2xl border border-beige-border/30 bg-council px-4 py-3 text-sm text-navy-muted">
          {error}
        </p>
      ) : null}

      {files.length > 0 ? (
        <div className="space-y-2">
          <p className="font-mono text-xs text-navy-muted-dim">Uploaded files</p>
          <ul className="space-y-2">
            {files.map((file) => (
              <li
                key={file.id}
                className="flex items-center gap-3 rounded-2xl border border-beige-border bg-beige px-4 py-3"
              >
                <FileText className="size-4 shrink-0 text-card-text/45" />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium text-card-text">
                    {file.name}
                  </p>
                  <p
                    className={cn(
                      "font-mono text-xs",
                      file.status === "error"
                        ? "text-neutral"
                        : file.status === "uploading"
                          ? "text-card-text/50"
                          : "text-sage",
                    )}
                  >
                    {file.status === "uploading"
                      ? "Ingesting…"
                      : (file.detail ?? "Ready")}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      <p className="text-sm text-navy-muted-dim">
        After uploading, try asking &quot;What does my program say about deload week?&quot;
        in chat.
      </p>
    </div>
  );
}
