import type { CouncilProposals } from "@/lib/types";

type CouncilPanelProps = {
  proposals: CouncilProposals;
};

const SKIP_KEYS = new Set(["plan_changed", "proposed_week_plan"]);

export function CouncilPanel({ proposals }: CouncilPanelProps) {
  const entries = Object.entries(proposals).filter(([key]) => !SKIP_KEYS.has(key));

  if (entries.length === 0) return null;

  return (
    <div className="space-y-2">
      {entries.map(([agent, proposal]) => (
        <div
          key={agent}
          className="border-l-[3px] border-lift px-3 py-1.5 font-mono text-xs leading-relaxed text-steel"
        >
          <span className="text-[10px] font-bold uppercase tracking-wider text-lift">
            {agent}
          </span>
          <p className="mt-1 whitespace-pre-wrap">{String(proposal).slice(0, 400)}</p>
        </div>
      ))}
    </div>
  );
}
