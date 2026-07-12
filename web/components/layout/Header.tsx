"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { href: "/chat", label: "Chat" },
  { href: "/plan", label: "Plan" },
  { href: "/upload", label: "Upload" },
];

export function Header() {
  const pathname = usePathname();

  return (
    <header className="flex flex-wrap items-baseline justify-between gap-3 border-b-[3px] border-ink px-5 py-4">
      <div className="flex items-baseline gap-3">
        <Link href="/chat" className="font-mono text-xl font-bold tracking-tight">
          STEADY<span className="text-lift">FIT</span>
        </Link>
        <small className="font-mono text-[11px] uppercase tracking-widest text-steel">
          your coaching council
        </small>
      </div>
      <nav className="flex gap-4 font-mono text-xs uppercase tracking-wider">
        {NAV.map(({ href, label }) => {
          const active = pathname === href || pathname.startsWith(`${href}/`);
          return (
            <Link
              key={href}
              href={href}
              className={
                active
                  ? "font-bold text-lift"
                  : "text-steel transition hover:text-ink"
              }
            >
              {label}
            </Link>
          );
        })}
      </nav>
    </header>
  );
}
