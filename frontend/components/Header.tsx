"use client";

import { useRef } from "react";
import { formatDMY, formatLongDate } from "@/lib/api";

interface Props {
  date: string;
  isDemo: boolean;
  source: string;
  onPrev: () => void;
  onToday: () => void;
  onNext: () => void;
  onPick: (date: string) => void;
}

export default function Header({
  date,
  isDemo,
  source,
  onPrev,
  onToday,
  onNext,
  onPick,
}: Props) {
  const dateRef = useRef<HTMLInputElement>(null);

  const openPicker = () => {
    const el = dateRef.current;
    if (!el) return;
    // showPicker() abre el calendario nativo; fallback a focus/click
    if (typeof el.showPicker === "function") el.showPicker();
    else el.click();
  };

  return (
    <header className="h-[64px] shrink-0 rounded-xl bg-panel border border-line px-4 flex items-center justify-between">
      {/* Izquierda: título */}
      <div className="flex items-center gap-3 w-[300px]">
        <div className="w-1.5 h-9 bg-brand rounded-full" />
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight leading-none">
            Mundial 2026
          </h1>
          <span className="text-[11px] text-muted capitalize">
            {formatLongDate(date)}
          </span>
        </div>
        {isDemo && (
          <span
            title="Datos de muestra: el plan gratuito de Sportmonks no incluye el Mundial."
            className="ml-1 text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-gold/20 text-gold border border-gold/40"
          >
            DEMO
          </span>
        )}
      </div>

      {/* Centro: navegación */}
      <div className="flex items-center gap-2">
        <button
          onClick={onPrev}
          className="px-4 py-2 rounded-lg bg-panel2 border border-line hover:border-brand text-sm font-semibold transition"
        >
          ‹ Anterior
        </button>
        <button
          onClick={onToday}
          className="px-4 py-2 rounded-lg bg-brand hover:brightness-110 text-sm font-bold transition"
        >
          Hoy
        </button>
        <button
          onClick={onNext}
          className="px-4 py-2 rounded-lg bg-panel2 border border-line hover:border-brand text-sm font-semibold transition"
        >
          Siguiente ›
        </button>
        {/* Selector de fecha en formato DD/MM/YYYY (input nativo oculto) */}
        <div className="relative ml-2">
          <button
            onClick={openPicker}
            className="px-3 py-2 rounded-lg bg-panel2 border border-line hover:border-brand text-sm font-semibold tabular-nums flex items-center gap-2 transition"
          >
            <span>📅</span>
            <span>{formatDMY(date)}</span>
          </button>
          <input
            ref={dateRef}
            type="date"
            value={date}
            onChange={(e) => e.target.value && onPick(e.target.value)}
            className="absolute inset-0 w-full h-full opacity-0 pointer-events-none [color-scheme:dark]"
            tabIndex={-1}
            aria-hidden="true"
          />
        </div>
      </div>

      {/* Derecha: logo */}
      <div className="w-[300px] flex items-center justify-end gap-3">
        {/* Logo oficial incluido en la raíz del proyecto */}
        <img src="/Logo.svg" alt="Mundial 2026" className="h-12 w-auto" />
      </div>
    </header>
  );
}
