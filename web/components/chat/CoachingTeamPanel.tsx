"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import { cn } from "@/lib/utils";
import type { CoachingTeamProposals } from "@/lib/types";

const AGENT_LABELS: Record<string, string> = {
  scheduler: "Scheduler",
  nutrition: "Nutrition",
  adherence: "Adherence",
  knowledge: "Knowledge",
  coach: "Coach",
};

type CoachingTeamPanelProps = {
  coachingTeam: CoachingTeamProposals;
  className?: string;
  defaultOpen?: boolean;
};

export function CoachingTeamPanel({
  coachingTeam,
  className,
  defaultOpen = false,
}: CoachingTeamPanelProps) {
  const [open, setOpen] = useState(defaultOpen);
  const entries = Object.entries(coachingTeam).filter(([, text]) => text?.trim());

  if (entries.length === 0) return null;

  return (
    <div className={cn("animate-enter w-full max-w-[92%]", className)}>
      <div className="overflow-hidden rounded-lg border border-beige-border/20 bg-team-panel">
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          className="flex w-full items-center justify-between gap-2 border-l-[3px] border-sage px-3 py-2.5 text-left transition-colors hover:bg-white/5"
          aria-expanded={open}
        >
          <span className="font-mono text-xs text-navy-muted">
            ◆ behind the glass — AI Coaching Team deliberation
          </span>
          <span className="flex shrink-0 items-center gap-1 font-mono text-[11px] text-navy-muted-dim">
            {open ? "hide" : "show"}
            {open ? (
              <ChevronUp className="size-3.5" aria-hidden />
            ) : (
              <ChevronDown className="size-3.5" aria-hidden />
            )}
          </span>
        </button>

        {open ? (
          <div className="space-y-2 border-l-[3px] border-sage/60 px-3 pb-3 pt-1">
            {entries.map(([agent, text]) => (
              <p key={agent} className="font-mono text-xs leading-relaxed">
                <span className="font-semibold text-navy-text">
                  {AGENT_LABELS[agent] ?? agent}
                </span>
                <span className="text-navy-muted"> — {text}</span>
              </p>
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
}
