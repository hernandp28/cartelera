"""
Servicio de alertas — derivadas de datos reales disponibles (sin inventar).

Hoy genera alertas a partir del calendario: jornadas con muchos partidos,
inicio del torneo, etc. Cuando estén activas las lesiones/sanciones/noticias,
estas se sumarán como alertas críticas.
"""
from __future__ import annotations

from collections import Counter
from datetime import date

from app.seed import worldcup2026 as seed


def current_alerts() -> list[dict]:
    alerts: list[dict] = []
    matches = seed.all_matches()
    if not matches:
        return alerts

    by_day = Counter(m["date"] for m in matches)
    first_day = min(by_day)
    alerts.append({
        "level": "info",
        "title": "Inicio del Mundial 2026",
        "detail": f"La fase de grupos (datos DEMO) arranca el {first_day}.",
        "date": first_day,
    })

    for day, count in sorted(by_day.items()):
        if count >= 8:
            alerts.append({
                "level": "medium",
                "title": f"Jornada cargada: {count} partidos",
                "detail": f"El {day} hay {count} partidos programados.",
                "date": day,
            })

    alerts.append({
        "level": "info",
        "title": "Lesiones/sanciones pendientes de fuente",
        "detail": "El motor de bajas se activa al conectar API de lesiones/noticias.",
        "date": date.today().isoformat(),
    })
    return alerts
