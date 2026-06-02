"""
Cliente Sportmonks v3 (football) con rate-limit simple y manejo de errores.

Plan gratuito: solo Superliga (DK) y Scottish Premiership. El Mundial (732)
requiere un plan superior; las llamadas se manejan con gracia si no hay acceso.
Doc: https://docs.sportmonks.com/v3
"""
from __future__ import annotations

import logging
import time
from collections import deque
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class SportmonksError(RuntimeError):
    pass


class SportmonksAccessError(SportmonksError):
    """La suscripción actual no da acceso al recurso pedido."""


class _RateLimiter:
    """Ventana deslizante de 1 hora."""

    def __init__(self, max_per_hour: int) -> None:
        self.max = max_per_hour
        self.calls: deque[float] = deque()

    def acquire(self) -> None:
        now = time.monotonic()
        while self.calls and now - self.calls[0] > 3600:
            self.calls.popleft()
        if len(self.calls) >= self.max:
            wait = 3600 - (now - self.calls[0])
            raise SportmonksError(
                f"Rate limit alcanzado ({self.max}/h). Reintentar en {wait:.0f}s."
            )
        self.calls.append(now)


class SportmonksClient:
    def __init__(self) -> None:
        self.base_url = settings.sportmonks_base_url.rstrip("/")
        self.token = settings.sportmonks_api_token
        self.limiter = _RateLimiter(settings.sportmonks_rate_limit_per_hour)

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict:
        if not self.token:
            raise SportmonksError("Falta SPORTMONKS_API_TOKEN en el entorno.")
        self.limiter.acquire()
        params = dict(params or {})
        params["api_token"] = self.token
        url = f"{self.base_url}/{path.lstrip('/')}"
        try:
            with httpx.Client(timeout=20.0) as client:
                resp = client.get(url, params=params)
        except httpx.HTTPError as exc:  # red/timeout
            raise SportmonksError(f"Error de red Sportmonks: {exc}") from exc

        if resp.status_code in (401, 403):
            raise SportmonksAccessError(
                "Sin acceso al recurso con la suscripción actual."
            )
        if resp.status_code == 429:
            raise SportmonksError("Sportmonks devolvió 429 (rate limit).")
        if resp.status_code >= 400:
            raise SportmonksError(f"Sportmonks {resp.status_code}: {resp.text[:200]}")

        data = resp.json()
        # El plan gratuito a veces responde 200 con mensaje de "sin acceso"
        if isinstance(data, dict) and data.get("message") and "data" not in data:
            raise SportmonksAccessError(data["message"])
        return data

    # --- Endpoints usados por la cartelera ---

    def fixtures_by_date(self, day: str, league_id: int | None = None) -> list[dict]:
        """Partidos de una fecha (YYYY-MM-DD) con equipos y marcador."""
        params = {
            "include": "participants;scores;state;league;group;venue;events.player",
            "per_page": 50,
        }
        data = self._get(f"fixtures/date/{day}", params)
        fixtures = data.get("data", [])
        lid = league_id if league_id is not None else settings.sportmonks_league_id
        if lid:
            fixtures = [f for f in fixtures if f.get("league_id") == lid]
        return fixtures

    def standings_by_season(self, season_id: int) -> list[dict]:
        data = self._get(
            f"standings/seasons/{season_id}",
            {"include": "participant;group;details"},
        )
        return data.get("data", [])

    def teams_by_country(self, country_id: int) -> list[dict]:
        data = self._get(f"teams/countries/{country_id}", {"per_page": 50})
        return data.get("data", [])


# Singleton liviano
sportmonks = SportmonksClient()
