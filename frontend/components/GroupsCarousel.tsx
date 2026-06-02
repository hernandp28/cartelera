"use client";

import { useEffect, useState } from "react";
import type { GroupTable } from "@/lib/types";

function GroupCard({ g }: { g: GroupTable }) {
  return (
    <div className="rounded-lg bg-panel2 border border-line overflow-hidden flex flex-col">
      <div className="bg-brand/90 px-2 py-0.5 flex items-center justify-between shrink-0">
        <span className="text-xs font-extrabold">Grupo {g.group}</span>
      </div>
      {/* wrapper flex-1: la tabla ocupa todo el alto restante del contenedor */}
      <div className="flex-1 min-h-0">
        <table className="w-full h-full text-[10px]">
          <thead className="text-muted">
            <tr className="border-b border-line">
              <th className="w-4 text-center font-semibold py-0.5">#</th>
              <th className="text-left font-semibold pl-1">País</th>
              <th className="w-6 text-center font-semibold">Pts</th>
              <th className="w-6 text-center font-semibold">PJ</th>
              <th className="w-7 text-center font-semibold">DG</th>
            </tr>
          </thead>
          <tbody>
            {g.rows.map((r) => (
              <tr
                key={String(r.team.id)}
                className={`border-b border-line/40 align-middle ${
                  r.position <= 2 ? "text-white" : "text-gray-400"
                }`}
              >
                <td className="text-center">
                  <span
                    className={`inline-block w-3.5 h-3.5 rounded-sm text-[8px] leading-[14px] ${
                      r.position <= 2 ? "bg-live/30 text-live" : "bg-line text-muted"
                    }`}
                  >
                    {r.position}
                  </span>
                </td>
                <td className="pl-1">
                  <div className="flex items-center gap-1">
                    {r.team.flag_url && (
                      <img
                        src={r.team.flag_url}
                        alt=""
                        className="w-4 h-3 rounded-[1px] object-cover shrink-0"
                      />
                    )}
                    <span className="truncate max-w-[78px]">{r.team.name}</span>
                  </div>
                </td>
                <td className="text-center font-bold tabular-nums">{r.points}</td>
                <td className="text-center tabular-nums">{r.played}</td>
                <td className="text-center tabular-nums">
                  {r.goal_diff > 0 ? `+${r.goal_diff}` : r.goal_diff}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default function GroupsCarousel({ groups }: { groups: GroupTable[] }) {
  const pages: GroupTable[][] = [];
  for (let i = 0; i < groups.length; i += 6) pages.push(groups.slice(i, i + 6));

  const [page, setPage] = useState(0);

  useEffect(() => {
    if (pages.length <= 1) return;
    const id = setInterval(() => {
      setPage((p) => (p + 1) % pages.length);
    }, 10000); // 10 segundos por página
    return () => clearInterval(id);
  }, [pages.length]);

  const current = pages[page] || [];

  return (
    <section className="shrink-0 h-[200px] rounded-xl bg-panel border border-line p-3">
      <div className="flex items-center justify-between mb-1.5 px-1">
        <h2 className="text-sm font-bold tracking-widest text-muted uppercase">
          Tabla de posiciones por grupo
        </h2>
        <div className="flex gap-1.5 items-center">
          {pages.map((_, i) => (
            <span
              key={i}
              className={`w-2 h-2 rounded-full transition ${
                i === page ? "bg-brand" : "bg-line"
              }`}
            />
          ))}
        </div>
      </div>
      <div
        key={page}
        className="fade-swap grid grid-cols-6 gap-2"
        style={{ height: "calc(100% - 28px)" }}
      >
        {current.map((g) => (
          <GroupCard key={g.group} g={g} />
        ))}
      </div>
    </section>
  );
}
