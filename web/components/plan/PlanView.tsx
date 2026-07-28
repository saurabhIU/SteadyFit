"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { ChevronDown, ChevronRight } from "lucide-react";
import { ApiError, fetchPlan, fetchTodayFoodLog } from "@/lib/api";
import { PLAN_UPDATED } from "@/lib/plan-events";
import { threadStorageKey, useProfile } from "@/lib/profile";
import type { FoodLogMeal, PlanResponse, TodayFoodLogResponse, WorkoutDay } from "@/lib/types";
import { dayOfMonthLabel, formatWeekRange } from "@/lib/plan-dates";
import { cn } from "@/lib/utils";

const DAY_ABBR: Record<string, string> = {
  Monday: "Mon",
  Tuesday: "Tue",
  Wednesday: "Wed",
  Thursday: "Thu",
  Friday: "Fri",
  Saturday: "Sat",
  Sunday: "Sun",
};

function sessionStats(days: WorkoutDay[], target: number) {
  const done = days.filter((d) => d.status === "done").length;
  const total = target || days.filter((d) => d.status !== "moved").length;
  return { done, total: Math.max(total, days.length) };
}

function StatusDot({ status }: { status: WorkoutDay["status"] }) {
  if (status === "done") {
    return (
      <span
        className="size-2.5 shrink-0 rounded-full bg-sage"
        aria-label="Done"
      />
    );
  }
  if (status === "skipped") {
    return (
      <span
        className="size-2.5 shrink-0 rounded-full border-2 border-surface-raised bg-transparent"
        aria-label="Skipped"
      />
    );
  }
  return (
    <span
      className="size-2.5 shrink-0 rounded-full border-2 border-surface-raised bg-transparent"
      aria-label="Planned"
    />
  );
}

function ProgressDots({ done, total }: { done: number; total: number }) {
  return (
    <div className="flex items-center gap-1" aria-hidden>
      {Array.from({ length: total }, (_, i) => (
        <span
          key={i}
          className={cn(
            "size-2 rounded-full",
            i < done ? "bg-sage" : "bg-surface-raised",
          )}
        />
      ))}
    </div>
  );
}

function formatInt(n: number | null | undefined) {
  if (n == null || Number.isNaN(n)) return "—";
  return Math.round(n).toLocaleString("en-US");
}

function mealSummary(meal: FoodLogMeal): string {
  const label = (meal.meal_label || "").trim();
  if (label) return label;
  const names = (meal.foods || [])
    .map((f) => (typeof f === "string" ? f : f?.name || ""))
    .map((s) => s.trim())
    .filter(Boolean);
  if (names.length === 0) return "Logged meal";
  if (names.length === 1) return names[0];
  if (names.length === 2) return `${names[0]} + ${names[1]}`;
  return `${names[0]} + ${names.length - 1} more`;
}

function TodaysMealsSection({ food }: { food: TodayFoodLogResponse | null }) {
  const meals = food?.meals ?? [];
  const planned = food?.planned_meals ?? [];
  const totals = food?.totals;
  const targets = food?.targets;
  const kcalTarget = targets?.calorie_target ?? null;
  const proteinTarget = targets?.protein_target_g ?? null;

  return (
    <section className="space-y-4" aria-labelledby="todays-meals-heading">
      <h3 id="todays-meals-heading" className="text-lg font-semibold text-navy-text">
        Today&apos;s meals
      </h3>

      {planned.length > 0 ? (
        <div className="space-y-2">
          <p className="text-xs font-medium uppercase tracking-wide text-navy-muted">
            Planned
          </p>
          {planned.map((meal) => (
            <div
              key={`${meal.day}-${meal.meal_slot}-${meal.id ?? meal.food_description}`}
              className="overflow-hidden rounded-2xl border border-beige-border/60 bg-transparent px-4 py-3"
            >
              <div className="flex items-start justify-between gap-3">
                <p className="min-w-0 flex-1 text-sm text-navy-text">
                  <span className="font-medium capitalize">{meal.meal_slot}</span>
                  {" — "}
                  {meal.food_description}
                </p>
                <p className="shrink-0 font-mono text-xs text-navy-muted">
                  {formatInt(meal.kcal)} kcal · {formatInt(meal.protein_g)}g
                </p>
              </div>
            </div>
          ))}
        </div>
      ) : null}

      <div className="space-y-2">
        <p className="text-xs font-medium uppercase tracking-wide text-navy-muted">
          Logged
        </p>
        {meals.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-beige-border/40 px-4 py-6 text-center">
            <p className="text-sm text-navy-muted">
              Nothing logged yet today — snap a photo or tell me what you ate
            </p>
            <Link
              href="/chat"
              className="mt-3 inline-block text-sm font-medium text-sage hover:text-sage-hover"
            >
              Log in chat →
            </Link>
          </div>
        ) : (
          <>
            {meals.map((meal) => (
              <div
                key={meal.id}
                className="overflow-hidden rounded-2xl border border-beige-border bg-beige px-4 py-3.5"
              >
                <div className="flex items-start justify-between gap-3">
                  <p className="min-w-0 flex-1 truncate text-sm font-medium text-card-text">
                    {mealSummary(meal)}
                  </p>
                  <p className="shrink-0 font-mono text-xs text-card-text/60">
                    {formatInt(meal.kcal)} kcal · {formatInt(meal.protein_g)}g protein
                  </p>
                </div>
              </div>
            ))}
          </>
        )}
        <p className="px-1 pt-1 font-mono text-sm text-navy-text">
          {formatInt(totals?.kcal_consumed)} / {formatInt(kcalTarget)} kcal ·{" "}
          {formatInt(totals?.protein_g_consumed)} / {formatInt(proteinTarget)}g protein
        </p>
      </div>
    </section>
  );
}

function DayRow({
  day,
  weekStart,
}: {
  day: WorkoutDay;
  weekStart: string;
}) {
  const [open, setOpen] = useState(false);
  const abbr = DAY_ABBR[day.day] ?? day.day.slice(0, 3);
  const dateNum = dayOfMonthLabel(weekStart, day.day);

  const detail =
    day.status === "skipped"
      ? "Life happened — we can fold this back in when you're ready."
      : day.status === "moved"
        ? "Moved to fit your week — still counts toward consistency."
        : day.status === "done"
          ? `Completed · ${day.duration_min} min`
          : `${day.duration_min} min · ${day.focus}`;

  return (
    <div className="overflow-hidden rounded-2xl border border-beige-border bg-beige">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center gap-3 px-4 py-3.5 text-left transition-colors hover:bg-beige-border/20"
        aria-expanded={open}
      >
        <div className="w-10 shrink-0 text-center">
          <p className="font-mono text-[11px] font-medium uppercase text-card-text/50">
            {abbr}
          </p>
          <p className="font-mono text-sm font-medium text-card-text">{dateNum}</p>
        </div>

        <StatusDot status={day.status} />

        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium text-card-text">{day.focus}</p>
          <p className="truncate text-xs text-card-text/55">
            {day.status === "skipped"
              ? "Rest day — no guilt"
              : `${day.duration_min} min`}
          </p>
        </div>

        {open ? (
          <ChevronDown className="size-4 shrink-0 text-card-text/40" />
        ) : (
          <ChevronRight className="size-4 shrink-0 text-card-text/40" />
        )}
      </button>

      {open ? (
        <div className="border-t border-beige-border/60 px-4 py-2.5">
          <p className="text-sm text-card-text/70">{detail}</p>
        </div>
      ) : null}
    </div>
  );
}

export function PlanView() {
  const { userId, ready } = useProfile();
  const [data, setData] = useState<PlanResponse | null>(null);
  const [foodLog, setFoodLog] = useState<TodayFoodLogResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadPlan = useCallback(async () => {
    if (!ready) return;
    const threadId = sessionStorage.getItem(threadStorageKey(userId));
    const [plan, todayFood] = await Promise.all([
      fetchPlan(threadId),
      fetchTodayFoodLog(threadId).catch(() => null),
    ]);
    setData(plan);
    setFoodLog(todayFood);
    setError(null);
  }, [userId, ready]);

  useEffect(() => {
    if (!ready) return;
    setLoading(true);
    loadPlan()
      .catch((err) => {
        const message =
          err instanceof ApiError
            ? `API error (${err.status}): ${err.message}`
            : "Could not load your plan — is the backend running?";
        setError(message);
      })
      .finally(() => setLoading(false));

    const onRefresh = () => {
      setLoading(true);
      loadPlan()
        .catch((err) => {
          const message =
            err instanceof ApiError
              ? `API error (${err.status}): ${err.message}`
              : "Could not refresh your plan.";
          setError(message);
        })
        .finally(() => setLoading(false));
    };

    window.addEventListener(PLAN_UPDATED, onRefresh);
    window.addEventListener("focus", onRefresh);
    return () => {
      window.removeEventListener(PLAN_UPDATED, onRefresh);
      window.removeEventListener("focus", onRefresh);
    };
  }, [loadPlan, ready]);

  if (loading && !data) {
    return (
      <div className="content-width space-y-4 py-6">
        <div className="skeleton animate-shimmer h-8 w-48 rounded-lg" />
        <div className="skeleton animate-shimmer h-16 rounded-2xl" />
        <div className="skeleton animate-shimmer h-16 rounded-2xl" />
        <div className="skeleton animate-shimmer h-16 rounded-2xl" />
        <p className="text-sm text-navy-muted">Loading your week…</p>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="content-width py-6">
        <div className="rounded-2xl border border-beige-border/30 bg-team-panel px-4 py-3 text-sm text-navy-muted">
          {error}
        </div>
      </div>
    );
  }

  if (!data) return null;

  const plan = data.week_plan;
  const stats = plan
    ? sessionStats(plan.days, data.profile.sessions_per_week ?? 3)
    : { done: 0, total: data.profile.sessions_per_week ?? 3 };

  return (
    <div className="content-width space-y-5 py-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-navy-text">This week</h2>
          {plan ? (
            <p className="mt-0.5 font-mono text-sm text-navy-muted">
              {formatWeekRange(plan.week_start)}
            </p>
          ) : (
            <p className="mt-0.5 text-sm text-navy-muted">No plan yet</p>
          )}
        </div>

        {plan ? (
          <div className="flex flex-col items-end gap-1.5">
            <p className="font-mono text-sm text-navy-text">
              {stats.done} of {stats.total} sessions
            </p>
            <ProgressDots done={stats.done} total={stats.total} />
          </div>
        ) : null}
      </div>

      {plan ? (
        <div className="space-y-2">
          {plan.days.map((day) => (
            <DayRow
              key={`${day.day}-${day.focus}`}
              day={day}
              weekStart={plan.week_start}
            />
          ))}
        </div>
      ) : (
        <div className="rounded-2xl border border-dashed border-beige-border/40 px-4 py-10 text-center">
          <p className="text-sm text-navy-muted">
            Nothing on the calendar yet — chat with the AI Coaching Team to sketch your first week.
          </p>
          <Link
            href="/chat"
            className="mt-3 inline-block text-sm font-medium text-sage hover:text-sage-hover"
          >
            Start in chat →
          </Link>
        </div>
      )}

      <TodaysMealsSection food={foodLog} />

      <div className="rounded-2xl border border-beige-border bg-beige p-5 text-card-text">
        <p className="text-sm leading-relaxed text-card-text/85">
          A miss is information, not failure. When life shifts, we adjust — no
          scorekeeping, just steady progress.
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          <Link
            href="/chat"
            onClick={() => {
              try {
                sessionStorage.setItem("steadyfit:pending_micro_10", "1");
              } catch {
                /* ignore */
              }
            }}
            className={cn(
              "inline-flex items-center gap-1.5 rounded-[var(--radius-pill)] border border-sage/50",
              "bg-accent-tint px-5 py-2 text-sm font-medium text-sage",
              "transition-colors duration-150 ease-out hover:bg-sage/20",
            )}
          >
            I have 10 minutes
          </Link>
          <Link
            href="/chat"
            className={cn(
              "inline-flex rounded-[var(--radius-pill)] bg-sage px-5 py-2 text-sm font-medium text-sage-foreground",
              "transition-colors duration-150 ease-out hover:bg-sage-hover",
            )}
          >
            Chat about it
          </Link>
        </div>
      </div>
    </div>
  );
}
