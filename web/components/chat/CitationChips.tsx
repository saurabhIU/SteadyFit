"use client";

import { useState } from "react";
import type { Citation } from "@/lib/types";
import { cn } from "@/lib/utils";

export function CitationChips({ citations }: { citations: Citation[] }) {
  const [openKey, setOpenKey] = useState<string | null>(null);
  if (!citations.length) return null;

  return (
    <div className="ml-1 flex flex-col gap-2">
      <div className="flex flex-wrap gap-1.5">
        {citations.map((c) => {
          const key = `${c.source_file}::${c.section}`;
          const label = c.section
            ? `${c.source_file} — ${c.section}`
            : c.source_file;
          const active = openKey === key;
          return (
            <button
              key={key}
              type="button"
              onClick={() => setOpenKey(active ? null : key)}
              className={cn(
                "rounded-[var(--radius-pill)] border px-2.5 py-1 font-mono text-[10px] tracking-tight transition-colors",
                active
                  ? "border-sage bg-sage/20 text-navy-text"
                  : "border-sage/50 bg-transparent text-sage hover:bg-sage/10",
              )}
            >
              {label}
            </button>
          );
        })}
      </div>
      {citations.map((c) => {
        const key = `${c.source_file}::${c.section}`;
        if (openKey !== key) return null;
        return (
          <div
            key={`${key}-panel`}
            className="rounded-xl border border-beige-border/40 bg-team-panel px-3 py-2 text-xs text-navy-muted"
          >
            <p className="font-mono text-[10px] text-sage">
              {c.tag || `[KB: ${c.source_file} — ${c.section}]`}
            </p>
            <p className="mt-1 leading-relaxed text-navy-text/80">
              {c.snippet || "Retrieved from SteadyFit knowledge base."}
            </p>
          </div>
        );
      })}
    </div>
  );
}
