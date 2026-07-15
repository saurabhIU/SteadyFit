"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { ChevronDown, ChevronRight } from "lucide-react";
import { ApiError, fetchPlan } from "@/lib/api";
import { PLAN_UPDATED } from "@/lib/plan-events";
import { threadStorageKey, useProfile } from "@/lib/profile";
import type { PlanResponse, WorkoutDay } from "@/lib/types";
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

function formatDateRange(weekStart: string, dayCount: number) {
  const start = new Date(`${weekStart}T12:00:00`);
  if (Number.isNaN(start.getTime())) return weekStart;
  const end = new Date(start);
  end.setDate(end.getDate() + Math.max(dayCount - 1, 0));
  const fmt = (d: Date) =>
    d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  return `${fmt(start)} – ${fmt(end)}`;
}

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
        className="size-2.5 shrink-0 rounded-full border-2 border-neutral/60 bg-transparent"
        aria-label="Skipped"
      />
    );
  }
  return (
    <span
      className="size-2.5 shrink-0 rounded-full border-2 border-beige-border bg-transparent"
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
            i < done ? "bg-sage" : "bg-navy-muted-dim/40",
          )}
        />
      ))}
    </div>
  );
}

function DayRow({ day, index }: { day: WorkoutDay; index: number }) {
  const [open, setOpen] = useState(false);
  const abbr = DAY_ABBR[day.day] ?? day.day.slice(0, 3);

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
          <p className="font-mono text-sm font-medium text-card-text">
            {String(index + 1).padStart(2, "0")}
          </p>
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
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadPlan = useCallback(async () => {
    if (!ready) return;
    const threadId = sessionStorage.getItem(threadStorageKey(userId));
    const plan = await fetchPlan(threadId);
    setData(plan);
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
              {formatDateRange(plan.week_start, plan.days.length)}
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
          {plan.days.map((day, index) => (
            <DayRow key={`${day.day}-${day.focus}`} day={day} index={index} />
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

      <div className="rounded-2xl border border-beige-border bg-beige p-5 text-card-text">
        <p className="text-sm leading-relaxed text-card-text/85">
          A miss is information, not failure. When life shifts, we adjust — no
          scorekeeping, just steady progress.
        </p>
        <Link
          href="/chat"
          className={cn(
            "mt-4 inline-flex rounded-[var(--radius-pill)] bg-sage px-5 py-2 text-sm font-medium text-sage-foreground",
            "transition-colors duration-150 ease-out hover:bg-sage-hover",
          )}
        >
          Chat about it
        </Link>
      </div>
    </div>
  );
}
