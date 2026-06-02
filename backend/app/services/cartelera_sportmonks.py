"""Mapeo de fixtures de Sportmonks a tarjetas de cartelera (proveedor alternativo).

Solo se usa si DATA_PROVIDER=sportmonks. Requiere un plan con la liga del Mundial.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.config import settings
from app.services.sportmonks import sportmonks

AR_TZ = ZoneInfo(settings.display_timezone)
UTC = ZoneInfo("UTC")

_STATE_MAP = {
    "NS": "NS", "INPLAY_1ST_HALF": "LIVE", "HT": "HT",
    "INPLAY_2ND_HALF": "LIVE", "INPLAY_ET": "LIVE", "BREAK": "LIVE",
    "INPLAY_PENALTIES": "LIVE", "FT": "FT", "AET": "AET",
    "FT_PEN": "PEN", "POSTPONED": "POSTP", "CANCELLED": "POSTP",
}


def _utc_to_ar(dt_str: str) -> datetime:
    return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S").replace(
        tzinfo=UTC
    ).astimezone(AR_TZ)


def _map_fixture(fx: dict) -> dict:
    parts = {p.get("meta", {}).get("location"): p for p in fx.get("participants", [])}
    home, away = parts.get("home", {}), parts.get("away", {})
    state = (fx.get("state") or {}).get("short_name") or (
        fx.get("state") or {}
    ).get("developer_name", "NS")
    status = _STATE_MAP.get(state, "NS")

    hs = as_ = None
    for sc in fx.get("scores", []):
        if sc.get("description") == "CURRENT":
            g = sc.get("score", {})
            if g.get("participant") == "home":
                hs = g.get("goals")
            elif g.get("participant") == "away":
                as_ = g.get("goals")

    ar = _utc_to_ar(fx["starting_at"])

    def ref(p: dict) -> dict:
        return {
            "id": p.get("id"), "name": p.get("name", "—"),
            "code": (p.get("short_code") or "").lower() or None,
            "flag_url": p.get("image_path"), "logo_url": p.get("image_path"),
        }

    return {
        "id": fx["id"], "date": ar.date().isoformat(),
        "kickoff": ar.strftime("%H:%M"), "status": status,
        "minute": fx.get("minute"), "stage": (fx.get("league") or {}).get("name"),
        "group": (fx.get("group") or {}).get("name"),
        "venue": (fx.get("venue") or {}).get("name"),
        "home": ref(home), "away": ref(away),
        "home_score": hs, "away_score": as_,
        "home_pens": None, "away_pens": None, "scorers": [], "red_cards": [],
    }


def live_matches_on(day: str) -> list[dict]:
    base = datetime.strptime(day, "%Y-%m-%d").date()
    seen, fixtures = set(), []
    for offset in (-1, 0, 1):
        d = (base + timedelta(days=offset)).isoformat()
        for fx in sportmonks.fixtures_by_date(d):
            if fx["id"] not in seen:
                seen.add(fx["id"])
                fixtures.append(fx)
    return [m for m in (_map_fixture(f) for f in fixtures) if m["date"] == day]
