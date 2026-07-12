"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { ApiError, fetchPlan } from "@/lib/api";
import { PLAN_UPDATED } from "@/lib/plan-events";
import type { PlanResponse } from "@/lib/types";

const THREAD_KEY = "steadyfit_thread_id";

const STATUS_STYLES: Record<string, string> = {
  planned: "border-line bg-white/70 text-ink",
  done: "border-emerald-300/60 bg-emerald-50 text-emerald-900",
  skipped: "border-red-300/50 bg-red-50 text-red-900",
  moved: "border-amber-300/60 bg-amber-50 text-amber-900",
};

export function PlanView() {
  const [data, setData] = useState<PlanResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadPlan = useCallback(async () => {
    const threadId = sessionStorage.getItem(THREAD_KEY);
    const plan = await fetchPlan(threadId);
    setData(plan);
    setError(null);
  }, []);

  useEffect(() => {
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
  }, [loadPlan]);

  if (loading && !data) {
    return (
      <div className="mx-auto w-full max-w-3xl px-5 py-8 text-sm text-steel">
        loading your week…
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="mx-auto w-full max-w-3xl px-5 py-8">
        <div className="rounded border border-lift/40 bg-lift/10 px-3.5 py-2.5 text-sm text-ink">
          {error}
        </div>
      </div>
    );
  }

  if (!data) return null;

  const plan = data.week_plan;
  const profileTags =
    data.profile.injuries.length > 0 ||
    data.profile.food_preferences.length > 0 ||
    data.profile.workout_preferences.length > 0;

  return (
    <div className="mx-auto w-full max-w-3xl px-5 py-6">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="font-mono text-[10px] font-bold uppercase tracking-wider text-lift">
            weekly plan
          </p>
          <h2 className="mt-1 text-xl font-semibold text-ink">
            {data.profile.name}&apos;s week
          </h2>
          <p className="mt-1 text-sm text-steel">{data.profile.goal}</p>
        </div>
        <Link
          href="/chat"
          className="font-mono text-xs text-lift underline-offset-2 hover:underline"
        >
          adjust in chat →
        </Link>
      </div>

      <div className="mb-6 grid gap-3 sm:grid-cols-3">
        <StatCard
          label="adherence (14d)"
          value={
            data.adherence.adherence_pct != null
              ? `${data.adherence.adherence_pct}%`
              : "no logs yet"
          }
          hint={
            data.adherence.drop_off_signal
              ? "drop-off signal — council may simplify"
              : "based on workout log"
          }
        />
        <StatCard
          label="sessions / week"
          value={String(data.profile.sessions_per_week)}
          hint="target frequency"
        />
        <StatCard
          label="macros"
          value={plan ? `${plan.calorie_target ?? "—"} kcal` : "—"}
          hint={
            plan?.protein_target_g
              ? `${plan.protein_target_g}g protein`
              : "set after first plan"
          }
        />
      </div>

      {plan ? (
        <div className="space-y-3">
          <p className="font-mono text-[11px] text-steel">
            week of {plan.week_start}
            {plan.notes ? ` · ${plan.notes}` : ""}
          </p>
          <div className="grid gap-2">
            {plan.days.map((day) => (
              <div
                key={`${day.day}-${day.focus}`}
                className={`flex items-center justify-between rounded-lg border px-4 py-3 ${STATUS_STYLES[day.status] ?? STATUS_STYLES.planned}`}
              >
                <div>
                  <p className="font-medium">{day.day}</p>
                  <p className="text-sm text-steel">{day.focus}</p>
                </div>
                <div className="text-right font-mono text-xs">
                  <p>{day.duration_min} min</p>
                  <p className="uppercase tracking-wide opacity-70">{day.status}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="rounded-lg border border-dashed border-line bg-white/50 px-4 py-8 text-center">
          <p className="text-sm text-steel">No plan saved yet.</p>
          <Link
            href="/chat"
            className="mt-2 inline-block text-sm font-medium text-lift hover:underline"
          >
            Chat with the council to build your first week
          </Link>
        </div>
      )}

      {profileTags ? (
        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {data.profile.injuries.length > 0 ? (
            <TagList title="injuries / constraints" items={data.profile.injuries} />
          ) : null}
          {data.profile.food_preferences.length > 0 ? (
            <TagList title="food preferences" items={data.profile.food_preferences} />
          ) : null}
          {data.profile.workout_preferences.length > 0 ? (
            <TagList title="workout preferences" items={data.profile.workout_preferences} />
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

function StatCard({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint: string;
}) {
  return (
    <div className="rounded-lg border border-line bg-white/60 px-3.5 py-3">
      <p className="font-mono text-[10px] font-bold uppercase tracking-wider text-steel">
        {label}
      </p>
      <p className="mt-1 text-lg font-semibold text-ink">{value}</p>
      <p className="mt-0.5 text-xs text-steel">{hint}</p>
    </div>
  );
}

function TagList({ title, items }: { title: string; items: string[] }) {
  return (
    <div>
      <p className="font-mono text-[10px] font-bold uppercase tracking-wider text-steel">
        {title}
      </p>
      <ul className="mt-2 flex flex-wrap gap-1.5">
        {items.map((item) => (
          <li
            key={item}
            className="rounded-full border border-line bg-paper px-2.5 py-1 text-xs text-ink"
          >
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}
