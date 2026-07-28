"use client";

import { useEffect, useState } from "react";
import { ApiError, fetchPlan, fetchTodayFoodLog } from "@/lib/api";
import type { PlanResponse, TodayFoodLogResponse, WorkoutDay } from "@/lib/types";
import { cn } from "@/lib/utils";

const PREVIEW_USER = "demo-veteran";

const DAY_ABBR: Record<string, string> = {
  Monday: "Mon",
  Tuesday: "Tue",
  Wednesday: "Wed",
  Thursday: "Thu",
  Friday: "Fri",
  Saturday: "Sat",
  Sunday: "Sun",
};

function formatDateRange(weekStart: string) {
  const start = new Date(`${weekStart}T12:00:00`);
  if (Number.isNaN(start.getTime())) return weekStart;
  const end = new Date(start);
  end.setDate(end.getDate() + 6);
  const fmt = (d: Date) =>
    d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  return `${fmt(start)} – ${fmt(end)}`;
}

function formatInt(n: number | null | undefined) {
  if (n == null || Number.isNaN(n)) return "—";
  return Math.round(n).toLocaleString("en-US");
}

function StatusDot({ status }: { status: WorkoutDay["status"] }) {
  if (status === "done") {
    return <span className="size-2 shrink-0 rounded-full bg-sage" aria-hidden />;
  }
  if (status === "skipped") {
    return (
      <span
        className="size-2 shrink-0 rounded-full border-2 border-surface-raised bg-transparent"
        aria-hidden
      />
    );
  }
  return (
    <span
      className="size-2 shrink-0 rounded-full border-2 border-surface-raised bg-transparent"
      aria-hidden
    />
  );
}

function CompactDayRow({ day }: { day: WorkoutDay }) {
  const abbr = DAY_ABBR[day.day] ?? day.day.slice(0, 3);
  return (
    <div className="flex items-center gap-2.5 rounded-xl border border-beige-border bg-beige px-2.5 py-2">
      <p className="w-7 shrink-0 font-mono text-[10px] font-medium uppercase text-card-text/50">
        {abbr}
      </p>
      <StatusDot status={day.status} />
      <div className="min-w-0 flex-1">
        <p className="truncate text-[11px] font-medium text-card-text">{day.focus}</p>
        <p className="truncate text-[10px] text-card-text/55">
          {day.status === "skipped" ? "Rest" : `${day.duration_min} min`}
        </p>
      </div>
    </div>
  );
}

/** Live Plan page snapshot (demo-veteran) inside the landing phone frame. */
export function PlanPhonePreview() {
  const [plan, setPlan] = useState<PlanResponse | null>(null);
  const [food, setFood] = useState<TodayFoodLogResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [p, f] = await Promise.all([
          fetchPlan(null, { userId: PREVIEW_USER }),
          fetchTodayFoodLog(null, { userId: PREVIEW_USER }).catch(() => null),
        ]);
        if (cancelled) return;
        setPlan(p);
        setFood(f);
        setError(null);
      } catch (err) {
        if (cancelled) return;
        const message =
          err instanceof ApiError
            ? "Plan preview unavailable"
            : "Could not load plan preview";
        setError(message);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const week = plan?.week_plan;
  const days = week?.days ?? [];
  const sessionsDone = days.filter((d) => d.status === "done").length;
  const sessionsTarget =
    plan?.profile.sessions_per_week ?? Math.max(days.length, 3);
  const planned = food?.planned_meals ?? [];
  const kcalTarget = food?.targets?.calorie_target ?? week?.calorie_target ?? null;
  const proteinTarget =
    food?.targets?.protein_target_g ?? week?.protein_target_g ?? null;

  return (
    <div
      className="landing-phone pointer-events-none select-none"
      aria-hidden={false}
      aria-label="Preview of the SteadyFit plan screen"
    >
      <div className="landing-phone-notch" aria-hidden />
      <div className="landing-phone-screen">
        {error && !plan ? (
          <div className="flex h-full items-center justify-center px-4 text-center">
            <p className="text-xs text-navy-muted">{error}</p>
          </div>
        ) : !plan ? (
          <div className="space-y-2 p-3">
            <div className="skeleton animate-shimmer h-4 w-24 rounded" />
            <div className="skeleton animate-shimmer h-12 rounded-xl" />
            <div className="skeleton animate-shimmer h-12 rounded-xl" />
            <div className="skeleton animate-shimmer h-12 rounded-xl" />
          </div>
        ) : (
          <div className="space-y-3 p-3 pb-5">
            <div className="flex items-start justify-between gap-2">
              <div>
                <p className="text-xs font-semibold text-navy-text">This week</p>
                {week ? (
                  <p className="font-mono text-[10px] text-navy-muted">
                    {formatDateRange(week.week_start)}
                  </p>
                ) : (
                  <p className="text-[10px] text-navy-muted">No plan yet</p>
                )}
              </div>
              <p className="font-mono text-[10px] text-navy-text">
                {sessionsDone} of {sessionsTarget}
              </p>
            </div>

            <div className="space-y-1.5">
              {days.slice(0, 5).map((day) => (
                <CompactDayRow key={`${day.day}-${day.focus}`} day={day} />
              ))}
              {days.length > 5 ? (
                <p className="px-1 font-mono text-[10px] text-navy-muted">
                  +{days.length - 5} more
                </p>
              ) : null}
            </div>

            <div className="space-y-2 pt-1">
              <p className="text-[11px] font-semibold text-navy-text">
                Today&apos;s meals
              </p>
              {planned.length > 0 ? (
                <div className="space-y-1.5">
                  {planned.slice(0, 3).map((meal) => (
                    <div
                      key={`${meal.day}-${meal.meal_slot}-${meal.id ?? meal.food_description}`}
                      className="rounded-xl border border-beige-border/50 px-2.5 py-2"
                    >
                      <p className="truncate text-[11px] text-navy-text">
                        <span className="font-medium capitalize">
                          {meal.meal_slot}
                        </span>
                        {" — "}
                        {meal.food_description}
                      </p>
                      <p className="mt-0.5 font-mono text-[10px] text-navy-muted">
                        {formatInt(meal.kcal)} kcal · {formatInt(meal.protein_g)}g
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-[10px] text-navy-muted">
                  Planned meals show here once the coach builds your week.
                </p>
              )}
              <p
                className={cn(
                  "font-mono text-[10px] text-navy-text",
                  "rounded-lg border border-beige-border/30 bg-team-panel px-2 py-1.5",
                )}
              >
                {formatInt(food?.totals?.kcal_consumed)} / {formatInt(kcalTarget)}{" "}
                kcal · {formatInt(food?.totals?.protein_g_consumed)} /{" "}
                {formatInt(proteinTarget)}g protein
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
