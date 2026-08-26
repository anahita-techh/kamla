# KAMLA

Production-oriented academic decision and planning platform.

This monorepo follows ADR-001:

- `apps/web` — Next.js presentation only (Vercel). Never talks to the database.
- `apps/api` — FastAPI application layer (Fly.io). PostgreSQL + RLS is the source of truth.

The frontend must not contain database credentials or perform privileged data access.

## Privacy

- Student data is not sent to model providers for training.
- Chat messages are retained 90 days unless deleted earlier.
- Uploaded PDFs are retained until the student deletes them or the account.
- Account deletion wipes remaining student data within 30 days.

## Local development

API:

```bash
cd apps/api
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
alembic upgrade head
```

`alembic upgrade head` creates the `kamla_app` role (NOLOGIN by default — it's meant to be
granted a login, not connected to directly). Give it a local password once per database
before running the app, then set `APP_DATABASE_URL` in `.env` to match:

```bash
docker exec <postgres-container-name> psql -U postgres -d kamla -c \
  "ALTER ROLE kamla_app LOGIN PASSWORD 'your-local-password'"
```

```bash
uvicorn kamla_api.main:app --reload --port 8000
```

Web:

```bash
cd apps/web
cp .env.example .env.local
npm install
npm run dev
```

Required env: `DATABASE_URL` (migrations only, `postgresql+psycopg://...`), `APP_DATABASE_URL`
(the running app's connection — must be the `kamla_app` role, `NOBYPASSRLS`), Clerk keys,
`NEXT_PUBLIC_API_URL=http://localhost:8000`.
