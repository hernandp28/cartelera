"""
Cliente API-Football v3 (acceso directo api-sports.io).
Doc: https://www.api-football.com/documentation-v3

Auth: header `x-apisports-key: <API_KEY>`.  Base: https://v3.football.api-sports.io
Mundial 2026: league=1, season=2026. Soporta `timezone=` → horarios en hora AR.

Ventajas sobre el proveedor anterior:
  • /standings?league=1&season=2026 trae los 12 grupos nativos.
  • /fixtures/events?fixture=ID trae goleadores y tarjetas (también en vivo).
  • /fixtures?live=all para refrescar minuto/marcador en vivo.
"""
from __future__ import annotations

import logging
import re
import time
from collections import deque
from typing import Any

import httpx

from app.config import settings
from app.services.flags import es_name, flag_for

logger = logging.getLogger(__name__)

# status.short de API-Football -> estado de cartelera
_STATUS_MAP = {
    "TBD": "NS", "NS": "NS",
    "1H": "LIVE", "2H": "LIVE", "ET": "LIVE", "BT": "LIVE", "P": "LIVE",
    "LIVE": "LIVE", "INT": "LIVE",
    "HT": "HT",
    "FT": "FT", "AET": "AET", "PEN": "PEN",
    "PST": "POSTP", "CANC": "POSTP", "ABD": "POSTP", "SUSP": "POSTP",
    "AWD": "POSTP", "WO": "POSTP",
}
_FINISHED = {"FT", "AET", "PEN"}


class APIFootballError(RuntimeError):
    pass


class _RateLimiter:
    def __init__(self, max_per_min: int) -> None:
        self.max = max_per_min
        self.calls: deque[float] = deque()

    def acquire(self) -> None:
        now = time.monotonic()
        while self.calls and now - self.calls[0] > 60:
            self.calls.popleft()
        if len(self.calls) >= self.max:
            raise APIFootballError(f"Rate limit {self.max}/min alcanzado.")
        self.calls.append(now)


def _to_int(v: Any) -> int | None:
    try:
        return int(v) if v not in (None, "") else None
    except (TypeError, ValueError):
        return None


_YOUTH_RE = re.compile(r"\bU\d{1,2}\b", re.IGNORECASE)


def _is_senior_men(name: str | None) -> bool:
    """Excluye juveniles (U17..U23) y femenino de los amistosos."""
    n = name or ""
    if _YOUTH_RE.search(n):
        return False
    if n.endswith(" W") or "women" in n.lower():
        return False
    return True


class APIFootballClient:
    def __init__(self) -> None:
        self.base = settings.apifootball_base_url.rstrip("/")
        self.key = settings.apifootball_api_key
        self.tz = settings.display_timezone
        self.league_id = settings.apifootball_league_id
        self.season = settings.apifootball_season
        self.limiter = _RateLimiter(settings.apifootball_rate_limit_per_min)
        self._cache: dict[str, tuple[float, Any]] = {}

    # ── HTTP ──────────────────────────────────────────────────────────
    def _get(self, path: str, params: dict[str, Any] | None = None) -> list[dict]:
        if not self.key:
            raise APIFootballError("Falta APIFOOTBALL_API_KEY en el entorno.")
        self.limiter.acquire()
        url = f"{self.base}/{path.lstrip('/')}"
        try:
            with httpx.Client(timeout=20.0) as client:
                resp = client.get(
                    url, params=params or {}, headers={"x-apisports-key": self.key}
                )
        except httpx.HTTPError as exc:
            raise APIFootballError(f"Error de red API-Football: {exc}") from exc
        if resp.status_code == 429:
            raise APIFootballError("API-Football 429 (rate limit).")
        if resp.status_code >= 400:
            raise APIFootballError(f"API-Football {resp.status_code}: {resp.text[:160]}")
        data = resp.json() or {}
        errors = data.get("errors")
        if errors:  # puede ser dict o list
            raise APIFootballError(f"API-Football errores: {errors}")
        return data.get("response") or []

    def _cached(self, key: str, ttl: float, fn) -> Any:
        hit = self._cache.get(key)
        if hit and time.monotonic() - hit[0] < ttl:
            return hit[1]
        val = fn()
        self._cache[key] = (time.monotonic(), val)
        return val

    # ── Normalización de fixtures ─────────────────────────────────────
    def _map_fixture(self, fx: dict) -> dict:
        f = fx.get("fixture", {})
        lg = fx.get("league", {})
        teams = fx.get("teams", {})
        goals = fx.get("goals", {})
        pen = (fx.get("score", {}) or {}).get("penalty", {}) or {}
        home, away = teams.get("home", {}), teams.get("away", {})

        date_iso = f.get("date") or ""  # ya en hora AR por el param timezone
        date = date_iso[:10]
        kickoff = date_iso[11:16]

        st = (f.get("status", {}) or {})
        status = _STATUS_MAP.get(st.get("short", "NS"), "NS")
        minute = st.get("elapsed") if status in ("LIVE", "HT") else None

        league_name = lg.get("name") or ""
        round_name = lg.get("round") or ""
        is_friendly = "friend" in league_name.lower()
        stage = "Amistoso" if is_friendly else (round_name or league_name)
        # Grupo: de "Group Stage - 1" no sale el grupo; eso viene de standings.
        group = None
        if round_name.lower().startswith("group ") and "-" not in round_name:
            group = round_name.split(" ")[-1]

        def ref(t: dict) -> dict:
            return {
                "id": t.get("id"),
                "name": es_name(t.get("name")),
                "code": None,
                "flag_url": flag_for(t.get("name"), t.get("logo")),
                "logo_url": t.get("logo"),
            }

        return {
            "id": f.get("id"),
            "date": date,
            "kickoff": kickoff,
            "status": status,
            "minute": minute,
            "league_id": lg.get("id"),
            "stage": stage,
            "competition": league_name,
            "group": group,
            "venue": (f.get("venue", {}) or {}).get("name"),
            "home": ref(home),
            "away": ref(away),
            "home_score": _to_int(goals.get("home")),
            "away_score": _to_int(goals.get("away")),
            "home_pens": _to_int(pen.get("home")),
            "away_pens": _to_int(pen.get("away")),
            "scorers": [],
            "red_cards": [],
        }

    # ── Fixtures por liga/temporada (cache 5 min) ─────────────────────
    def _season_fixtures(self, league_id: int) -> list[dict]:
        def fetch() -> list[dict]:
            raw = self._get(
                "fixtures",
                {"league": league_id, "season": self.season, "timezone": self.tz},
            )
            return [self._map_fixture(fx) for fx in raw]

        return self._cached(f"season-{league_id}", 300, fetch)

    @property
    def agenda_league_ids(self) -> list[int]:
        ids = [self.league_id]
        if settings.apifootball_include_friendlies:
            ids.append(settings.apifootball_friendlies_league_id)
        return ids

    def _live_map(self) -> dict[int, dict]:
        """Fixtures en vivo (todas las ligas) -> {id: fixture crudo}. Cache 60 s."""
        def fetch() -> dict[int, dict]:
            try:
                raw = self._get("fixtures", {"live": "all", "timezone": self.tz})
            except APIFootballError as exc:
                logger.warning("live=all falló: %s", exc)
                return {}
            return {fx["fixture"]["id"]: fx for fx in raw if fx.get("fixture")}

        return self._cached("live", 60, fetch)

    def _overlay_live(self, matches: list[dict]) -> None:
        live = self._live_map()
        if not live:
            return
        for m in matches:
            fx = live.get(m["id"])
            if not fx:
                continue
            mapped = self._map_fixture(fx)
            m["status"] = mapped["status"]
            m["minute"] = mapped["minute"]
            if mapped["home_score"] is not None:
                m["home_score"] = mapped["home_score"]
            if mapped["away_score"] is not None:
                m["away_score"] = mapped["away_score"]

    def _team_group_map(self) -> dict:
        """{team_id: 'A'} para el Mundial, derivado de standings (cache reusada)."""
        def fetch() -> dict:
            mapping = {}
            for t in self.group_tables():
                for row in t["rows"]:
                    mapping[row["team"]["id"]] = t["group"]
            return mapping
        return self._cached("teamgroups", 60, fetch)

    def all_agenda_matches(self) -> list[dict]:
        out: list[dict] = []
        for lid in self.agenda_league_ids:
            try:
                fixtures = self._season_fixtures(lid)
            except APIFootballError as exc:
                logger.warning("No se pudo traer la liga %s: %s", lid, exc)
                continue
            # Amistosos: solo selecciones mayores masculinas (sin U23/femenino)
            if lid == settings.apifootball_friendlies_league_id:
                fixtures = [
                    m for m in fixtures
                    if _is_senior_men(m["home"]["name"]) and _is_senior_men(m["away"]["name"])
                ]
            out.extend(fixtures)
        self._overlay_live(out)

        # Letra de grupo para las tarjetas del Mundial (el fixture no la trae)
        try:
            gmap = self._team_group_map()
        except APIFootballError:
            gmap = {}
        for m in out:
            if m.get("league_id") == self.league_id and not m.get("group"):
                m["group"] = gmap.get(m["home"]["id"]) or gmap.get(m["away"]["id"])
        return out

    def matches_on(self, day: str) -> list[dict]:
        return [m for m in self.all_agenda_matches() if m["date"] == day]

    # ── Eventos: goleadores y expulsados ──────────────────────────────
    def _events(self, fixture_id: int, home_id, away_id, finished: bool) -> tuple[list, list]:
        ttl = 600 if finished else 60
        key = f"ev-{fixture_id}"

        def fetch() -> tuple[list, list]:
            # OJO: /fixtures/events NO acepta el parámetro timezone.
            raw = self._get("fixtures/events", {"fixture": fixture_id})
            scorers, reds = [], []
            for ev in raw:
                etype = (ev.get("type") or "").lower()
                detail = (ev.get("detail") or "").lower()
                team_id = (ev.get("team", {}) or {}).get("id")
                player = (ev.get("player", {}) or {}).get("name") or ""
                minute = (ev.get("time", {}) or {}).get("elapsed")
                if not player:
                    continue
                side = "home" if team_id == home_id else "away"
                if etype == "goal" and "missed" not in detail:
                    scoring = side
                    label = player
                    if "own" in detail:
                        scoring = "away" if side == "home" else "home"
                        label = f"{player} (ec)"
                    elif "penal" in detail:
                        label = f"{player} (p)"
                    scorers.append(
                        {"minute": minute, "player": label, "team_side": scoring}
                    )
                elif etype == "card" and "red" in detail:
                    reds.append({"minute": minute, "player": player, "team_side": side})
            scorers.sort(key=lambda e: e["minute"] or 0)
            reds.sort(key=lambda e: e["minute"] or 0)
            return scorers, reds

        return self._cached(key, ttl, fetch)

    def enrich_with_events(self, matches: list[dict]) -> None:
        """Rellena scorers/red_cards de cada partido EN VIVO o finalizado."""
        for m in matches:
            if m["status"] not in ("LIVE", "HT", "FT", "AET", "PEN"):
                continue
            try:
                scorers, reds = self._events(
                    m["id"], m["home"]["id"], m["away"]["id"],
                    finished=m["status"] in _FINISHED,
                )
            except APIFootballError as exc:
                logger.warning("events %s falló: %s", m["id"], exc)
                continue
            if scorers:
                m["scorers"] = scorers
            if reds:
                m["red_cards"] = reds

    # ── Alineaciones (formación, DT, titulares, suplentes) ───────────
    def lineups(self, fixture_id: int) -> dict:
        """Devuelve {'home': {...}, 'away': {...}} o None si no hay datos."""
        _POS = {"G": "ARQ", "D": "DEF", "M": "MED", "F": "DEL"}

        def player(p: dict) -> dict:
            pl = p.get("player", {}) or {}
            return {
                "name": pl.get("name"),
                "number": pl.get("number"),
                "pos": _POS.get(pl.get("pos"), pl.get("pos")),
            }

        def team_block(t: dict) -> dict:
            tm = t.get("team", {}) or {}
            return {
                "team": {
                    "id": tm.get("id"),
                    "name": es_name(tm.get("name")),
                    "flag_url": flag_for(tm.get("name"), tm.get("logo")),
                    "logo_url": tm.get("logo"),
                },
                "coach": (t.get("coach") or {}).get("name"),
                "formation": t.get("formation"),
                "startXI": [player(p) for p in (t.get("startXI") or [])],
                "substitutes": [player(p) for p in (t.get("substitutes") or [])],
            }

        def fetch() -> dict:
            raw = self._get("fixtures/lineups", {"fixture": fixture_id})
            blocks = [team_block(t) for t in raw]
            return {
                "home": blocks[0] if len(blocks) > 0 else None,
                "away": blocks[1] if len(blocks) > 1 else None,
            }

        return self._cached(f"lineup-{fixture_id}", 600, fetch)

    # ── Standings (grupos nativos) ────────────────────────────────────
    def group_tables(self) -> list[dict]:
        def fetch() -> list[dict]:
            raw = self._get(
                "standings", {"league": self.league_id, "season": self.season}
            )
            if not raw:
                return []
            groups_raw = (raw[0].get("league", {}) or {}).get("standings") or []
            tables = []
            for grp in groups_raw:
                if not grp:
                    continue
                raw_label = grp[0].get("group") or ""
                label = raw_label.replace("Group ", "").strip()
                # Solo grupos reales "Group A".."Group L" (1 letra). Excluye
                # "Group Stage", "Ranking of third-placed teams", etc.
                if len(label) != 1 or not label.isalpha():
                    continue
                tables.append({
                    "group": label or "?",
                    "rows": [
                        {
                            "position": r.get("rank") or i + 1,
                            "team": {
                                "id": (r.get("team", {}) or {}).get("id"),
                                "name": es_name((r.get("team", {}) or {}).get("name")),
                                "code": None,
                                "flag_url": flag_for(
                                    (r.get("team", {}) or {}).get("name"),
                                    (r.get("team", {}) or {}).get("logo"),
                                ),
                            },
                            "points": r.get("points") or 0,
                            "played": ((r.get("all", {}) or {}).get("played")) or 0,
                            "goal_diff": r.get("goalsDiff") or 0,
                        }
                        for i, r in enumerate(grp)
                    ],
                })
            return tables

        return self._cached("standings", 60, fetch)


apifootball = APIFootballClient()
