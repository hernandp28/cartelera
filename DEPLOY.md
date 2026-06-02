# Desplegar la cartelera — Vercel (frontend) + Render (backend)

La cartelera **no necesita base de datos ni Redis**: el backend sirve los datos
de TheSportsDB en vivo + el seed. Solo desplegás 2 cosas:

- **Backend (FastAPI)** → Render
- **Frontend (Next.js)** → Vercel

## URLs de producción actuales

| Servicio | URL |
|----------|-----|
| Backend (Render) | https://cartelera-api-vn4z.onrender.com |
| Frontend (Vercel) | https://cartelera-ceya7uedn-hernan-mundial.vercel.app |

---

## Paso 0 — Subir el código a GitHub

Tanto Vercel como Render despliegan desde un repo de GitHub.

```bash
cd "C:\Users\Ryzen PC\Documents\Cartelera"
git init
git add .
git commit -m "Cartelera Mundial 2026"
# Creá un repo vacío en github.com y luego:
git remote add origin https://github.com/TU_USUARIO/cartelera.git
git push -u origin main
```

> El `.gitignore` ya excluye `node_modules/`, `.next/`, `.venv/`, `__pycache__/`,
> `.tmp/` y el `.env`. **El `.env` con tu API key NO se sube** — la key se carga
> como variable de entorno en Render (más seguro).

---

## Paso 1 — Backend en Render

1. Entrá a https://render.com → **New +** → **Blueprint**.
2. Conectá tu repo de GitHub. Render detecta el archivo **`render.yaml`** y
   propone el servicio `cartelera-api`.
3. Antes de crear, te va a pedir las variables marcadas `sync: false`:
   - **`APIFOOTBALL_API_KEY`** = tu key Pro de API-Football
   - **`API_CORS_ORIGINS`** = dejalo provisorio (ej. `*`) por ahora; lo ajustás
     en el Paso 3 con la URL real de Vercel.
4. **Create** y esperá el build (~3-5 min).
5. Te queda una URL tipo **`https://cartelera-api-vn4z.onrender.com`**.
   Probala: `https://cartelera-api-vn4z.onrender.com/health` → debe responder JSON.

> ⚠️ El plan **free** de Render "duerme" el servicio tras ~15 min sin tráfico
> (primer request luego tarda ~50 s). Como la cartelera consulta cada 10 s,
> mientras esté abierta se mantiene despierta. Si querés evitar el cold start,
> el plan Starter (~7 USD/mes) no duerme.

### Alternativa sin `render.yaml` (manual)
New + → **Web Service** → repo → **Root Directory: `backend`** →
Runtime **Docker** → agregá las env vars del `render.yaml` a mano.

---

## Paso 2 — Frontend en Vercel

1. Entrá a https://vercel.com → **Add New** → **Project** → importá el repo.
2. **IMPORTANTE — Root Directory:** poné **`frontend`** (no la raíz).
   Vercel detecta Next.js solo.
3. En **Environment Variables** agregá:
   - **`NEXT_PUBLIC_API_BASE_URL`** = la URL del backend en Render
     (ej. `https://cartelera-api-vn4z.onrender.com`, **sin** barra final).
4. **Deploy**. Te queda una URL tipo **`https://cartelera-ceya7uedn-hernan-mundial.vercel.app`**.

---

## Paso 3 — Conectar los dos (CORS)

Falta que el backend acepte llamadas desde el dominio del frontend:

1. En Render → servicio `cartelera-api` → **Environment** →
   editá **`API_CORS_ORIGINS`** = tu URL de Vercel
   (ej. `https://cartelera-ceya7uedn-hernan-mundial.vercel.app`). Podés poner varias separadas por coma.
2. Guardá → Render redeploya solo.
3. Abrí tu URL de Vercel: la cartelera ya consume datos reales desde cualquier lado. ✅

---

## Resumen de variables

| Dónde | Variable | Valor |
|-------|----------|-------|
| Render | `APIFOOTBALL_API_KEY` | tu key Pro de API-Football |
| Render | `API_CORS_ORIGINS` | URL de Vercel (paso 3) |
| Vercel | `NEXT_PUBLIC_API_BASE_URL` | URL de Render |

El resto (liga 1, temporada 2026, amistosos, timezone) ya tiene valores por
defecto en el código / `render.yaml`.

---

## Actualizar después

Cada `git push` a `main` redeploya **automáticamente** Vercel y Render. No hay
que volver a tocar nada.
