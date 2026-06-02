"use client";

import type { MatchCard as Match } from "@/lib/types";
import MatchCard from "./MatchCard";

/** Calcula columnas para distribuir prolijamente hasta 10 partidos. */
function gridCols(n: number): number {
  if (n <= 1) return 1;
  if (n <= 2) return 2;
  return Math.ceil(n / 2); // 2 filas; 3..10 => 2..5 columnas
}

export default function Agenda({ matches }: { matches: Match[] }) {
  const cols = gridCols(matches.length);
  const rows = matches.length <= 2 ? 1 : 2;

  return (
    <section className="flex-1 min-h-0 rounded-xl bg-panel border border-line p-3 flex flex-col">
      <div className="flex items-center justify-between mb-2 px-1">
        <h2 className="text-sm font-bold tracking-widest text-muted uppercase">
          Agenda del día
        </h2>
        <span className="text-[11px] text-muted">
          {matches.length} partido{matches.length === 1 ? "" : "s"}
        </span>
      </div>

      {matches.length === 0 ? (
        <div className="flex-1 flex items-center justify-center text-muted text-sm">
          No hay partidos programados para esta fecha.
        </div>
      ) : (
        <div
          className="flex-1 min-h-0 grid gap-2"
          style={{
            gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))`,
            gridTemplateRows: `repeat(${rows}, minmax(0, 1fr))`,
          }}
        >
          {matches.map((m) => (
            <MatchCard key={m.id} m={m} />
          ))}
        </div>
      )}
    </section>
  );
}
