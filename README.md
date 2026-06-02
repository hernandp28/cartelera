# Mundial 2026 — Cartelera & Motor Predictivo

Plataforma para el **Mundial de Fútbol 2026**: una **cartelera 720p** estilo
*sports analytics* (header + agenda del día + tabla de posiciones por grupo en
carrusel + “juegan mañana”) sobre un backend FastAPI con motor predictivo y
motor de noticias.

> Inspiración de formato: promiedos, pero con layout propio para pantalla 1280×720.

---

## Datos: API-Football v3 (proveedor principal)

La cartelera usa **API-Football v3** para el Mundial 2026
(**liga `1`, temporada `2026`**) y los amistosos de selecciones (**liga `10`**).
Trae fixtures, marcadores, sedes, **standings con los 12 grupos nativos** y
**goleadores/expulsados (también en vivo)** con minuto transcurrido.

### 👉 Paso a paso: poner tu API key Pro

1. Abrí el archivo **`.env`** en la raíz del proyecto.
2. Completá tu key Pro de API-Football:
   ```env
   APIFOOTBALL_API_KEY=TU_KEY_ACA
   ```
3. Asegurate de que esté `DATA_PROVIDER=apifootball` (ya viene así).
4. **Reiniciá el backend**:
   ```bash
   # Local:  Ctrl+C y de nuevo  uvicorn app.main:app --reload
   # Docker: docker compose restart backend
   ```
5. Verificá: abrí http://localhost:8000/health → debe decir
   `"apifootball_key_set": true`.

Acceso directo (api-sports.io): la key va en el header `x-apisports-key`.
Base `https://v3.football.api-sports.io`. Los horarios se piden con
`timezone=America/Argentina/Buenos_Aires`, ya en hora Argentina.

### Grupos y goleadores

- **Grupos:** `/standings?league=1&season=2026` devuelve los 12 grupos nativos
  (A–L). La API agrega además una tabla "Ranking of third-placed teams" que se
  excluye del carrusel. La letra de grupo de cada partido del Mundial se toma de
  standings (el fixture trae "Group Stage - N", sin letra).
- **Goleadores/expulsados:** `/fixtures/events?fixture=ID` (tipo Goal/Card,
  minuto, autor, penal `(p)`, en contra `(ec)`), disponible también en vivo.
- **En vivo:** `/fixtures?live=all` refresca minuto y marcador.
- Lógica en `backend/app/services/apifootball.py`. Nombres en castellano y
  banderas (flagcdn) vía `backend/app/services/flags.py`.

### Fallback DEMO (regla “no inventar datos”)

Si el proveedor no responde o un día no tiene partidos, la cartelera cae a un
**dataset SEMILLA marcado `DEMO`** (`backend/app/seed/worldcup2026.py`) y lo
señala con un badge **DEMO** en pantalla. Nada se presenta como oficial si no
viene de la API. Controlás esto con `CARTELERA_SOURCE` (`auto`|`live`|`seed`).

---

## Arquitectura

```
Sportmonks ─┐
GDELT/News ─┼─► FastAPI (services) ─► PostgreSQL + pgvector
Seed DEMO ──┘        │                      ▲
                     ▼                  Celery + Redis
              REST /api/...                 (jobs)
                     │
                     ▼
            Next.js — Cartelera 1280×720
      [Header] [Agenda] [Grupos carrusel] [Juegan mañana]
```

- **Backend (`/backend`)** — FastAPI. `services/` lógica determinística (cliente
  Sportmonks con rate-limit, armado de cartelera con timezone AR, predictor,
  noticias, alertas). `db/models.py` las 15 tablas. `ml/`, `news/`, `tasks/`
  andamiados (ver sus README/stubs).
- **Frontend (`/frontend`)** — Next.js 14 + TS + Tailwind. La pantalla se escala
  a 1280×720 y encaja en cualquier ventana sin deformar.
- **Infra** — `docker-compose.yml` (Postgres+pgvector, Redis, backend, worker,
  frontend).

Todos los horarios se muestran en **hora Argentina**
(`America/Argentina/Buenos_Aires`).

---

## Puesta en marcha

### Opción A — Docker (todo junto)

```bash
cp .env.example .env        # ya viene con el token cargado
docker compose up --build
```

- Cartelera: http://localhost:3000
- API + Swagger: http://localhost:8000/docs

### Opción B — Local (sin Docker, rápido para ver la cartelera)

**Backend:**
```bash
cd backend
python -m venv .venv && . .venv/Scripts/activate    # Windows PowerShell
pip install -r requirements.txt
uvicorn app.main:app --reload                       # :8000
```

**Frontend:**
```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev                                         # :3000
```

La cartelera levanta aunque **no haya Postgres**: los endpoints de cartelera
sirven desde el seed + overlay en vivo. La BD se usa para el resto del sistema.

> Como hoy (01/06/2026) el torneo aún no empezó, la agenda de hoy estará vacía.
> Usá **Siguiente** o el selector de fecha para ir al **11/06/2026** y ver la
> jornada inaugural (datos DEMO).

---

## Endpoints principales

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/cartelera?date=YYYY-MM-DD` | Payload completo de la pantalla |
| GET | `/api/matches` | Lista de partidos (filtros `date`, `group`) |
| GET | `/api/matches/{id}` | Detalle de partido |
| GET | `/api/teams` | Selecciones |
| GET | `/api/teams/{id}` | Detalle de selección |
| GET | `/api/predictions/{match_id}` | Predicción 1X2 + xG + factores |
| POST | `/api/predictions/recalculate/{match_id}` | Recalcula predicción |
| GET | `/api/news/team/{team_id}` | Noticias por selección (stub) |
| GET | `/api/alerts` | Alertas |
| GET | `/health` | Healthcheck |

Documentación interactiva: **http://localhost:8000/docs** (OpenAPI/Swagger).

---

## La cartelera (formato pedido)

- **Header** — Título *“Mundial 2026”* (izq.), botones **Anterior / Hoy /
  Siguiente** + selector de fecha (centro), **logo** del Mundial (der.).
- **Agenda del día** — tarjetas de cada partido; el tamaño se ajusta a la
  cantidad (máx. 10/día). Cada tarjeta: equipos + banderas, resultado, minuto en
  juego, goleadores, expulsados y, si se definió por penales, el marcador de la
  tanda entre paréntesis.
- **Grupos** — 12 grupos en carrusel: 6 a lo ancho durante 10 s, luego los otros
  6, en ciclo. Columnas: **# / País / Pts / PJ / DG**.
- **Juegan mañana** — `HH:MM — Equipo1 vs Equipo2`.

---

## Estado de implementación (honesto)

| Módulo | Estado |
|--------|--------|
| Cartelera 720p (front + API) | ✅ Funcional |
| Integración **API-Football v3** (Mundial liga 1/2026) | ✅ Funcional (datos reales) |
| Integración Sportmonks (proveedor alternativo) | ✅ Funcional |
| Seed DEMO Mundial (fallback) | ✅ Funcional |
| Predicción 1X2 + xG + factores | ✅ Modelo **dummy** reemplazable |
| Endpoints matches/teams/predictions/alerts | ✅ Funcional |
| Modelos de BD (15 tablas + pgvector) | ✅ Definidos |
| Motor de noticias (GDELT/NewsAPI, entidades, impacto) | 🟡 Stub (no inventa) |
| Modelo ML real (Elo+Poisson+LightGBM), backtesting | 🟡 Roadmap (`app/ml/README.md`) |
| Panel admin (ABM), Celery beat | 🟡 Andamiado |

---

## Tests

```bash
cd backend && pytest -q
```

---

## Variables de entorno

Ver `.env.example`. Clave: `DATA_PROVIDER` (`apifootball`|`thesportsdb`|`seed`),
`APIFOOTBALL_API_KEY` (tu key Pro), `APIFOOTBALL_LEAGUE_ID` (1),
`APIFOOTBALL_SEASON` (2026), `CARTELERA_SOURCE` (`auto`|`seed`|`live`),
`DISPLAY_TIMEZONE`, `DATABASE_URL`, `REDIS_URL`, `NEWSAPI_KEY`.
