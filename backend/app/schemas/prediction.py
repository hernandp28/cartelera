"""Esquemas de predicción (modelo dummy reemplazable)."""
from __future__ import annotations

from pydantic import BaseModel, Field


class PredictionFactor(BaseModel):
    label: str
    impact: str            # "positivo" | "negativo" | "neutro"
    weight: float          # 0..1
    side: str              # "home" | "away" | "match"


class Prediction(BaseModel):
    match_id: int | str
    model_version: str
    prob_home: float
    prob_draw: float
    prob_away: float
    xg_home: float
    xg_away: float
    likely_score: str
    confidence: float                      # 0..1
    factors: list[PredictionFactor] = Field(default_factory=list)
    explanation: str
    generated_at: str
    disclaimer: str = (
        "Predicción probabilística con fines analíticos. No es una certeza "
        "ni una recomendación de apuesta."
    )
