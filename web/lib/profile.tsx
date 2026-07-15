"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import {
  fetchProfiles,
  setApiUserId,
  type ProfileSummary,
} from "@/lib/api";

const DEFAULT_PROFILE = "demo-veteran";

type ProfileContextValue = {
  userId: string;
  profiles: ProfileSummary[];
  ready: boolean;
  setUserId: (id: string) => void;
  hrefWithProfile: (path: string) => string;
};

const ProfileContext = createContext<ProfileContextValue | null>(null);

export function threadStorageKey(userId: string) {
  return `steadyfit_thread_id:${userId}`;
}

export function ProfileProvider({ children }: { children: ReactNode }) {
  const searchParams = useSearchParams();
  const pathname = usePathname();
  const router = useRouter();
  const urlProfile = searchParams.get("profile");

  const [profiles, setProfiles] = useState<ProfileSummary[]>([]);
  const [userId, setUserIdState] = useState(urlProfile || DEFAULT_PROFILE);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetchProfiles()
      .then((list) => {
        if (cancelled) return;
        setProfiles(list);
        const ids = new Set(list.map((p) => p.user_id));
        const preferred =
          (urlProfile && ids.has(urlProfile) && urlProfile) ||
          (ids.has(DEFAULT_PROFILE) && DEFAULT_PROFILE) ||
          list[0]?.user_id ||
          DEFAULT_PROFILE;
        setUserIdState(preferred);
        setApiUserId(preferred);
        if (urlProfile !== preferred) {
          const params = new URLSearchParams(searchParams.toString());
          params.set("profile", preferred);
          router.replace(`${pathname}?${params.toString()}`);
        }
      })
      .catch(() => {
        if (!cancelled) setApiUserId(urlProfile || DEFAULT_PROFILE);
      })
      .finally(() => {
        if (!cancelled) setReady(true);
      });
    return () => {
      cancelled = true;
    };
    // Bootstrap once on mount.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!urlProfile || urlProfile === userId) return;
    if (profiles.length && !profiles.some((p) => p.user_id === urlProfile)) return;
    setUserIdState(urlProfile);
    setApiUserId(urlProfile);
  }, [urlProfile, userId, profiles]);

  useEffect(() => {
    setApiUserId(userId);
  }, [userId]);

  const setUserId = useCallback(
    (id: string) => {
      setUserIdState(id);
      setApiUserId(id);
      const params = new URLSearchParams(searchParams.toString());
      params.set("profile", id);
      router.replace(`${pathname}?${params.toString()}`);
    },
    [pathname, router, searchParams],
  );

  const hrefWithProfile = useCallback(
    (path: string) => {
      const [base, qs = ""] = path.split("?");
      const params = new URLSearchParams(qs);
      params.set("profile", userId);
      const q = params.toString();
      return q ? `${base}?${q}` : base;
    },
    [userId],
  );

  const value = useMemo(
    () => ({ userId, profiles, ready, setUserId, hrefWithProfile }),
    [userId, profiles, ready, setUserId, hrefWithProfile],
  );

  return (
    <ProfileContext.Provider value={value}>{children}</ProfileContext.Provider>
  );
}

export function useProfile() {
  const ctx = useContext(ProfileContext);
  if (!ctx) {
    throw new Error("useProfile must be used within ProfileProvider");
  }
  return ctx;
}
