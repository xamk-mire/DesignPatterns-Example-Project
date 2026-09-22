# Smart Greenhouse

Operator dashboard for a smart greenhouse — Phase 3 (Abstract Factory device families) on Phases 1–2.

## Prerequisites

| Tool | Minimum |
|------|---------|
| Python | 3.11+ (optional host venv) |
| Node.js | 20 LTS (optional host `npm`) |
| Docker Desktop | current (engine must be running) |

If host port 5432 is already used, keep `POSTGRES_PORT=5435` in `.env`. Compose still maps that host port to **5432 inside** the Postgres container. Backend containers talk to hostname `postgres` on 5432.

## First-time setup

From this `Example-project` folder:

```powershell
Copy-Item .env.example .env
Copy-Item frontend/.env.example frontend/.env
docker compose up --build -d
docker compose exec backend alembic upgrade head
```

Optional host tooling (debug only):

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
cd ..\frontend
npm install
```

Host `DATABASE_URL` in `.env` uses `localhost` and `POSTGRES_PORT`. Compose **overrides** backend `DATABASE_URL` to `@postgres:5432`.

## Daily start (required path)

```powershell
docker compose up --build -d
docker compose exec backend alembic upgrade head
```

Migrations from this phase onward:

```powershell
docker compose exec backend alembic revision --autogenerate -m "message"
docker compose exec backend alembic upgrade head
```

Tests:

```powershell
docker compose exec backend pytest tests -q
```

Host venv remains valid for unit tests (`cd backend` then `pytest`).

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

Pattern notes: [docs/patterns/factory-method.md](docs/patterns/factory-method.md), [docs/patterns/abstract-factory.md](docs/patterns/abstract-factory.md).
