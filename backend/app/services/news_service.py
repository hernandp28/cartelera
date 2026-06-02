"""
Motor de noticias — STUB inicial.

Define la interfaz (buscar por equipo, clasificar impacto/confiabilidad,
detectar entidades) sin llamadas externas todavía. Cuando se configuren
NEWSAPI_KEY / GDELT, se completa la ingesta real y el guardado en
news_articles + embeddings pgvector.

⚠️ Mientras no haya fuente configurada, devuelve lista vacía (NO inventa
   noticias) en cumplimiento de la regla "no inventar datos".
"""
from __future__ import annotations

from app.config import settings


def news_for_team(team_id: str | int, limit: int = 10) -> dict:
    configured = bool(settings.newsapi_key) or settings.gdelt_enabled
    return {
        "team_id": team_id,
        "configured": configured,
        "articles": [],  # se llena cuando la ingesta real esté activa
        "note": (
            "Motor de noticias en modo stub. Configurá NEWSAPI_KEY o GDELT para "
            "ingesta real. No se inventan noticias."
        ),
    }


def daily_summary(team_id: str | int) -> dict:
    return {
        "team_id": team_id,
        "summary": None,
        "note": "Resumen diario disponible cuando la ingesta de noticias esté activa.",
    }
