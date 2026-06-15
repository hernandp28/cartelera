"use client";

import type { MatchCard as Match, MatchEvent } from "@/lib/types";

function statusLabel(m: Match): { text: string; live: boolean } {
  switch (m.status) {
    case "LIVE":
      return { text: m.minute ? `${m.minute}'` : "EN JUEGO", live: true };
    case "HT":
      return { text: "ENT", live: true };
    case "FT":
      return { text: "Final", live: false };
    case "AET":
      return { text: "Final (TS)", live: false };
    case "PEN":
      return { text: "Final (Pen.)", live: false };
    case "POSTP":
      return { text: "Susp.", live: false };
    default:
      return { text: m.kickoff, live: false };
  }
}

function Flag({ url, name }: { url?: string | null; name: string }) {
  if (!url)
    return (
      <span className="inline-block w-9 h-6 rounded-sm bg-line text-[8px] text-muted text-center leading-6">
        {name.slice(0, 3)}
      </span>
    );
  return (
    <img
      src={url}
      alt={name}
      className="w-9 h-6 rounded-sm object-cover border border-line shrink-0"
    />
  );
}

function eventNames(events: MatchEvent[], side: "home" | "away") {
  return events
    .filter((e) => e.team_side === side)
    .map((e) => (e.minute ? `${e.player} ${e.minute}'` : e.player));
}

/** Goleadores ⚽ y expulsados 🟥 de un equipo. `align` define el lado. */
function TeamEvents({
  m,
  side,
  align,
}: {
  m: Match;
  side: "home" | "away";
  align: "left" | "right";
}) {
  const goals = eventNames(m.scorers, side);
  const reds = eventNames(m.red_cards, side);
  if (goals.length === 0 && reds.length === 0) return <div />;
  return (
    <div className={align === "right" ? "text-right" : "text-left"}>
      {goals.map((g, i) => (
        <div key={`g${i}`} className="truncate text-gray-300 text-[10px] leading-tight">
          ⚽ {g}
        </div>
      ))}
      {reds.map((r, i) => (
        <div key={`r${i}`} className="truncate text-red-400 text-[10px] leading-tight">
          🟥 {r}
        </div>
      ))}
    </div>
  );
}

export default function MatchCard({
  m,
  onSelect,
  justScored,
}: {
  m: Match;
  onSelect?: (m: Match) => void;
  justScored?: boolean;
}) {
  const st = statusLabel(m);
  const started = !["NS"].includes(m.status);
  const clickable = ["LIVE", "HT", "FT", "AET", "PEN"].includes(m.status) && !!onSelect;
  const score =
    m.home_score != null && m.away_score != null
      ? `${m.home_score} - ${m.away_score}`
      : "vs";
  const pens =
    m.status === "PEN" && m.home_pens != null && m.away_pens != null
      ? `(${m.home_pens} - ${m.away_pens})`
      : null;

  return (
    <div
      onClick={clickable ? () => onSelect!(m) : undefined}
      title={clickable ? "Ver alineaciones" : undefined}
      className={`h-full min-h-0 rounded-lg bg-panel2 border border-line px-3 py-2 flex flex-col justify-center gap-1.5 overflow-hidden transition ${
        clickable ? "cursor-pointer hover:border-brand hover:bg-panel2/80" : "hover:border-brand/60"
      }`}
    >
      {/* meta: competición + estado */}
      <div className="flex items-center justify-between text-[10px] text-muted">
        <span className="uppercase tracking-wide truncate">
          {m.group ? `Grupo ${m.group}` : m.stage || ""}
        </span>
        <span
          className={`flex items-center gap-1 font-bold ${
            st.live ? "text-live" : "text-gray-300"
          }`}
        >
          {st.live && (
            <span className="live-dot w-1.5 h-1.5 rounded-full bg-live" />
          )}
          {st.text}
        </span>
      </div>

      {/* Equipo1 — Resultado — Equipo2 */}
      <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-2">
        {/* Equipo1 (izquierda) */}
        <div className="flex items-center gap-2 min-w-0">
          <Flag url={m.home.flag_url || m.home.logo_url} name={m.home.name} />
          <span className="truncate font-semibold text-[13px] leading-tight">
            {m.home.name}
          </span>
        </div>

        {/* Resultado (centro) */}
        <div className="text-center px-1">
          <div
            className={`text-2xl font-extrabold tabular-nums leading-none whitespace-nowrap origin-center ${
              justScored ? "goal-pop" : ""
            }`}
          >
            {started ? score : <span className="text-muted text-base">{m.kickoff}</span>}
          </div>
          {pens && <div className="text-[10px] text-gold font-bold">{pens}</div>}
        </div>

        {/* Equipo2 (derecha) */}
        <div className="flex items-center gap-2 min-w-0 justify-end">
          <span className="truncate font-semibold text-[13px] leading-tight text-right">
            {m.away.name}
          </span>
          <Flag url={m.away.flag_url || m.away.logo_url} name={m.away.name} />
        </div>
      </div>

      {/* goleadores / expulsados debajo de cada equipo */}
      {(m.scorers.length > 0 || m.red_cards.length > 0) && (
        <div className="grid grid-cols-2 gap-x-3">
          <TeamEvents m={m} side="home" align="left" />
          <TeamEvents m={m} side="away" align="right" />
        </div>
      )}

      {/* sede */}
      {m.venue && (
        <div className="flex items-center gap-1 text-[9px] text-muted border-t border-line/40 pt-1 mt-0.5">
          <span className="shrink-0">📍</span>
          <span className="truncate">{m.venue}</span>
        </div>
      )}
    </div>
  );
}
