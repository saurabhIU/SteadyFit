"use client";

import { useCallback, useEffect, useState } from "react";
import { fetchPlan } from "@/lib/api";
import { PLAN_UPDATED } from "@/lib/plan-events";
import { threadStorageKey, useProfile } from "@/lib/profile";

export function useWeekStreak() {
  const { userId, ready } = useProfile();
  const [streakWeeks, setStreakWeeks] = useState<number | null>(null);

  const load = useCallback(async () => {
    if (!ready) return;
    try {
      const threadId = sessionStorage.getItem(threadStorageKey(userId));
      const plan = await fetchPlan(threadId);
      setStreakWeeks(plan.adherence.streak_weeks ?? 0);
    } catch {
      setStreakWeeks(0);
    }
  }, [userId, ready]);

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
