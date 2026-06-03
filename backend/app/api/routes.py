"""Router principal con todos los endpoints REST (documentados en OpenAPI)."""
from __future__ import annotations

from datetime import date as date_cls

from fastapi import APIRouter, HTTPException, Query

from app.schemas.cartelera import CarteleraResponse
from app.schemas.prediction import Prediction
from app.seed import worldcup2026 as seed
from app.services import alerts_service, news_service, prediction_service
from app.services.cartelera_service import build_cartelera, get_lineups

router = APIRouter()


def _today() -> str:
    return date_cls.today().isoformat()


def _find_match(match_id: str) -> dict:
    for m in seed.all_matches():
        if str(m["id"]) == str(match_id):
            return m
    raise HTTPException(status_code=404, detail=f"Partido {match_id} no encontrado.")


# ─────────────────────────── Cartelera ───────────────────────────
@router.get("/cartelera", response_model=CarteleraResponse, tags=["cartelera"])
def get_cartelera(
    date: str | None = Query(None, description="Fecha YYYY-MM-DD (hora AR). Default: hoy.")
):
    """Payload completo de la pantalla 720p para una fecha."""
    return build_cartelera(date or _today())


# ─────────────────────────── Partidos ───────────────────────────
@router.get("/matches", tags=["matches"])
def list_matches(
    date: str | None = Query(None, description="Filtra por fecha YYYY-MM-DD"),
    group: str | None = Query(None, description="Filtra por grupo A–L"),
):
    matches = seed.all_matches()
    if date:
        matches = [m for m in matches if m["date"] == date]
    if group:
        matches = [m for m in matches if m["group"] == group.upper()]
    return {"count": len(matches), "data": matches}


@router.get("/matches/{match_id}", tags=["matches"])
def get_match(match_id: str):
    return _find_match(match_id)


@router.get("/fixtures/{fixture_id}/lineups", tags=["matches"])
def fixture_lineups(fixture_id: str):
    """Formación, DT, titulares y suplentes de ambos equipos."""
    return get_lineups(fixture_id)


# ─────────────────────────── Selecciones ───────────────────────────
@router.get("/teams", tags=["teams"])
def list_teams():
    teams = []
    for letter, members in seed.GROUPS.items():
        for name, code in members:
            teams.append({
                "id": f"t-{code}", "name": name, "code": code,
                "group": letter, "flag_url": seed.flag_url(code),
            })
    return {"count": len(teams), "data": teams}


@router.get("/teams/{team_id}", tags=["teams"])
def get_team(team_id: str):
    for letter, members in seed.GROUPS.items():
        for name, code in members:
            if f"t-{code}" == team_id or code == team_id:
                matches = [
                    m for m in seed.all_matches()
                    if m["home"]["code"] == code or m["away"]["code"] == code
                ]
                return {
                    "id": f"t-{code}", "name": name, "code": code, "group": letter,
                    "flag_url": seed.flag_url(code),
                    "manager": None, "fifa_rank": None,  # pendiente de fuente
                    "matches": matches,
                    "note": "Plantel/ranking/lesiones se completan al conectar la API.",
                }
    raise HTTPException(status_code=404, detail=f"Selección {team_id} no encontrada.")


# ─────────────────────────── Predicciones ───────────────────────────
@router.get("/predictions/{match_id}", response_model=Prediction, tags=["predictions"])
def get_prediction(match_id: str):
    return prediction_service.predict(_find_match(match_id))


@router.post(
    "/predictions/recalculate/{match_id}",
    response_model=Prediction,
    tags=["predictions"],
)
def recalculate_prediction(match_id: str):
    """Recalcula y (en el futuro) persiste la predicción con versión y fecha."""
    return prediction_service.predict(_find_match(match_id))


# ─────────────────────────── Noticias ───────────────────────────
@router.get("/news/team/{team_id}", tags=["news"])
def get_team_news(team_id: str, limit: int = 10):
    return news_service.news_for_team(team_id, limit)


# ─────────────────────────── Alertas ───────────────────────────
@router.get("/alerts", tags=["alerts"])
def get_alerts():
    return {"data": alerts_service.current_alerts()}
