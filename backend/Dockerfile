FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libgomp1 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
# Render (y otros PaaS) inyectan el puerto en $PORT; localmente cae a 8000.
# Forma shell para que ${PORT} se expanda.
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
