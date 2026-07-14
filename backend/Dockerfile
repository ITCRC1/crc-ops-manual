FROM python:3.11-slim

WORKDIR /app

# build-essential: por si algún wheel (asyncpg, argon2-cffi) necesita compilar.
# La firma de PDF usa ReportLab (puro Python) — no hace falta pango/cairo/gdk-pixbuf.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Railway inyecta $PORT y espera que la app escuche ahí; 8000 es el default local.
# `alembic upgrade head` corre en cada arranque: es idempotente y deja el esquema de
# producción al día automáticamente (elimina el paso manual de migración vía proxy).
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
