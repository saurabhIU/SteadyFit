"use client";

import { useState } from "react";
import { ApiError, sendApprove } from "@/lib/api";
import type { PendingApproval } from "@/lib/types";
import { cn } from "@/lib/utils";

type PlanApprovalCardProps = {
  approval: PendingApproval;
  threadId: string;
  onResolved: (reply: string) => void;
  onError: (message: string) => void;
};

export function PlanApprovalCard({
  approval,
  threadId,
  onResolved,
  onError,
}: PlanApprovalCardProps) {
  const [busy, setBusy] = useState(false);
  const [confirmation, setConfirmation] = useState<string | null>(null);
  const plan = approval.proposed_plan;

  async function decide(decision: "accept" | "reject") {
    setBusy(true);
    try {
      const data = await sendApprove(threadId, decision);
      setConfirmation(
        decision === "accept"
          ? "Plan saved — we'll keep you on track."
          : "No changes — your current week stays as is.",
      );
      onResolved(data.reply);
    } catch (err) {
      const message =
        err instanceof ApiError
          ? `Approval failed (${err.status}): ${err.message}`
          : "Could not reach the backend to save your decision.";
      onError(message);
    } finally {
      setBusy(false);
    }
  }

  const bullets: string[] = [];
  if (plan?.days.length) {
    for (const day of plan.days) {
      bullets.push(`${day.day}: ${day.focus} (${day.duration_min} min)`);
    }
  } else if (approval.scheduler_summary) {
    bullets.push(approval.scheduler_summary.slice(0, 200));
  }

  return (
    <div className="animate-enter max-w-[92%] rounded-2xl border border-beige-border bg-beige p-4 text-card-text">
      <h3 className="text-sm font-semibold text-card-text">
        A small tweak to your week
      </h3>
      <p className="mt-1.5 text-sm text-card-text/80">
        The council lined up these adjustments — only if they work for you.
      </p>

      {bullets.length > 0 ? (
        <ul className="mt-3 space-y-1.5 text-sm text-card-text/90">
          {bullets.map((item) => (
            <li key={item} className="flex gap-2">
              <span className="text-sage" aria-hidden>
                •
              </span>
              <span>{item}</span>
            </li>
          ))}
        </ul>
      ) : null}

      {plan?.notes ? (
        <p className="mt-2 text-xs text-card-text/60">{plan.notes}</p>
      ) : null}

      {confirmation ? (
        <p className="mt-4 font-mono text-xs text-sage">{confirmation}</p>
      ) : (
        <div className="mt-4 flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={() => decide("accept")}
            disabled={busy}
            className={cn(
              "rounded-[var(--radius-pill)] bg-sage px-5 py-2 text-sm font-medium text-sage-foreground",
              "transition-colors duration-150 ease-out hover:bg-sage-hover disabled:opacity-60",
            )}
          >
            Sounds good
          </button>
          <button
            type="button"
            onClick={() => decide("reject")}
            disabled={busy}
            className="text-sm text-card-text/60 underline-offset-2 transition-colors hover:text-card-text hover:underline disabled:opacity-60"
          >
            Keep my current plan
          </button>
        </div>
      )}
    </div>
  );
}
