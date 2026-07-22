"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import { cn } from "@/lib/utils";
import type { CoachingTeamChip, CoachingTeamProposals } from "@/lib/types";

const AGENT_LABELS: Record<string, string> = {
  scheduler: "Scheduler",
  nutrition: "Nutrition",
  adherence: "Adherence",
  knowledge: "Knowledge",
  coach: "Coach",
};

function chipLabel(entry: CoachingTeamChip): string {
  const agent = AGENT_LABELS[entry.agent] ?? entry.agent;
  if (entry.type === "critique") return "Coach flagged";
  if (entry.type === "revision") return `${agent} revised`;
  if (entry.type === "proposal") return `${agent} draft`;
  return agent;
}

function toEntries(coachingTeam: CoachingTeamProposals): CoachingTeamChip[] {
  if (Array.isArray(coachingTeam)) {
    return coachingTeam.filter((e) => e?.text?.trim());
  }
  return Object.entries(coachingTeam)
    .filter(([, text]) => text?.trim())
    .map(([agent, text]) => ({
      type: agent === "critique" ? "critique" : "proposal",
      agent: agent === "critique" ? "coach" : agent,
      text,
    }));
}

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
  const entries = toEntries(coachingTeam);

  if (entries.length === 0) return null;

  const hasCritiqueExchange = entries.some((e) => e.type === "critique");

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
            {hasCritiqueExchange ? " · critique → revise" : ""}
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
            {entries.map((entry, idx) => (
              <p
                key={`${entry.type}-${entry.agent}-${idx}`}
                className={cn(
                  "font-mono text-xs leading-relaxed",
                  entry.type === "critique" && "text-amber-200/90",
                )}
              >
                <span className="font-semibold text-navy-text">
                  {chipLabel(entry)}
                </span>
                <span className="text-navy-muted"> — {entry.text}</span>
              </p>
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
}
