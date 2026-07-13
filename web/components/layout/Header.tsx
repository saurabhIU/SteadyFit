"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useWeekStreak } from "@/lib/use-week-streak";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/chat", label: "Chat" },
  { href: "/plan", label: "Plan" },
  { href: "/update", label: "Update" },
] as const;

function isActive(pathname: string, href: string) {
  return pathname === href || pathname.startsWith(`${href}/`);
}

function PillTabs({ pathname, className }: { pathname: string; className?: string }) {
  return (
    <nav
      className={cn(
        "flex items-center gap-0.5 rounded-[var(--radius-pill)] border border-beige-border/30 bg-navy p-0.5",
        className,
      )}
      aria-label="Main navigation"
    >
      {NAV.map(({ href, label }) => {
        const active = isActive(pathname, href);
        return (
          <Link
            key={href}
            href={href}
            className={cn(
              "rounded-[var(--radius-pill)] px-3.5 py-1.5 text-sm font-medium transition-colors duration-150 ease-out",
              active
                ? "bg-sage text-sage-foreground"
                : "text-navy-muted hover:text-navy-text",
            )}
          >
            {label}
          </Link>
        );
      })}
    </nav>
  );
}

function StreakBadge({ weeks }: { weeks: number }) {
  if (weeks < 1) return null;

  return (
    <div
      className="hidden items-center gap-1.5 rounded-[var(--radius-pill)] border border-amber-border bg-amber-bg px-2.5 py-1 sm:flex"
      aria-label={`${weeks} week streak`}
      title={`${weeks} consecutive week${weeks === 1 ? "" : "s"} on track`}
    >
      <span className="font-mono text-xs font-medium text-amber">{weeks}</span>
      <span className="font-mono text-[10px] uppercase tracking-wide text-amber/80">
        wk
      </span>
    </div>
  );
}

function BottomNav({ pathname }: { pathname: string }) {
  return (
    <nav
      className="fixed inset-x-0 bottom-0 z-50 border-t border-beige-border/20 bg-navy/95 backdrop-blur-md md:hidden"
      aria-label="Mobile navigation"
    >
      <div className="mx-auto flex max-w-[var(--content-max)] items-stretch justify-around px-2 py-2">
        {NAV.map(({ href, label }) => {
          const active = isActive(pathname, href);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex flex-1 flex-col items-center gap-1 py-1 text-xs font-medium transition-colors duration-150 ease-out",
                active ? "text-navy-text" : "text-navy-muted-dim",
              )}
            >
              <span>{label}</span>
              <span
                className={cn(
                  "size-1.5 rounded-full transition-colors",
                  active ? "bg-sage" : "bg-transparent",
                )}
                aria-hidden
              />
            </Link>
          );
        })}
      </div>
    </nav>
  );
}

export function Header() {
  const pathname = usePathname();
  const streakWeeks = useWeekStreak();
  const showStreak =
    (pathname === "/chat" || pathname === "/plan") &&
    streakWeeks !== null &&
    streakWeeks > 0;

  return (
    <>
      <header className="sticky top-0 z-40 border-b border-beige-border/15 bg-navy/95 backdrop-blur-md">
        <div className="content-width flex h-[var(--header-h)] items-center justify-between gap-3">
          <Link href="/chat" className="flex shrink-0 items-center gap-2.5">
            <span
              className="size-2.5 shrink-0 rounded-full bg-sage"
              aria-hidden
            />
            <span className="text-base font-semibold tracking-tight text-navy-text lowercase">
              steadyfit
            </span>
          </Link>

          <div className="flex items-center gap-3">
            <PillTabs pathname={pathname} className="hidden sm:flex" />
            {showStreak ? <StreakBadge weeks={streakWeeks} /> : null}
          </div>
        </div>

        <div className="content-width pb-2 sm:hidden">
          <PillTabs pathname={pathname} className="w-full justify-center" />
        </div>
      </header>

      <BottomNav pathname={pathname} />
    </>
  );
}
