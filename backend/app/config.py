"""Configuración central. Lee variables de entorno desde `.env` (python-dotenv)."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"), env_file_encoding="utf-8", extra="ignore"
    )

    # Proveedor de datos: "apifootball" | "thesportsdb" | "sportmonks" | "seed"
    data_provider: str = "apifootball"

    # API-Football v3 (proveedor principal)
    apifootball_api_key: str = ""
    apifootball_base_url: str = "https://v3.football.api-sports.io"
    apifootball_league_id: int = 1  # FIFA World Cup
    apifootball_season: str = "2026"
    apifootball_friendlies_league_id: int = 10  # Friendlies (selecciones)
    apifootball_include_friendlies: bool = True
    apifootball_rate_limit_per_min: int = 300  # plan Pro

    # TheSportsDB (proveedor principal)
    thesportsdb_api_key: str = "3"  # "3"/"123" = demo limitado; poné tu key premium
    thesportsdb_base_url: str = "https://www.thesportsdb.com/api/v1/json"
    thesportsdb_league_id: int = 4429  # FIFA World Cup (define los grupos)
    thesportsdb_season: str = "2026"
    thesportsdb_rate_limit_per_min: int = 100  # premium = 100/min
    # Amistosos internacionales FIFA (se suman a la agenda; no tienen grupos)
    thesportsdb_friendlies_league_id: int = 4562
    thesportsdb_include_friendlies: bool = True
    # Tope de partidos por día en la agenda (los EN VIVO tienen prioridad)
    agenda_max_matches: int = 10

    # Sportmonks (proveedor alternativo)
    sportmonks_api_token: str = ""
    sportmonks_base_url: str = "https://api.sportmonks.com/v3/football"
    sportmonks_league_id: int = 732
    sportmonks_rate_limit_per_hour: int = 180

    # Visualización
    display_timezone: str = "America/Argentina/Buenos_Aires"
    cartelera_source: str = "auto"  # auto | seed | live

    # Base de datos
    database_url: str = "postgresql+psycopg://mundial:mundial@localhost:5432/mundial2026"

    # Redis / Celery
    redis_url: str = "redis://localhost:6379/0"

    # Noticias
    newsapi_key: str = ""
    gdelt_enabled: bool = True

    # App
    api_cors_origins: str = "http://localhost:3000"
    log_level: str = "INFO"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.api_cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
