"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Header from "@/components/Header";
import Agenda from "@/components/Agenda";
import GroupsCarousel from "@/components/GroupsCarousel";
import JueganManana from "@/components/JueganManana";
import LineupModal from "@/components/LineupModal";
import { fetchCartelera, shiftDate, todayAR } from "@/lib/api";
import { playGoalCrowd, playWhistle, unlockAudio } from "@/lib/sound";
import type { CarteleraResponse, MatchCard } from "@/lib/types";

export default function Page() {
  const [date, setDate] = useState<string>(todayAR());
  const [data, setData] = useState<CarteleraResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [scale, setScale] = useState(1);
  const [selected, setSelected] = useState<MatchCard | null>(null);
  const [goalIds, setGoalIds] = useState<Set<string | number>>(new Set());
  const prevTotals = useRef<Record<string, number>>({});
  const prevStatus = useRef<Record<string, string>>({});
  const stageRef = useRef<HTMLDivElement>(null);

  // Refs para el chequeo de medianoche sin recrear timers
  const todayRef = useRef<string>(todayAR());
  const dateRef = useRef<string>(date);
  useEffect(() => {
    dateRef.current = date;
  }, [date]);

  const load = useCallback(async (d: string) => {
    try {
      const res = await fetchCartelera(d);
      setData(res);
      setError(null);
    } catch (e) {
      setError("No se pudo conectar con la API (¿backend en :8000?).");
    }
  }, []);

  // Polling adaptativo: rápido si hay partidos en vivo, lento si no hay ninguno.
  // Ahorra requests a la API externa cuando no hay actividad.
  // (el backend ya normaliza los estados a "LIVE"/"HT")
  const hasLive =
    data?.agenda?.some((m) => m.status === "LIVE" || m.status === "HT") ?? false;
  const pollInterval = hasLive ? 10_000 : 300_000;

  useEffect(() => {
    load(date);
    const id = setInterval(() => load(date), pollInterval);
    return () => clearInterval(id);
  }, [date, load, pollInterval]);

  // Cambio de día automático: al pasar las 00:00 (hora Argentina), si el
  // usuario está viendo "hoy", la cartelera salta al nuevo día. Si está
  // navegando otra fecha, no lo molesta (pero "Hoy" sigue apuntando bien).
  useEffect(() => {
    const id = setInterval(() => {
      const now = todayAR();
      if (now !== todayRef.current) {
        const estabaEnHoy = dateRef.current === todayRef.current;
        todayRef.current = now;
        if (estabaEnHoy) setDate(now);
      }
    }, 20000); // chequea cada 20s → salta dentro de ~20s de la medianoche
    return () => clearInterval(id);
  }, []);

  // Detección entre refrescos:
  //  • Gol (sube el marcador)        → festejo de tribuna + animación 5s
  //  • Cambio de fase del partido    → silbato de árbitro
  //      NS→LIVE (inicio), LIVE→HT (fin 1T), HT→LIVE (inicio 2T),
  //      LIVE/HT→FT/AET/PEN (final)
  useEffect(() => {
    if (!data) return;
    const prevT = prevTotals.current;
    const prevS = prevStatus.current;
    const nextT: Record<string, number> = {};
    const nextS: Record<string, string> = {};
    const scored: (string | number)[] = [];
    let whistle = false;

    const isPhaseChange = (p: string, c: string) =>
      (p === "NS" && c === "LIVE") ||
      (p === "LIVE" && c === "HT") ||
      (p === "HT" && c === "LIVE") ||
      ((p === "LIVE" || p === "HT") && ["FT", "AET", "PEN"].includes(c));

    for (const m of data.agenda) {
      const id = String(m.id);
      const total = (m.home_score ?? 0) + (m.away_score ?? 0);
      nextT[id] = total;
      nextS[id] = m.status;
      if (id in prevT && total > prevT[id]) scored.push(m.id);
      if (id in prevS && isPhaseChange(prevS[id], m.status)) whistle = true;
    }
    prevTotals.current = nextT;
    prevStatus.current = nextS;

    if (whistle) playWhistle();
    if (scored.length > 0) {
      setGoalIds(new Set(scored));
      playGoalCrowd();
      const t = setTimeout(() => setGoalIds(new Set()), 5200); // dura la anim.
      return () => clearTimeout(t);
    }
  }, [data]);

  // Desbloquea el audio en la primera interacción del usuario (kiosko/navegador)
  useEffect(() => {
    const unlock = () => {
      unlockAudio();
      window.removeEventListener("pointerdown", unlock);
      window.removeEventListener("keydown", unlock);
    };
    window.addEventListener("pointerdown", unlock);
    window.addEventListener("keydown", unlock);
    return () => {
      window.removeEventListener("pointerdown", unlock);
      window.removeEventListener("keydown", unlock);
    };
  }, []);

  // Escala la cartelera 1280x720 para llenar la ventana sin deformar
  useEffect(() => {
    const fit = () => {
      const s = Math.min(window.innerWidth / 1280, window.innerHeight / 720);
      setScale(s);
    };
    fit();
    window.addEventListener("resize", fit);
    return () => window.removeEventListener("resize", fit);
  }, []);

  return (
    <main className="w-screen h-screen flex items-center justify-center bg-[#05070d] overflow-hidden">
      <div
        ref={stageRef}
        className="stage origin-center relative"
        style={{ transform: `scale(${scale})` }}
      >
        {/* Crédito: chico, abajo a la derecha, sin afectar la visual */}
        <span className="pointer-events-none absolute bottom-1 right-2 z-10 text-[9px] text-white/30 select-none">
          Desarrollado por Hernan DP
        </span>
        <div className="w-full h-full p-3 flex flex-col gap-3">
          <Header
            date={date}
            isDemo={data?.is_demo ?? false}
            source={data?.source ?? "seed"}
            onPrev={() => setDate((d) => shiftDate(d, -1))}
            onToday={() => setDate(todayAR())}
            onNext={() => setDate((d) => shiftDate(d, 1))}
            onPick={(d) => setDate(d)}
          />

          {error ? (
            <div className="flex-1 rounded-xl bg-panel border border-line flex items-center justify-center text-center px-8">
              <div>
                <p className="text-brand font-bold mb-1">⚠ {error}</p>
                <p className="text-muted text-sm">
                  Levantá el backend: <code>uvicorn app.main:app --reload</code>
                </p>
              </div>
            </div>
          ) : (
            <>
              <Agenda
                matches={data?.agenda ?? []}
                onSelect={setSelected}
                goalIds={goalIds}
              />
              <GroupsCarousel groups={data?.groups ?? []} />
              <JueganManana matches={data?.tomorrow ?? []} />
            </>
          )}
        </div>
      </div>

      {/* Modal de alineaciones (fuera del stage escalado, tamaño real) */}
      {selected && (
        <LineupModal match={selected} onClose={() => setSelected(null)} />
      )}
    </main>
  );
}
