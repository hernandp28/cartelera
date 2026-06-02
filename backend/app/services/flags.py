"""
Mapa de nombre de selección (TheSportsDB, en inglés) -> código ISO-2 para banderas
(flagcdn). Los escudos de TheSportsDB son crestas/federaciones; acá usamos la
BANDERA del país. Si un equipo no está en el mapa (p. ej. ganadores de repechaje
con nombre provisional), se cae al escudo original.
"""
from __future__ import annotations

_NAME_TO_ISO2 = {
    "argentina": "ar", "algeria": "dz", "australia": "au", "austria": "at",
    "belgium": "be", "bosnia-herzegovina": "ba", "bosnia and herzegovina": "ba",
    "bosnia & herzegovina": "ba",
    "brazil": "br", "canada": "ca", "cape verde": "cv", "cape verde islands": "cv",
    "colombia": "co",
    "croatia": "hr", "curaçao": "cw", "curacao": "cw", "czech republic": "cz",
    "czechia": "cz", "dr congo": "cd", "democratic republic of congo": "cd",
    "congo dr": "cd",
    "ecuador": "ec", "egypt": "eg", "england": "gb-eng", "france": "fr",
    "germany": "de", "ghana": "gh", "haiti": "ht", "iran": "ir", "iraq": "iq",
    "ivory coast": "ci", "côte d'ivoire": "ci", "cote d'ivoire": "ci",
    "japan": "jp", "jordan": "jo", "mexico": "mx", "morocco": "ma",
    "netherlands": "nl", "new zealand": "nz", "norway": "no", "panama": "pa",
    "paraguay": "py", "portugal": "pt", "qatar": "qa", "saudi arabia": "sa",
    "scotland": "gb-sct", "senegal": "sn", "south africa": "za",
    "south korea": "kr", "korea republic": "kr", "spain": "es", "sweden": "se",
    "switzerland": "ch", "tunisia": "tn", "turkey": "tr", "türkiye": "tr",
    "uruguay": "uy", "usa": "us", "united states": "us", "uzbekistan": "uz",
    "wales": "gb-wls",
}


# Nombre en inglés (TheSportsDB) -> castellano. Sin match => se deja el original.
_NAME_ES = {
    "argentina": "Argentina", "algeria": "Argelia", "australia": "Australia",
    "austria": "Austria", "belgium": "Bélgica", "bosnia-herzegovina": "Bosnia",
    "bosnia and herzegovina": "Bosnia", "brazil": "Brasil", "bulgaria": "Bulgaria",
    "bosnia & herzegovina": "Bosnia",
    "canada": "Canadá", "cape verde": "Cabo Verde",
    "cape verde islands": "Cabo Verde", "colombia": "Colombia",
    "costa rica": "Costa Rica", "croatia": "Croacia", "curaçao": "Curazao",
    "curacao": "Curazao", "czech republic": "Rep. Checa", "czechia": "Rep. Checa",
    "dr congo": "RD Congo", "democratic republic of congo": "RD Congo",
    "congo dr": "RD Congo",
    "denmark": "Dinamarca", "ecuador": "Ecuador", "egypt": "Egipto",
    "england": "Inglaterra", "finland": "Finlandia", "france": "Francia",
    "georgia": "Georgia", "germany": "Alemania", "ghana": "Ghana",
    "greece": "Grecia", "haiti": "Haití", "hungary": "Hungría", "iran": "Irán",
    "iraq": "Irak", "ireland": "Irlanda", "ivory coast": "Costa de Marfil",
    "côte d'ivoire": "Costa de Marfil", "cote d'ivoire": "Costa de Marfil",
    "japan": "Japón", "jordan": "Jordania", "madagascar": "Madagascar",
    "malta": "Malta", "mexico": "México", "montenegro": "Montenegro",
    "morocco": "Marruecos", "netherlands": "Países Bajos",
    "new zealand": "Nueva Zelanda", "nigeria": "Nigeria",
    "north macedonia": "Macedonia del Norte", "norway": "Noruega",
    "panama": "Panamá", "paraguay": "Paraguay", "peru": "Perú",
    "poland": "Polonia", "portugal": "Portugal", "qatar": "Catar",
    "romania": "Rumania", "russia": "Rusia", "saudi arabia": "Arabia Saudita",
    "scotland": "Escocia", "senegal": "Senegal", "serbia": "Serbia",
    "slovakia": "Eslovaquia", "slovenia": "Eslovenia", "south africa": "Sudáfrica",
    "south korea": "Corea del Sur", "korea republic": "Corea del Sur",
    "spain": "España", "sweden": "Suecia", "switzerland": "Suiza",
    "tajikistan": "Tayikistán", "palestine": "Palestina", "tunisia": "Túnez",
    "turkey": "Turquía", "türkiye": "Turquía", "ukraine": "Ucrania",
    "uruguay": "Uruguay", "usa": "Estados Unidos", "united states": "Estados Unidos",
    "uzbekistan": "Uzbekistán", "wales": "Gales",
}


def iso2_for(name: str | None) -> str | None:
    if not name:
        return None
    return _NAME_TO_ISO2.get(name.strip().lower())


def es_name(name: str | None) -> str:
    """Nombre del país en castellano; si no está mapeado, devuelve el original."""
    if not name:
        return "—"
    return _NAME_ES.get(name.strip().lower(), name)


def flag_for(name: str | None, fallback: str | None = None) -> str | None:
    """URL de bandera (flagcdn) por nombre de país; fallback al escudo si no hay."""
    code = iso2_for(name)
    if code:
        return f"https://flagcdn.com/w160/{code}.png"
    return fallback
