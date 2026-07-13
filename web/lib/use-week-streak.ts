"use client";

import { useCallback, useEffect, useState } from "react";
import { fetchPlan } from "@/lib/api";
import { PLAN_UPDATED } from "@/lib/plan-events";

const THREAD_KEY = "steadyfit_thread_id";

export function useWeekStreak() {
  const [streakWeeks, setStreakWeeks] = useState<number | null>(null);

  const load = useCallback(async () => {
    try {
      const threadId = sessionStorage.getItem(THREAD_KEY);
      const plan = await fetchPlan(threadId);
      setStreakWeeks(plan.adherence.streak_weeks ?? 0);
    } catch {
      setStreakWeeks(0);
    }
  }, []);

  useEffect(() => {
    void load();
    window.addEventListener(PLAN_UPDATED, load);
    window.addEventListener("focus", load);
    return () => {
      window.removeEventListener(PLAN_UPDATED, load);
      window.removeEventListener("focus", load);
    };
  }, [load]);

  return streakWeeks;
}
