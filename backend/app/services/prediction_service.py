"""
Motor predictivo — implementación DUMMY reemplazable.

Hoy: modelo determinístico basado en un "rating" semilla por selección + ventaja
de localía, que produce probabilidades 1X2, goles esperados (Poisson), resultado
probable, confianza y factores. La interfaz `predict(match)` es estable: cuando se
entrene el modelo real (Elo + Poisson + LightGBM + capa contextual) se reemplaza
el cuerpo sin tocar los endpoints.

Ver roadmap en app/ml/README.md
"""
from __future__ import annotations

import hashlib
import math
from datetime import datetime
from zoneinfo import ZoneInfo

from app.config import settings

MODEL_VERSION = "dummy-0.1.0"
AR_TZ = ZoneInfo(settings.display_timezone)

# Rating de muestra (0-100) para selecciones frecuentes; default 70.
_BASE_RATING = {
    "ar": 92, "br": 90, "fr": 91, "es": 88, "gb-eng": 87, "de": 86, "pt": 86,
    "nl": 84, "be": 82, "hr": 81, "uy": 80, "co": 79, "mx": 77, "us": 76,
    "ma": 78, "sn": 76, "jp": 75, "kr": 73, "ch": 78, "dk": 77, "rs": 74,
}


def _rating(code: str | None) -> float:
    if not code:
        return 70.0
    return float(_BASE_RATING.get(code.lower(), 70))


def _stable_jitter(seed: str) -> float:
    """Ruido determinístico en [-3, 3] a partir de un string."""
    h = int(hashlib.sha256(seed.encode()).hexdigest(), 16)
    return (h % 601) / 100.0 - 3.0


def _poisson_topscore(lh: float, la: float) -> tuple[int, int]:
    best, bx, by = -1.0, 0, 0
    for x in range(6):
        for y in range(6):
            p = (
                math.exp(-lh) * lh**x / math.factorial(x)
                * math.exp(-la) * la**y / math.factorial(y)
            )
            if p > best:
                best, bx, by = p, x, y
    return bx, by


def predict(match: dict) -> dict:
    home, away = match["home"], match["away"]
    rh = _rating(home.get("code")) + 4.0  # ventaja de localía/sede
    ra = _rating(away.get("code"))
    rh += _stable_jitter(f"{match['id']}-h")
    ra += _stable_jitter(f"{match['id']}-a")

    diff = (rh - ra) / 8.0
    p_home = 1 / (1 + math.exp(-diff))
    p_away = 1 / (1 + math.exp(diff))
    p_draw = 0.26 * math.exp(-abs(diff) / 2)
    s = p_home + p_away + p_draw
    p_home, p_draw, p_away = p_home / s, p_draw / s, p_away / s

    xg_home = round(1.15 + max(diff, 0) * 0.55 + 0.15, 2)
    xg_away = round(1.05 + max(-diff, 0) * 0.55, 2)
    sh, sa = _poisson_topscore(xg_home, xg_away)

    confidence = round(min(0.92, 0.45 + abs(p_home - p_away) * 0.6), 2)

    factors = [
        {
            "label": f"Rating base superior ({home['name']})" if rh >= ra
            else f"Rating base superior ({away['name']})",
            "impact": "positivo",
            "weight": round(min(abs(rh - ra) / 25, 1.0), 2),
            "side": "home" if rh >= ra else "away",
        },
        {"label": "Ventaja de sede/localía", "impact": "positivo",
         "weight": 0.25, "side": "home"},
        {"label": "Forma reciente (placeholder — pendiente de datos)",
         "impact": "neutro", "weight": 0.1, "side": "match"},
    ]

    fav = home["name"] if p_home >= p_away else away["name"]
    explanation = (
        f"{fav} llega como favorito según el rating base del modelo y la ventaja "
        f"de sede. Probabilidades: {home['name']} {p_home*100:.0f}%, empate "
        f"{p_draw*100:.0f}%, {away['name']} {p_away*100:.0f}%. Goles esperados "
        f"{xg_home}–{xg_away}. Confianza {confidence*100:.0f}%. "
        "Modelo DUMMY: ajustar con estadística real, lesiones y noticias."
    )

    return {
        "match_id": match["id"],
        "model_version": MODEL_VERSION,
        "prob_home": round(p_home, 4),
        "prob_draw": round(p_draw, 4),
        "prob_away": round(p_away, 4),
        "xg_home": xg_home,
        "xg_away": xg_away,
        "likely_score": f"{sh}-{sa}",
        "confidence": confidence,
        "factors": factors,
        "explanation": explanation,
        "generated_at": datetime.now(AR_TZ).isoformat(),
    }
