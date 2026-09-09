# Smart Greenhouse

Operator dashboard for a smart greenhouse — Phase 1 skeleton (FastAPI, PostgreSQL, React).

## Prerequisites

| Tool | Minimum |
|------|---------|
| Python | 3.11+ |
| Node.js | 20 LTS |
| Docker Desktop | current (engine must be running) |

If port 5432 is already used by a local PostgreSQL, set `POSTGRES_PORT` in `.env` (and the matching host port in Compose) before `docker compose up`.

## First-time setup

From this `Example-project` folder:

1. Copy environment files:

   ```powershell
   Copy-Item .env.example .env
   Copy-Item frontend/.env.example frontend/.env
   ```

2. Start PostgreSQL:

   ```powershell
   docker compose up -d
   docker compose ps
   ```

3. Install the backend and apply the Alembic baseline (no business tables yet):

   ```powershell
   cd backend
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -e ".[dev]"
   alembic upgrade head
   cd ..
   ```

4. Install the frontend:

   ```powershell
   cd frontend
   npm install
   cd ..
   ```

## Daily start

Three terminals, all from `Example-project`:

```text
Terminal 1: docker compose up -d
Terminal 2: cd backend && .\.venv\Scripts\Activate.ps1 && cd src && uvicorn main:app --reload --host 0.0.0.0 --port 8000
Terminal 3: cd frontend && npm run dev
```

Run backend tests from `backend/` (PYTHONPATH is set in `pyproject.toml`):

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pytest
```

## URLs

| What | URL |
|------|-----|
| API | http://localhost:8000 |
| Health | http://localhost:8000/health |
| Scalar API reference | http://localhost:8000/scalar |
| OpenAPI JSON | http://localhost:8000/openapi.json |
| Dashboard UI | http://localhost:5173/dashboard |

Swagger `/docs` is disabled on purpose.

## Phase order

Course assignments: [../phases/README.md](../phases/README.md) (also [docs/phases/README.md](docs/phases/README.md)).
