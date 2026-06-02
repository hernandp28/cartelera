"""
Dataset SEMILLA del Mundial 2026 — *DEMO*.

⚠️  IMPORTANTE: la composición de grupos y el fixture de abajo son una
    REPRESENTACIÓN DE MUESTRA para que la cartelera renderice con el formato
    real (12 grupos, 48 selecciones). NO son el sorteo/calendario oficial de
    la FIFA. En la UI se muestra un badge "DEMO".

    Para usar datos reales:
      • con un plan Sportmonks que incluya la liga 732, poné CARTELERA_SOURCE=live
      • o reemplazá GROUPS/horarios de este archivo por los oficiales.

Genera de forma determinística:
    • 12 grupos (A–L) con 4 selecciones cada uno (banderas vía ISO-2).
    • 72 partidos de fase de grupos (round-robin), con horario en hora Argentina.
"""
from __future__ import annotations

from datetime import date, timedelta

# (Nombre, ISO-2 para flagcdn).  gb-eng/gb-wls/gb-sct = Inglaterra/Gales/Escocia
GROUPS: dict[str, list[tuple[str, str]]] = {
    "A": [("México", "mx"), ("Croacia", "hr"), ("Ecuador", "ec"), ("Túnez", "tn")],
    "B": [("Canadá", "ca"), ("Bélgica", "be"), ("Marruecos", "ma"), ("Perú", "pe")],
    "C": [("Argentina", "ar"), ("Polonia", "pl"), ("Japón", "jp"), ("Ghana", "gh")],
    "D": [("Estados Unidos", "us"), ("Países Bajos", "nl"), ("Senegal", "sn"), ("Paraguay", "py")],
    "E": [("España", "es"), ("Serbia", "rs"), ("Corea del Sur", "kr"), ("Costa Rica", "cr")],
    "F": [("Francia", "fr"), ("Suiza", "ch"), ("Nigeria", "ng"), ("Panamá", "pa")],
    "G": [("Inglaterra", "gb-eng"), ("Dinamarca", "dk"), ("Australia", "au"), ("Egipto", "eg")],
    "H": [("Alemania", "de"), ("Uruguay", "uy"), ("Arabia Saudita", "sa"), ("Nueva Zelanda", "nz")],
    "I": [("Brasil", "br"), ("Suecia", "se"), ("Camerún", "cm"), ("Catar", "qa")],
    "J": [("Portugal", "pt"), ("Austria", "at"), ("Costa de Marfil", "ci"), ("Irán", "ir")],
    "K": [("Colombia", "co"), ("Noruega", "no"), ("Argelia", "dz"), ("Italia", "it")],
    "L": [("Chile", "cl"), ("Turquía", "tr"), ("Gales", "gb-wls"), ("Escocia", "gb-sct")],
}

# Sedes de muestra (host: USA/Canadá/México)
VENUES = [
    "MetLife Stadium, Nueva York", "SoFi Stadium, Los Ángeles",
    "Estadio Azteca, Ciudad de México", "BMO Field, Toronto",
    "AT&T Stadium, Dallas", "Mercedes-Benz Stadium, Atlanta",
    "Lumen Field, Seattle", "Hard Rock Stadium, Miami",
]

# Round-robin balanceado para 4 equipos (índices 0..3)
_ROUNDS = [
    [(0, 1), (2, 3)],   # Jornada 1
    [(0, 2), (3, 1)],   # Jornada 2
    [(3, 0), (1, 2)],   # Jornada 3
]

# Horarios (hora Argentina) — 4 franjas por día
_SLOTS = ["13:00", "16:00", "19:00", "22:00"]

GROUP_STAGE_START = date(2026, 6, 11)


def flag_url(code: str) -> str:
    return f"https://flagcdn.com/w160/{code}.png"


def _team_ref(name: str, code: str) -> dict:
    return {"id": f"t-{code}", "name": name, "code": code, "flag_url": flag_url(code)}


def build_matches() -> list[dict]:
    """Construye los 72 partidos de fase de grupos de forma determinística."""
    raw: list[dict] = []
    for letter, teams in GROUPS.items():
        for md, pairs in enumerate(_ROUNDS, start=1):
            for hi, ai in pairs:
                home_n, home_c = teams[hi]
                away_n, away_c = teams[ai]
                raw.append({
                    "group": letter,
                    "matchday": md,
                    "home": _team_ref(home_n, home_c),
                    "away": _team_ref(away_n, away_c),
                })

    # Ordena por jornada para agrupar el calendario, luego por grupo
    raw.sort(key=lambda m: (m["matchday"], m["group"]))

    # Asigna fecha/horario: 8 partidos por día (4 franjas × 2 canchas), <=10/día
    matches: list[dict] = []
    per_day = 8
    for idx, m in enumerate(raw):
        day_offset = idx // per_day
        slot_idx = (idx % per_day) // 2
        match_date = GROUP_STAGE_START + timedelta(days=day_offset)
        matches.append({
            "id": f"wc-{idx + 1:03d}",
            "date": match_date.isoformat(),
            "kickoff": _SLOTS[slot_idx],
            "status": "NS",
            "minute": None,
            "stage": "Fase de grupos",
            "group": m["group"],
            "venue": VENUES[idx % len(VENUES)],
            "home": m["home"],
            "away": m["away"],
            "home_score": None,
            "away_score": None,
            "home_pens": None,
            "away_pens": None,
            "scorers": [],
            "red_cards": [],
        })
    return matches


# Cache en memoria (determinístico, barato de recalcular)
_MATCHES_CACHE: list[dict] | None = None


def all_matches() -> list[dict]:
    global _MATCHES_CACHE
    if _MATCHES_CACHE is None:
        _MATCHES_CACHE = build_matches()
    return _MATCHES_CACHE


def matches_on(day: str) -> list[dict]:
    return [m for m in all_matches() if m["date"] == day]


def group_tables() -> list[dict]:
    """
    Tabla de posiciones por grupo calculada a partir de partidos finalizados.
    Pre-torneo todo en cero; si hay resultados cargados, se recalcula.
    """
    tables: list[dict] = []
    finished = {"FT", "AET", "PEN"}
    matches = all_matches()
    for letter, teams in GROUPS.items():
        stats = {
            code: {"name": name, "code": code, "pts": 0, "pj": 0, "gf": 0, "gc": 0}
            for name, code in teams
        }
        for m in matches:
            if m["group"] != letter or m["status"] not in finished:
                continue
            hc, ac = m["home"]["code"], m["away"]["code"]
            hs, as_ = m["home_score"] or 0, m["away_score"] or 0
            for c in (hc, ac):
                if c in stats:
                    stats[c]["pj"] += 1
            stats[hc]["gf"] += hs; stats[hc]["gc"] += as_
            stats[ac]["gf"] += as_; stats[ac]["gc"] += hs
            if hs > as_:
                stats[hc]["pts"] += 3
            elif as_ > hs:
                stats[ac]["pts"] += 3
            else:
                stats[hc]["pts"] += 1; stats[ac]["pts"] += 1

        rows = sorted(
            stats.values(),
            key=lambda s: (s["pts"], s["gf"] - s["gc"], s["gf"]),
            reverse=True,
        )
        tables.append({
            "group": letter,
            "rows": [
                {
                    "position": i + 1,
                    "team": _team_ref(r["name"], r["code"]),
                    "points": r["pts"],
                    "played": r["pj"],
                    "goal_diff": r["gf"] - r["gc"],
                }
                for i, r in enumerate(rows)
            ],
        })
    return tables
