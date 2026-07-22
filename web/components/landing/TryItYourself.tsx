"use client";

import { useState } from "react";
import { createTryProfile } from "@/lib/api";
import { cn } from "@/lib/utils";

export function TryItYourself() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onTry() {
    setError(null);
    setLoading(true);
    try {
      const { user_id } = await createTryProfile();
      // Full navigation so ProfileProvider bootstraps with ?profile=try-…
      window.location.href = `/chat?profile=${encodeURIComponent(user_id)}`;
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Could not start a try session";
      setError(message);
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col items-center gap-3">
      <button
        type="button"
        onClick={onTry}
        disabled={loading}
        className={cn(
          "rounded-[var(--radius-pill)] bg-sage px-6 py-2.5 text-sm font-medium text-sage-foreground",
          "transition-opacity hover:opacity-90 disabled:opacity-60",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sage/50",
        )}
      >
        {loading ? "Starting…" : "Try it yourself"}
      </button>
      <p className="max-w-sm text-center font-mono text-xs text-navy-muted">
        No sign-up — try a real conversation right now.
      </p>
      {error ? (
        <p className="max-w-sm text-center text-xs text-red-300/90" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}
