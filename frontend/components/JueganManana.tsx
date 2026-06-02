"use client";

import type { UpcomingMatch } from "@/lib/types";

export default function JueganManana({ matches }: { matches: UpcomingMatch[] }) {
  return (
    <section className="shrink-0 h-[44px] rounded-xl bg-panel border border-line px-3 flex items-center gap-3 overflow-hidden">
      <span className="shrink-0 text-xs font-bold tracking-widest text-gold uppercase">
        Juegan mañana
      </span>
      <div className="flex-1 flex items-center gap-4 overflow-hidden whitespace-nowrap">
        {matches.length === 0 ? (
          <span className="text-xs text-muted">Sin partidos programados.</span>
        ) : (
          matches.map((m, i) => (
            <span key={i} className="text-xs flex items-center gap-1.5">
              <span className="text-gold font-bold tabular-nums">{m.kickoff}</span>
              <span className="text-muted">—</span>
              <span className="font-semibold">{m.home}</span>
              <span className="text-muted">vs</span>
              <span className="font-semibold">{m.away}</span>
              {i < matches.length - 1 && (
                <span className="text-line ml-2">•</span>
              )}
            </span>
          ))
        )}
      </div>
    </section>
  );
}
