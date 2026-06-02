"""Punto de entrada FastAPI — Mundial 2026."""
from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import settings

logging.basicConfig(level=settings.log_level)

app = FastAPI(
    title="Mundial 2026 — API de Cartelera y Predicción",
    description=(
        "Backend de la cartelera 720p y el motor predictivo del Mundial 2026.\n\n"
        "⚠️ El plan gratuito de Sportmonks no incluye la liga del Mundial (732): "
        "la cartelera usa un dataset DEMO hasta tener acceso o configurar datos reales."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/health", tags=["meta"])
def health():
    return {
        "status": "ok",
        "data_provider": settings.data_provider,
        "cartelera_source": settings.cartelera_source,
        "apifootball_league_id": settings.apifootball_league_id,
        "apifootball_season": settings.apifootball_season,
        "apifootball_key_set": bool(settings.apifootball_api_key),
    }
