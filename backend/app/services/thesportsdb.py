"""
Cliente TheSportsDB v1 (https://www.thesportsdb.com/documentation).

Autenticación premium: la API key va en el PATH de la URL ->
    https://www.thesportsdb.com/api/v1/json/{API_KEY}/<endpoint>
Límite premium: 100 req/min.

Para el Mundial 2026: league_id 4429, season "2026".
Estrategia eficiente: se baja UNA vez el fixture completo de la temporada
(eventsseason) y la tabla (lookuptable), con cache en memoria de 5 minutos.
Todos los horarios se normalizan a hora Argentina (strTimestamp viene en UTC).
"""
from __future__ import annotations

import logging
import time
from collections import deque
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import httpx

from app.config import settings
from app.services.flags import es_name, flag_for

logger = logging.getLogger(__name__)

AR_TZ = ZoneInfo(settings.display_timezone)
UTC = ZoneInfo("UTC")

# strStatus de TheSportsDB -> estado de cartelera
_STATUS_MAP = {
    "NS": "NS", "NOT STARTED": "NS", "TBD": "NS", "": "NS",
    "1H": "LIVE", "2H": "LIVE", "ET": "LIVE", "LIVE": "LIVE",
    "P": "LIVE", "BT": "LIVE", "INPLAY": "LIVE", "PLAYING": "LIVE",
    "HT": "HT", "HALF TIME": "HT",
    "FT": "FT", "MATCH FINISHED": "FT", "FINISHED": "FT", "AP": "PEN",
    "AET": "AET", "AFTER EXTRA TIME": "AET",
    "PEN": "PEN", "PENALTIES": "PEN", "AFTER PENALTIES": "PEN",
    "PPD": "POSTP", "POSTPONED": "POSTP", "POSTP": "POSTP", "CANC": "POSTP",
}


class TheSportsDBError(RuntimeError):
    pass


class _RateLimiter:
    """Ventana deslizante de 60 s."""

    def __init__(self, max_per_min: int) -> None:
        self.max = max_per_min
        self.calls: deque[float] = deque()

    def acquire(self) -> None:
        now = time.monotonic()
        while self.calls and now - self.calls[0] > 60:
            self.calls.popleft()
        if len(self.calls) >= self.max:
            raise TheSportsDBError(f"Rate limit {self.max}/min alcanzado.")
        self.calls.append(now)


def _to_int(v: Any) -> int | None:
    try:
        return int(v) if v not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _parse_goal_details(details: str | None, side: str) -> list[dict]:
    """Parsea 'XX':Jugador;YY':Otro' (formato legacy de TheSportsDB)."""
    out: list[dict] = []
    if not details:
        return out
    for chunk in details.replace("\r", "").replace("\n", ";").split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        minute, _, name = chunk.partition(":")
        minute = minute.replace("'", "").strip()
        name = name.strip()
        if name:
            out.append({"minute": _to_int(minute), "player": name, "team_side": side})
    return out


def _parse_timeline(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    """Extrae goleadores y expulsados del timeline (v1 lookuptimeline)."""
    scorers: list[dict] = []
    reds: list[dict] = []
    for r in rows:
        kind = (r.get("strTimeline") or "").lower()
        detail = (r.get("strTimelineDetail") or "").lower()
        player = (r.get("strPlayer") or "").strip()
        if not player:
            continue
        side = "home" if (r.get("strHome") or "").strip().lower() in (
            "yes", "home", "1", "true"
        ) else "away"
        minute = _to_int(r.get("intTime"))

        # Solo goles REALES: type == "Goal". Se excluyen VAR/anulados/errados
        # (esos vienen como type "Var" o con detalle "disallowed/cancelled/missed").
        invalid = any(
            x in detail for x in ("disallow", "cancel", "missed", "no goal", "offside")
        )
        if kind == "goal" and not invalid:
            scoring_side = side
            label = player
            if "own" in detail:  # gol en contra: cuenta para el rival
                scoring_side = "away" if side == "home" else "home"
                label = f"{player} (ec)"
            elif "penal" in detail:
                label = f"{player} (p)"
            scorers.append(
                {"minute": minute, "player": label, "team_side": scoring_side}
            )
        elif kind == "card" and "red" in detail:  # "Red Card"/"Yellow-Red Card"
            reds.append({"minute": minute, "player": player, "team_side": side})
    scorers.sort(key=lambda e: e["minute"] or 0)
    reds.sort(key=lambda e: e["minute"] or 0)
    return scorers, reds


class TheSportsDBClient:
    def __init__(self) -> None:
        self.base = settings.thesportsdb_base_url.rstrip("/")
        self.key = settings.thesportsdb_api_key or "3"
        self.league_id = settings.thesportsdb_league_id
        self.season = settings.thesportsdb_season
        self.limiter = _RateLimiter(settings.thesportsdb_rate_limit_per_min)
        self._cache: dict[str, tuple[float, Any]] = {}
        self._ttl = 60  # 1 min (para reflejar marcadores en vivo)

    @property
    def is_premium(self) -> bool:
        return self.key not in ("", "3", "123", "1")

    def _get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict:
        self.limiter.acquire()
        url = f"{self.base}/{self.key}/{endpoint}"
        try:
            with httpx.Client(timeout=20.0) as client:
                resp = client.get(url, params=params or {})
        except httpx.HTTPError as exc:
            raise TheSportsDBError(f"Error de red TheSportsDB: {exc}") from exc
        if resp.status_code == 429:
            raise TheSportsDBError("TheSportsDB 429 (rate limit).")
        if resp.status_code >= 400:
            raise TheSportsDBError(f"TheSportsDB {resp.status_code}: {resp.text[:160]}")
        return resp.json() or {}

    def _cached(self, key: str, endpoint: str, params: dict | None = None) -> dict:
        hit = self._cache.get(key)
        if hit and time.monotonic() - hit[0] < self._ttl:
            return hit[1]
        data = self._get(endpoint, params)
        self._cache[key] = (time.monotonic(), data)
        return data

    def _get_v2(self, path: str) -> dict:
        """v2 usa header X-API-KEY en vez de la key en el path."""
        self.limiter.acquire()
        base_v2 = self.base.replace("/api/v1/json", "/api/v2/json")
        url = f"{base_v2}/{path.lstrip('/')}"
        try:
            with httpx.Client(timeout=20.0) as client:
                resp = client.get(url, headers={"X-API-KEY": self.key})
        except httpx.HTTPError as exc:
            raise TheSportsDBError(f"Error de red TheSportsDB v2: {exc}") from exc
        if resp.status_code >= 400:
            raise TheSportsDBError(f"TheSportsDB v2 {resp.status_code}")
        return resp.json() or {}

    # Cache corto del livescore (refresco del front cada 10 s)
    _LIVE_TTL = 5

    def live_scores(self) -> dict[str, dict]:
        """Mapa idEvent -> registro en vivo (minuto, estado, marcador)."""
        hit = self._cache.get("livescore")
        if hit and time.monotonic() - hit[0] < self._LIVE_TTL:
            return hit[1]
        try:
            data = self._get_v2("livescore/soccer")
        except TheSportsDBError as exc:
            logger.warning("livescore v2 no disponible: %s", exc)
            data = {}
        rows = data.get("livescore") or []
        mapping = {str(r.get("idEvent")): r for r in rows}
        self._cache["livescore"] = (time.monotonic(), mapping)
        return mapping

    # --- Normalización ---

    def _map_event(self, e: dict) -> dict:
        ts = e.get("strTimestamp")
        if ts:
            try:
                ar = datetime.fromisoformat(ts.replace("Z", "")).replace(
                    tzinfo=UTC
                ).astimezone(AR_TZ)
            except ValueError:
                ar = None
        else:
            ar = None
        date = ar.date().isoformat() if ar else (e.get("dateEvent") or "")
        kickoff = ar.strftime("%H:%M") if ar else (e.get("strTime") or "")[:5]

        status = _STATUS_MAP.get((e.get("strStatus") or "").strip().upper(), "NS")
        if (e.get("strPostponed") or "").lower() == "yes":
            status = "POSTP"

        progress = e.get("strProgress")
        minute = _to_int(progress) if status in ("LIVE", "HT") else None

        scorers = _parse_goal_details(e.get("strHomeGoalDetails"), "home") + \
            _parse_goal_details(e.get("strAwayGoalDetails"), "away")
        reds = _parse_goal_details(e.get("strHomeRedCards"), "home") + \
            _parse_goal_details(e.get("strAwayRedCards"), "away")

        league = e.get("strLeague") or ""
        if "friendl" in league.lower():
            stage = "Amistoso FIFA"
        else:
            stage = e.get("strStage") or league

        return {
            "id": e.get("idEvent"),
            "date": date,
            "kickoff": kickoff,
            "status": status,
            "minute": minute,
            "round": _to_int(e.get("intRound")),
            "stage": stage,
            "competition": league,
            "group": (e.get("strGroup") or "").replace("Group ", "").strip() or None,
            "venue": e.get("strVenue"),
            "home": {
                "id": e.get("idHomeTeam"),
                "name": es_name(e.get("strHomeTeam")),
                "code": None,
                "flag_url": flag_for(e.get("strHomeTeam"), e.get("strHomeTeamBadge")),
                "logo_url": e.get("strHomeTeamBadge"),
            },
            "away": {
                "id": e.get("idAwayTeam"),
                "name": es_name(e.get("strAwayTeam")),
                "code": None,
                "flag_url": flag_for(e.get("strAwayTeam"), e.get("strAwayTeamBadge")),
                "logo_url": e.get("strAwayTeamBadge"),
            },
            "home_score": _to_int(e.get("intHomeScore")),
            "away_score": _to_int(e.get("intAwayScore")),
            "home_pens": _to_int(e.get("intHomeScorePenalty") or e.get("intHomePenalty")),
            "away_pens": _to_int(e.get("intAwayScorePenalty") or e.get("intAwayPenalty")),
            "scorers": scorers,
            "red_cards": reds,
        }

    # --- API pública usada por la cartelera ---

    def _league_season_matches(self, league_id: int) -> list[dict]:
        """Fixture de una liga/temporada (cacheado), normalizado."""
        data = self._cached(
            f"season-{league_id}",
            "eventsseason.php",
            {"id": league_id, "s": self.season},
        )
        events = data.get("events") or []
        return [self._map_event(e) for e in events]

    def season_matches(self) -> list[dict]:
        """Fixture completo del Mundial (define los grupos)."""
        return self._league_season_matches(self.league_id)

    @property
    def agenda_league_ids(self) -> list[int]:
        ids = [self.league_id]
        if settings.thesportsdb_include_friendlies:
            ids.append(settings.thesportsdb_friendlies_league_id)
        return ids

    def all_agenda_matches(self) -> list[dict]:
        """Mundial + amistosos (si está habilitado), con overlay en vivo."""
        out: list[dict] = []
        for lid in self.agenda_league_ids:
            try:
                out.extend(self._league_season_matches(lid))
            except TheSportsDBError as exc:
                logger.warning("No se pudo traer la liga %s: %s", lid, exc)
        self._overlay_live(out)
        return out

    def _overlay_live(self, matches: list[dict]) -> None:
        """Pisa minuto/estado/marcador con el feed en vivo (v2 livescore)."""
        live = self.live_scores()
        if not live:
            return
        for m in matches:
            rec = live.get(str(m["id"]))
            if not rec:
                continue
            status = _STATUS_MAP.get(
                (rec.get("strStatus") or "").strip().upper(), m["status"]
            )
            m["status"] = status
            prog = _to_int(rec.get("strProgress"))
            if status in ("LIVE", "HT"):
                m["minute"] = prog
            hs = _to_int(rec.get("intHomeScore"))
            as_ = _to_int(rec.get("intAwayScore"))
            if hs is not None:
                m["home_score"] = hs
            if as_ is not None:
                m["away_score"] = as_

    def matches_on(self, day: str) -> list[dict]:
        return [m for m in self.all_agenda_matches() if m["date"] == day]

    # --- Goleadores / expulsados (solo para los partidos mostrados) ---

    def _cached_call(self, key: str, ttl: float, fn) -> tuple[list, list]:
        hit = self._cache.get(key)
        if hit and time.monotonic() - hit[0] < ttl:
            return hit[1]
        parsed = fn()
        self._cache[key] = (time.monotonic(), parsed)
        return parsed

    def _event_timeline(self, event_id: str, finished: bool) -> tuple[list, list]:
        """Goleadores/expulsados desde lookuptimeline (fuente principal)."""
        ttl = 600 if finished else 10  # finalizados no cambian; en vivo refresca
        return self._cached_call(
            f"tl-{event_id}", ttl,
            lambda: _parse_timeline(
                self._get("lookuptimeline.php", {"id": event_id}).get("timeline") or []
            ),
        )

    def _event_goaldetails(self, event_id: str, finished: bool) -> tuple[list, list]:
        """Fuente secundaria: campos strHomeGoalDetails/RedCards de lookupevent."""
        def fetch() -> tuple[list, list]:
            e = (self._get("lookupevent.php", {"id": event_id}).get("events")
                 or [{}])[0]
            scorers = (
                _parse_goal_details(e.get("strHomeGoalDetails"), "home")
                + _parse_goal_details(e.get("strAwayGoalDetails"), "away")
            )
            reds = (
                _parse_goal_details(e.get("strHomeRedCards"), "home")
                + _parse_goal_details(e.get("strAwayRedCards"), "away")
            )
            return scorers, reds

        return self._cached_call(f"gd-{event_id}", 600 if finished else 10, fetch)

    def enrich_with_timeline(self, matches: list[dict]) -> None:
        """Rellena scorers/red_cards de cada partido EN VIVO o finalizado.

        Usa el timeline como fuente principal y, si hay goles pero el timeline
        aún no los trae (retraso típico en partidos en vivo), intenta una
        segunda fuente (goal details del evento). Si ninguna tiene el dato, se
        deja vacío (no se inventa: TheSportsDB a veces publica el goleador con
        demora respecto al marcador).
        """
        for m in matches:
            if m["status"] not in ("LIVE", "HT", "FT", "AET", "PEN"):
                continue
            finished = m["status"] in ("FT", "AET", "PEN")
            eid = str(m["id"])
            try:
                scorers, reds = self._event_timeline(eid, finished)
            except TheSportsDBError as exc:
                logger.warning("timeline %s falló: %s", eid, exc)
                scorers, reds = [], []

            has_goals = (m.get("home_score") or 0) + (m.get("away_score") or 0) > 0
            if not scorers and has_goals:
                try:
                    s2, r2 = self._event_goaldetails(eid, finished)
                    scorers = scorers or s2
                    reds = reds or r2
                except TheSportsDBError:
                    pass

            if scorers:
                m["scorers"] = scorers
            if reds:
                m["red_cards"] = reds

    def group_tables(self) -> list[dict]:
        """Tabla de posiciones agrupada por strGroup (lookuptable)."""
        data = self._cached(
            "table",
            "lookuptable.php",
            {"l": self.league_id, "s": self.season},
        )
        rows = data.get("table") or []
        groups: dict[str, list[dict]] = {}
        for r in rows:
            g = (r.get("strGroup") or "").replace("Group ", "").strip()
            if not g:
                continue
            groups.setdefault(g, []).append(r)

        tables: list[dict] = []
        for g in sorted(groups):
            entries = sorted(groups[g], key=lambda x: _to_int(x.get("intRank")) or 99)
            tables.append({
                "group": g,
                "rows": [
                    {
                        "position": _to_int(r.get("intRank")) or i + 1,
                        "team": {
                            "id": r.get("idTeam"),
                            "name": es_name(r.get("strTeam")),
                            "code": None,
                            "flag_url": flag_for(r.get("strTeam"), r.get("strBadge")),
                        },
                        "points": _to_int(r.get("intPoints")) or 0,
                        "played": _to_int(r.get("intPlayed")) or 0,
                        "goal_diff": _to_int(r.get("intGoalDifference")) or 0,
                    }
                    for i, r in enumerate(entries)
                ],
            })

        # Fallback: si la tabla no trae grupos, los armamos desde los partidos
        # (equipos y posiciones reales calculadas de los resultados disponibles).
        if not tables:
            tables = self._group_tables_from_matches()
        return tables

    def _group_tables_from_matches(self) -> list[dict]:
        """
        Reconstruye los 12 grupos a partir del fixture REAL.

        TheSportsDB no publica `strGroup` para el Mundial 2026, pero en fase de
        grupos cada grupo es un round-robin de 4 selecciones que solo juegan entre
        sí. Detectamos los grupos como *componentes conexas* del grafo de
        enfrentamientos (rondas 1–3). Composición y resultados = 100% reales; la
        LETRA del grupo se asigna por orden de fecha del primer partido (el grupo
        del partido inaugural queda como A).
        """
        finished = {"FT", "AET", "PEN"}
        matches = [m for m in self.season_matches() if (m.get("round") or 0) in (1, 2, 3)]
        if not matches:
            return []

        # Info por equipo + grafo de adyacencia
        info: dict[str, dict] = {}
        adj: dict[str, set[str]] = {}
        first_ts: dict[str, str] = {}
        for m in matches:
            ids = []
            for side in ("home", "away"):
                t = m[side]
                tid = str(t.get("id") or t["name"])
                ids.append(tid)
                info.setdefault(tid, {
                    "id": t.get("id"), "name": t["name"],
                    "flag_url": t.get("flag_url"),
                    "pts": 0, "pj": 0, "gf": 0, "gc": 0,
                })
                ts = m.get("date", "") + m.get("kickoff", "")
                if tid not in first_ts or ts < first_ts[tid]:
                    first_ts[tid] = ts
            adj.setdefault(ids[0], set()).add(ids[1])
            adj.setdefault(ids[1], set()).add(ids[0])

            # Acumular resultados (solo partidos jugados)
            if m["status"] in finished and m["home_score"] is not None:
                hid, aid = ids
                hs, as_ = m["home_score"], m["away_score"] or 0
                info[hid]["pj"] += 1; info[aid]["pj"] += 1
                info[hid]["gf"] += hs; info[hid]["gc"] += as_
                info[aid]["gf"] += as_; info[aid]["gc"] += hs
                if hs > as_:
                    info[hid]["pts"] += 3
                elif as_ > hs:
                    info[aid]["pts"] += 3
                else:
                    info[hid]["pts"] += 1; info[aid]["pts"] += 1

        # Componentes conexas (cada grupo = 4 equipos)
        seen: set[str] = set()
        comps: list[list[str]] = []
        for t in adj:
            if t in seen:
                continue
            stack, comp = [t], []
            while stack:
                x = stack.pop()
                if x in seen:
                    continue
                seen.add(x); comp.append(x)
                stack.extend(adj.get(x, ()))
            comps.append(comp)

        # Ordenar grupos por fecha del primer partido -> letras A, B, C...
        comps.sort(key=lambda c: min(first_ts.get(t, "") for t in c))

        out: list[dict] = []
        for idx, comp in enumerate(comps):
            letter = chr(ord("A") + idx) if idx < 26 else f"G{idx}"
            rows = sorted(
                (info[t] for t in comp),
                key=lambda s: (s["pts"], s["gf"] - s["gc"], s["gf"], s["name"]),
                reverse=True,
            )
            out.append({
                "group": letter,
                "rows": [
                    {
                        "position": i + 1,
                        "team": {"id": r["id"], "name": r["name"],
                                 "code": None, "flag_url": r["flag_url"]},
                        "points": r["pts"], "played": r["pj"],
                        "goal_diff": r["gf"] - r["gc"],
                    }
                    for i, r in enumerate(rows)
                ],
            })
        return out


thesportsdb = TheSportsDBClient()
