# StudentHelp — Production Deployment Guide

This guide covers deploying StudentHelp to production environments (e.g. Railway, Render, AWS, Docker).

---

## 1. Prerequisites
- **PostgreSQL 14+** Database
- **Python 3.11+** Runtime
- **Node.js 18+** Runtime
- Environment Variables configured based on `.env.example`

---

## 2. Environment Setup

Copy `.env.example` to `.env` in the `backend/` directory:

```bash
cd backend
cp .env.example .env
```

Ensure production values are configured:
- `ENV=production`
- `SECRET_KEY=<long-random-secret-key>`
- `DATABASE_URL=postgresql://user:pass@host:5432/studenthelp`
- `GEMINI_API_KEY=<your-gemini-api-key>`
- `GROQ_API_KEY=<your-groq-api-key>`

---

## 3. Database Migration & Seeding

Run Alembic database migrations:
```bash
cd backend
alembic upgrade head
```

Seed demonstration institutional data:
```bash
python scripts/seed_demo_data.py
```

---

## 4. Running Backend Server

Production startup command (using Gunicorn / Uvicorn workers):
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

---

## 5. Running Frontend Web App

Build and launch the Next.js production frontend:
```bash
cd web
npm run build
npm start
```

---

## 6. Docker Deployment

Launch via Docker Compose:
```bash
docker compose down
docker compose build --no-cache
docker compose up -d
docker compose ps
docker compose logs --tail=200
```

---

## 7. Verification Status (honest, as of this hardening pass)

- **Migrations**: verified by running the full Alembic chain (`alembic upgrade head`) against a genuinely empty, real PostgreSQL 16 database, inspecting the resulting schema column-by-column against every SQLAlchemy model, and confirming `alembic downgrade` + re-`upgrade` both work. A permanent regression test (`backend/tests/test_migration_schema_drift.py`) now runs this same check automatically.
- **Demo seed script** (`backend/scripts/seed_demo_data.py`): run end-to-end against real Postgres. Every readiness/intervention number it prints (the "before" and "after" composite scores, the improvement delta) is computed by the same production engine, not hardcoded — re-running it after a formula change will naturally produce different numbers.
- **`docker compose up` itself**: has not been run in the environment this hardening work was done in (no `docker` binary available there, separate from the Postgres/database verification above). The Dockerfiles and `docker-compose.yml` have been read and are structurally consistent with everything above (Postgres 16 with a healthcheck, `alembic upgrade head` on backend container start, curl-based backend healthcheck), but this should be verified with an actual `docker compose up` run before relying on it in production.
