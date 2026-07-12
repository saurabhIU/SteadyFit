"use client";

import { useState } from "react";
import { ApiError, sendApprove } from "@/lib/api";
import type { PendingApproval } from "@/lib/types";

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
  const plan = approval.proposed_plan;

  async function decide(decision: "accept" | "reject") {
    setBusy(true);
    try {
      const data = await sendApprove(threadId, decision);
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

  return (
    <div className="rounded-lg border border-lift/50 bg-paper/80 p-4 shadow-sm">
      <p className="font-mono text-[10px] font-bold uppercase tracking-wider text-lift">
        plan change — your approval needed
      </p>
      <p className="mt-2 text-sm text-ink">
        The scheduler proposed an updated week. Accept to save it, or decline to keep your
        current plan.
      </p>

      {plan ? (
        <div className="mt-3 space-y-1.5 rounded border border-line bg-white/60 px-3 py-2.5 text-sm">
          <p className="font-mono text-[11px] text-steel">
            week of {plan.week_start}
            {plan.calorie_target ? ` · ${plan.calorie_target} kcal` : ""}
            {plan.protein_target_g ? ` · ${plan.protein_target_g}g protein` : ""}
          </p>
          <ul className="space-y-1">
            {plan.days.map((day) => (
              <li key={`${day.day}-${day.focus}`} className="flex justify-between gap-3">
                <span>
                  <span className="font-medium text-ink">{day.day}</span>{" "}
                  <span className="text-steel">{day.focus}</span>
                </span>
                <span className="shrink-0 font-mono text-xs text-steel">
                  {day.duration_min}m
                </span>
              </li>
            ))}
          </ul>
          {plan.notes ? <p className="text-xs text-steel">{plan.notes}</p> : null}
        </div>
      ) : approval.scheduler_summary ? (
        <p className="mt-3 whitespace-pre-wrap text-sm text-steel">
          {approval.scheduler_summary.slice(0, 400)}
        </p>
      ) : null}

      <div className="mt-4 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => decide("accept")}
          disabled={busy}
          className="rounded bg-lift px-3.5 py-2 text-sm font-medium text-white transition hover:opacity-90 disabled:opacity-60"
        >
          Accept plan
        </button>
        <button
          type="button"
          onClick={() => decide("reject")}
          disabled={busy}
          className="rounded border border-line bg-white px-3.5 py-2 text-sm text-ink transition hover:bg-paper disabled:opacity-60"
        >
          Keep current plan
        </button>
      </div>
    </div>
  );
}
