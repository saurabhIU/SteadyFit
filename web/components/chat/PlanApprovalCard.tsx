"use client";

import { useState } from "react";
import { ApiError, sendApprove } from "@/lib/api";
import type { PendingApproval } from "@/lib/types";
import { cn } from "@/lib/utils";

type PlanApprovalCardProps = {
  approval: PendingApproval;
  threadId: string;
  userId: string;
  onResolved: (reply: string) => void;
  onError: (message: string) => void;
};

export function PlanApprovalCard({
  approval,
  threadId,
  userId,
  onResolved,
  onError,
}: PlanApprovalCardProps) {
  const [busy, setBusy] = useState(false);
  const [confirmation, setConfirmation] = useState<string | null>(null);
  const plan = approval.proposed_plan;
  const isFirst = Boolean(approval.is_first_plan);
  const personalizationNote =
    approval.personalization_note?.trim() ||
    (approval.subhead?.includes("uploaded a personal document")
      ? approval.subhead.trim()
      : "");
  const headline =
    approval.headline?.trim() ||
    (isFirst ? "Here's your first week" : "A small tweak to your week");
  const defaultSubhead = isFirst
    ? "The AI Coaching Team drafted this starting plan — only if it works for you."
    : "The AI Coaching Team lined up these adjustments — only if they work for you.";
  const subhead = personalizationNote
    ? personalizationNote
    : approval.subhead?.trim() || defaultSubhead;
  const rejectLabel = isFirst ? "Not yet" : "Keep my current plan";

  const calorie =
    approval.calorie_target ??
    approval.tdee_targets?.calorie_target ??
    plan?.calorie_target ??
    null;
  const protein =
    approval.protein_target_g ??
    approval.tdee_targets?.protein_target_g ??
    plan?.protein_target_g ??
    null;
  const dietSummary = approval.diet_plan_summary ?? [];
  const dietMeals = approval.proposed_diet_plan ?? [];
  const isEstimate = Boolean(approval.tdee_targets?.is_estimate);

  async function decide(decision: "accept" | "reject") {
    setBusy(true);
    try {
      const data = await sendApprove(threadId, decision, { userId });
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

  const workoutBullets: string[] = [];
  if (plan?.days.length) {
    for (const day of plan.days) {
      workoutBullets.push(`${day.day}: ${day.focus} (${day.duration_min} min)`);
    }
  } else if (approval.scheduler_summary) {
    workoutBullets.push(approval.scheduler_summary.slice(0, 200));
  }

  const mealBullets =
    dietSummary.length > 0
      ? dietSummary.filter((line) => !line.startsWith("Sources:"))
      : dietMeals.slice(0, 6).map(
          (m) => `${m.day} ${m.meal_slot}: ${m.food_description}`,
        );

  return (
    <div className="animate-enter max-w-[92%] rounded-2xl border border-beige-border bg-beige p-4 text-card-text">
      <h3 className="text-sm font-semibold text-card-text">
        {headline}
      </h3>
      {personalizationNote ? (
        <p className="mt-2 rounded-lg border border-sage/30 bg-sage/10 px-3 py-2 text-sm text-card-text">
          {personalizationNote}
        </p>
      ) : (
        <p className="mt-1.5 text-sm text-card-text/80">{subhead}</p>
      )}

      {calorie != null || protein != null ? (
        <p className="mt-3 font-mono text-sm text-card-text/90">
          {calorie != null ? `${calorie} kcal` : "— kcal"}
          {" · "}
          {protein != null ? `${protein}g protein` : "—g protein"}
          {isEstimate ? (
            <span className="text-card-text/60"> (starting estimate)</span>
          ) : null}
        </p>
      ) : null}

      {workoutBullets.length > 0 ? (
        <div className="mt-3">
          <p className="text-xs font-medium uppercase tracking-wide text-card-text/50">
            Workouts
          </p>
          <ul className="mt-1.5 space-y-1.5 text-sm text-card-text/90">
            {workoutBullets.map((item) => (
              <li key={item} className="flex gap-2">
                <span className="text-sage" aria-hidden>
                  •
                </span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {mealBullets.length > 0 ? (
        <div className="mt-3">
          <p className="text-xs font-medium uppercase tracking-wide text-card-text/50">
            Meals
          </p>
          <ul className="mt-1.5 space-y-1.5 text-sm text-card-text/90">
            {mealBullets.map((item) => (
              <li key={item} className="flex gap-2">
                <span className="text-sage" aria-hidden>
                  •
                </span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
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
            {rejectLabel}
          </button>
        </div>
      )}
    </div>
  );
}
