# CRC Operations Manual Hub

Sistema web multipropiedad, en español, para administrar Procedimientos Operativos Estándar (SOP), Descriptores de Puesto y Políticas de **The Costa Rica Collection** (Corcovado Wilderness Lodge, Amarena, Oxigen, Ojochal Garden Villas).

Spec completo del proyecto: [`docs/PROMPT_CLAUDE_CODE_CRC_OPS_MANUAL.md`](docs/PROMPT_CLAUDE_CODE_CRC_OPS_MANUAL.md).

## Estado actual

**Etapa 3 completa** — ingesta y reconciliación: 76 SOPs + 24 Descriptores cargados (borrador), CWL pre-asignado (`adoptado`). Reporte en [`seed/reconciliation_report.csv`](seed/reconciliation_report.csv), pipeline en [`backend/app/ingestion/`](backend/app/ingestion/README.md). Ver [`CHANGELOG.md`](CHANGELOG.md).
Pendiente: Etapa 4 (backend API — auth, CRUD, firma, asignación).

### Ingesta reproducible (backend)

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m app.ingestion.run_all
```

### Migraciones y seed (backend)

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
alembic upgrade head
python -m app.seed
```

## Stack

- **Backend:** Python 3.11 · FastAPI · SQLAlchemy 2.x (async) · Alembic · PostgreSQL
- **Frontend:** Next.js 14 (App Router) · TypeScript · Tailwind CSS
- **Infra:** Railway (`crc-ops-manual-api`) · Vercel (`crc-ops-manual-web`)

## Arranque local (Windows)

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Healthcheck: `http://localhost:8000/api/salud`

### Frontend

```powershell
cd frontend
npm install
copy .env.example .env.local
npm run dev
```

Abre `http://localhost:3000`.

### Base de datos local (opcional, vía Docker)

```powershell
docker compose up -d db
```

## Estructura del repositorio

Ver §15 del spec — `backend/app/{models,schemas,api,services,firma,ingestion,core}`, `frontend/app`, `seed/source`, `scripts/`, `docs/`.

## Reglas críticas

- El PDF de referencia USALI (`seed/source/usali-*.pdf`) tiene copyright: **solo referencia conceptual**, nunca copiar/almacenar su texto.
- No tocar ni reutilizar el stack `crc-coordination-hub` (proyecto separado).
- Antes de crear cualquier recurso remoto (repo, proyecto Railway/Vercel, base de datos), verificar si ya existe.
