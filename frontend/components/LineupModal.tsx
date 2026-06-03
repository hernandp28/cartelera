"use client";

import { useEffect, useState } from "react";
import { fetchLineups } from "@/lib/api";
import type { LineupsResponse, MatchCard, TeamLineup } from "@/lib/types";

function PlayerRow({ p }: { p: { name: string | null; number: number | null; pos: string | null } }) {
  return (
    <li className="flex items-center gap-2 py-0.5 text-[13px]">
      <span className="w-6 shrink-0 text-center font-bold tabular-nums text-gold">
        {p.number ?? "-"}
      </span>
      <span className="truncate flex-1">{p.name ?? "—"}</span>
      {p.pos && (
        <span className="shrink-0 text-[9px] text-muted border border-line rounded px-1">
          {p.pos}
        </span>
      )}
    </li>
  );
}

function TeamColumn({ t, align }: { t: TeamLineup | null; align: "left" | "right" }) {
  if (!t) {
    return (
      <div className="flex-1 text-center text-muted text-sm py-8">
        Alineación no disponible.
      </div>
    );
  }
  return (
    <div className="flex-1 min-w-0">
      <div
        className={`flex items-center gap-2 mb-2 ${
          align === "right" ? "flex-row-reverse text-right" : ""
        }`}
      >
        {t.team.flag_url && (
          <img
            src={t.team.flag_url}
            alt=""
            className="w-9 h-6 rounded-sm object-cover border border-line shrink-0"
          />
        )}
        <div className="min-w-0">
          <div className="font-extrabold text-lg truncate">{t.team.name}</div>
          <div className="text-[11px] text-muted">
            {t.formation || "—"} · DT: {t.coach || "—"}
          </div>
        </div>
      </div>

      <div className="text-[10px] uppercase tracking-widest text-brand font-bold mb-1">
        Titulares
      </div>
      <ul className="mb-3">
        {t.startXI.map((p, i) => (
          <PlayerRow key={`xi${i}`} p={p} />
        ))}
      </ul>

      <div className="text-[10px] uppercase tracking-widest text-muted font-bold mb-1">
        Suplentes
      </div>
      <ul>
        {t.substitutes.map((p, i) => (
          <PlayerRow key={`sub${i}`} p={p} />
        ))}
      </ul>
    </div>
  );
}

export default function LineupModal({
  match,
  onClose,
}: {
  match: MatchCard;
  onClose: () => void;
}) {
  const [data, setData] = useState<LineupsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    fetchLineups(match.id)
      .then((d) => alive && setData(d))
      .catch(() => alive && setError(true))
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, [match.id]);

  // Cerrar con Escape
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const score =
    match.home_score != null && match.away_score != null
      ? `${match.home_score} - ${match.away_score}`
      : "vs";
  const noData = data && !data.home && !data.away;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-3xl max-h-[88vh] overflow-y-auto rounded-2xl bg-panel border border-line shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Encabezado */}
        <div className="sticky top-0 bg-panel border-b border-line px-5 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="font-bold truncate">{match.home.name}</span>
            <span className="text-xl font-extrabold tabular-nums">{score}</span>
            <span className="font-bold truncate">{match.away.name}</span>
          </div>
          <button
            onClick={onClose}
            className="ml-3 w-8 h-8 shrink-0 rounded-lg bg-panel2 border border-line hover:border-brand text-lg leading-none"
            aria-label="Cerrar"
          >
            ✕
          </button>
        </div>

        {/* Cuerpo */}
        <div className="p-5">
          {loading ? (
            <div className="text-center text-muted py-10">Cargando alineaciones…</div>
          ) : error ? (
            <div className="text-center text-brand py-10">
              No se pudieron cargar las alineaciones.
            </div>
          ) : noData ? (
            <div className="text-center text-muted py-10">
              Las alineaciones de este partido todavía no están disponibles.
            </div>
          ) : (
            <div className="flex gap-6">
              <TeamColumn t={data?.home ?? null} align="left" />
              <div className="w-px bg-line shrink-0" />
              <TeamColumn t={data?.away ?? null} align="right" />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
