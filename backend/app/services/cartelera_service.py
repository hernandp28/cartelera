"""
Arma la respuesta de la cartelera para una fecha dada.

Proveedor de datos (settings.data_provider):
  • "thesportsdb" → TheSportsDB (Mundial 2026 = liga 4429). Proveedor principal.
  • "sportmonks"  → Sportmonks (requiere plan con la liga del Mundial).
  • "seed"        → dataset DEMO local.

Modo de origen (settings.cartelera_source):
  • "auto" → usa el proveedor; si falla/no hay datos, cae al seed DEMO.
  • "live" → solo el proveedor (sin fallback).
  • "seed" → fuerza el seed DEMO.

Todos los horarios se entregan en hora Argentina.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.config import settings
from app.seed import worldcup2026 as seed

logger = logging.getLogger(__name__)

AR_TZ = ZoneInfo(settings.display_timezone)

# Cooldown tras un fallo del proveedor para no machacar la API.
_LIVE_DISABLED_UNTIL = 0.0
_COOLDOWN_SECONDS = 120


def _provider_matches_on(day: str) -> list[dict]:
    if settings.data_provider == "apifootball":
        from app.services.apifootball import apifootball
        return apifootball.matches_on(day)
    if settings.data_provider == "thesportsdb":
        from app.services.thesportsdb import thesportsdb
        return thesportsdb.matches_on(day)
    if settings.data_provider == "sportmonks":
        from app.services.cartelera_sportmonks import live_matches_on
        return live_matches_on(day)
    return seed.matches_on(day)


def _provider_groups() -> list[dict]:
    if settings.data_provider == "apifootball":
        from app.services.apifootball import apifootball
        return apifootball.group_tables()
    if settings.data_provider == "thesportsdb":
        from app.services.thesportsdb import thesportsdb
        return thesportsdb.group_tables()
    return []


def _resolve_source(day: str) -> tuple[list[dict], str, bool]:
    """Devuelve (partidos, source, is_demo)."""
    global _LIVE_DISABLED_UNTIL
    mode = settings.cartelera_source
    provider = settings.data_provider

    if mode == "seed" or provider == "seed":
        return seed.matches_on(day), "seed", True

    if mode == "live":
        return _provider_matches_on(day), provider, False

    # auto
    if time.monotonic() < _LIVE_DISABLED_UNTIL:
        return seed.matches_on(day), "seed", True
    try:
        matches = _provider_matches_on(day)
        if matches:
            return matches, provider, False
        logger.info("Sin partidos del proveedor para %s; usando seed DEMO.", day)
    except Exception as exc:  # noqa: BLE001 — cualquier fallo cae al seed
        logger.warning(
            "Proveedor %s no disponible (%s); seed DEMO + cooldown %ss.",
            provider, exc, _COOLDOWN_SECONDS,
        )
        _LIVE_DISABLED_UNTIL = time.monotonic() + _COOLDOWN_SECONDS
    return seed.matches_on(day), "seed", True


def _resolve_groups(source: str) -> list[dict]:
    """Tabla de posiciones; si el proveedor no la trae, cae al seed (12 grupos)."""
    if source != "seed":
        try:
            groups = _provider_groups()
            if groups:
                return groups
            logger.info("Proveedor sin tabla de grupos; usando seed para grupos.")
        except Exception as exc:  # noqa: BLE001
            logger.warning("No se pudo traer la tabla del proveedor (%s).", exc)
    return seed.group_tables()


def _resolve_tomorrow(day: str, source: str) -> list[dict]:
    tomorrow_day = (
        datetime.strptime(day, "%Y-%m-%d").date() + timedelta(days=1)
    ).isoformat()
    try:
        raw = seed.matches_on(tomorrow_day) if source == "seed" \
            else _provider_matches_on(tomorrow_day)
    except Exception:  # noqa: BLE001
        raw = seed.matches_on(tomorrow_day)
    raw.sort(key=lambda m: m["kickoff"])
    return [
        {"kickoff": m["kickoff"], "home": m["home"]["name"], "away": m["away"]["name"]}
        for m in raw
    ]


# Prioridad de orden en la agenda: primero EN VIVO, luego finalizados, etc.
_STATUS_PRIORITY = {
    "LIVE": 0, "HT": 0, "FT": 1, "AET": 1, "PEN": 1, "NS": 2, "POSTP": 3,
}

# Prioridad por selección para elegir qué partidos sobreviven al tope diario
# (nombres en castellano, como llegan ya traducidos).
_EUROPE_POWERS = {
    "España", "Francia", "Alemania", "Inglaterra", "Portugal", "Italia",
    "Países Bajos", "Bélgica", "Croacia",
}
_SOUTH_AMERICA = {
    "Brasil", "Uruguay", "Colombia", "Chile", "Paraguay", "Perú",
    "Ecuador", "Bolivia", "Venezuela",
}


def _team_tier(m: dict) -> int:
    """0=Argentina, 1=potencia europea, 2=sudamericano, 3=resto."""
    names = {m["home"]["name"], m["away"]["name"]}
    if "Argentina" in names:
        return 0
    if names & _EUROPE_POWERS:
        return 1
    if names & _SOUTH_AMERICA:
        return 2
    return 3


def get_lineups(fixture_id: str) -> dict:
    """Alineaciones (formación, DT, titulares, suplentes) de un partido."""
    if settings.data_provider == "apifootball":
        from app.services.apifootball import apifootball
        try:
            return apifootball.lineups(int(fixture_id))
        except Exception as exc:  # noqa: BLE001
            logger.warning("lineups %s falló: %s", fixture_id, exc)
    return {"home": None, "away": None}


def build_cartelera(day: str) -> dict:
    agenda, source, is_demo = _resolve_source(day)

    # 1) Si hay más partidos que el tope, se eligen por prioridad de selección:
    #    Argentina > potencias europeas > sudamericanos > resto.
    agenda.sort(
        key=lambda m: (
            _team_tier(m), _STATUS_PRIORITY.get(m["status"], 2), m["kickoff"]
        )
    )
    agenda = agenda[: settings.agenda_max_matches]

    # 2) Orden de pantalla: EN VIVO primero, luego por horario.
    agenda.sort(
        key=lambda m: (
            _STATUS_PRIORITY.get(m["status"], 2), m["kickoff"], str(m["id"])
        )
    )

    # Goleadores y expulsados: solo para los partidos que se muestran
    if source == "apifootball":
        from app.services.apifootball import apifootball
        apifootball.enrich_with_events(agenda)
    elif source == "thesportsdb":
        from app.services.thesportsdb import thesportsdb
        thesportsdb.enrich_with_timeline(agenda)

    return {
        "date": day,
        "timezone": settings.display_timezone,
        "source": source,
        "is_demo": is_demo,
        "title": "Mundial 2026",
        "agenda": agenda,
        "groups": _resolve_groups(source),
        "tomorrow": _resolve_tomorrow(day, source),
        "generated_at": datetime.now(AR_TZ).isoformat(),
    }
