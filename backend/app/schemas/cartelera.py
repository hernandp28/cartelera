"""Esquemas Pydantic para la cartelera 720p."""
from __future__ import annotations

from pydantic import BaseModel, Field


class TeamRef(BaseModel):
    id: int | str
    name: str
    code: str | None = None  # ISO-2 para bandera (ej. "ar")
    flag_url: str | None = None
    logo_url: str | None = None


class MatchEvent(BaseModel):
    minute: int | None = None
    player: str
    team_side: str  # "home" | "away"


class MatchCard(BaseModel):
    id: int | str
    date: str          # YYYY-MM-DD (hora AR)
    kickoff: str       # "HH:MM" hora Argentina
    status: str        # NS | LIVE | HT | FT | AET | PEN | POSTP
    minute: int | None = None        # minuto transcurrido si está en juego
    stage: str | None = None         # "Fase de grupos", "Octavos", ...
    group: str | None = None         # "A".."L"
    venue: str | None = None
    home: TeamRef
    away: TeamRef
    home_score: int | None = None
    away_score: int | None = None
    home_pens: int | None = None     # penales (si se definió por tanda)
    away_pens: int | None = None
    scorers: list[MatchEvent] = Field(default_factory=list)
    red_cards: list[MatchEvent] = Field(default_factory=list)


class GroupRow(BaseModel):
    position: int      # 1..4
    team: TeamRef
    points: int = 0
    played: int = 0
    goal_diff: int = 0


class GroupTable(BaseModel):
    group: str         # "A".."L"
    rows: list[GroupRow]


class UpcomingMatch(BaseModel):
    kickoff: str       # "HH:MM" hora AR
    home: str
    away: str


class CarteleraResponse(BaseModel):
    date: str
    timezone: str
    source: str                       # "live" | "seed"
    is_demo: bool                      # True si los datos son del seed DEMO
    title: str = "Mundial 2026"
    agenda: list[MatchCard]
    groups: list[GroupTable]
    tomorrow: list[UpcomingMatch]
    generated_at: str
