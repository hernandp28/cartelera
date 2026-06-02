"""
Modelos SQLAlchemy iniciales — las 15 tablas del sistema.

Cubre: teams, players, matches, team_stats, player_status, injuries,
suspensions, news_articles, news_entities, predictions, prediction_factors,
model_versions, sources, odds_snapshots, alerts.

Las noticias usan pgvector (Vector) para embeddings; si la extensión no está,
las migraciones deben crear `CREATE EXTENSION vector;` primero.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

try:  # embeddings opcionales
    from pgvector.sqlalchemy import Vector
    _EMB = Vector(384)
except Exception:  # pragma: no cover
    _EMB = JSON


class Team(Base):
    __tablename__ = "teams"
    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[str | None] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(120))
    code: Mapped[str | None] = mapped_column(String(8))
    group: Mapped[str | None] = mapped_column(String(2))
    fifa_rank: Mapped[int | None]
    elo: Mapped[float | None]
    manager: Mapped[str | None] = mapped_column(String(120))
    logo_url: Mapped[str | None] = mapped_column(String(255))
    players: Mapped[list["Player"]] = relationship(back_populates="team")


class Player(Base):
    __tablename__ = "players"
    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[str | None] = mapped_column(String(64), index=True)
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"))
    name: Mapped[str] = mapped_column(String(120))
    position: Mapped[str | None] = mapped_column(String(40))
    number: Mapped[int | None]
    team: Mapped["Team"] = relationship(back_populates="players")


class Match(Base):
    __tablename__ = "matches"
    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[str | None] = mapped_column(String(64), index=True)
    home_team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"))
    away_team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"))
    kickoff_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    stage: Mapped[str | None] = mapped_column(String(60))
    group: Mapped[str | None] = mapped_column(String(2))
    venue: Mapped[str | None] = mapped_column(String(160))
    status: Mapped[str] = mapped_column(String(16), default="NS")
    home_score: Mapped[int | None]
    away_score: Mapped[int | None]
    home_pens: Mapped[int | None]
    away_pens: Mapped[int | None]


class TeamStats(Base):
    __tablename__ = "team_stats"
    id: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    window: Mapped[str] = mapped_column(String(16))  # last5/last10/last20
    played: Mapped[int] = mapped_column(default=0)
    wins: Mapped[int] = mapped_column(default=0)
    draws: Mapped[int] = mapped_column(default=0)
    losses: Mapped[int] = mapped_column(default=0)
    gf: Mapped[int] = mapped_column(default=0)
    ga: Mapped[int] = mapped_column(default=0)
    xg: Mapped[float | None]
    xga: Mapped[float | None]


class PlayerStatus(Base):
    __tablename__ = "player_status"
    id: Mapped[int] = mapped_column(primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"))
    status: Mapped[str] = mapped_column(String(40))  # disponible/duda/baja
    detail: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Injury(Base):
    __tablename__ = "injuries"
    id: Mapped[int] = mapped_column(primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"))
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"))
    description: Mapped[str | None] = mapped_column(Text)
    expected_return: Mapped[str | None] = mapped_column(String(60))
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"))


class Suspension(Base):
    __tablename__ = "suspensions"
    id: Mapped[int] = mapped_column(primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"))
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"))
    reason: Mapped[str | None] = mapped_column(String(160))
    matches_out: Mapped[int | None]


class Source(Base):
    __tablename__ = "sources"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    url: Mapped[str | None] = mapped_column(String(255))
    country: Mapped[str | None] = mapped_column(String(60))
    language: Mapped[str | None] = mapped_column(String(8))
    reliability: Mapped[str | None] = mapped_column(String(16))  # alta/media/baja


class NewsArticle(Base):
    __tablename__ = "news_articles"
    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"))
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"))
    title: Mapped[str] = mapped_column(String(400))
    body: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(String(500))
    country: Mapped[str | None] = mapped_column(String(60))
    language: Mapped[str | None] = mapped_column(String(8))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sentiment: Mapped[float | None]
    impact: Mapped[str | None] = mapped_column(String(8))   # alto/medio/bajo
    veracity: Mapped[str | None] = mapped_column(String(16))  # confirmado/probable/rumor
    embedding = mapped_column(_EMB, nullable=True)


class NewsEntity(Base):
    __tablename__ = "news_entities"
    id: Mapped[int] = mapped_column(primary_key=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("news_articles.id"))
    entity_type: Mapped[str] = mapped_column(String(40))  # jugador/equipo/DT/lesion...
    value: Mapped[str] = mapped_column(String(200))


class ModelVersion(Base):
    __tablename__ = "model_versions"
    id: Mapped[int] = mapped_column(primary_key=True)
    version: Mapped[str] = mapped_column(String(40), unique=True)
    algorithm: Mapped[str | None] = mapped_column(String(80))
    params: Mapped[dict | None] = mapped_column(JSON)
    metrics: Mapped[dict | None] = mapped_column(JSON)  # accuracy/logloss/brier
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Prediction(Base):
    __tablename__ = "predictions"
    id: Mapped[int] = mapped_column(primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"))
    model_version: Mapped[str] = mapped_column(String(40))
    prob_home: Mapped[float]
    prob_draw: Mapped[float]
    prob_away: Mapped[float]
    xg_home: Mapped[float | None]
    xg_away: Mapped[float | None]
    likely_score: Mapped[str | None] = mapped_column(String(12))
    confidence: Mapped[float | None]
    explanation: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class PredictionFactor(Base):
    __tablename__ = "prediction_factors"
    id: Mapped[int] = mapped_column(primary_key=True)
    prediction_id: Mapped[int] = mapped_column(ForeignKey("predictions.id"))
    label: Mapped[str] = mapped_column(String(200))
    impact: Mapped[str] = mapped_column(String(12))
    weight: Mapped[float]
    side: Mapped[str] = mapped_column(String(8))


class OddsSnapshot(Base):
    __tablename__ = "odds_snapshots"
    id: Mapped[int] = mapped_column(primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"))
    bookmaker: Mapped[str | None] = mapped_column(String(80))
    odd_home: Mapped[float | None]
    odd_draw: Mapped[float | None]
    odd_away: Mapped[float | None]
    captured_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Alert(Base):
    __tablename__ = "alerts"
    id: Mapped[int] = mapped_column(primary_key=True)
    level: Mapped[str] = mapped_column(String(12))  # info/medium/critical
    title: Mapped[str] = mapped_column(String(200))
    detail: Mapped[str | None] = mapped_column(Text)
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"))
    match_id: Mapped[int | None] = mapped_column(ForeignKey("matches.id"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
