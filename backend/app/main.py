import os
from sqlalchemy import text

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import settings
from app.core.rate_limit import limiter
from app.db.database import Base, engine, SessionLocal
from app.api.v1.api import api_router
from app.services.leetcode_reminder_service import send_daily_leetcode_reminders
from app.services.weekly_engine_service import send_weekly_quiz_reminders, generate_weekly_prep_plans
import app.models  # noqa: F401 - ensures models are registered on Base before create_all

if settings.SENTRY_DSN:
    import sentry_sdk

    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENV,
        traces_sample_rate=0.1,
    )

app = FastAPI(title="StudentHelp API", version="0.1.0")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

is_prod = settings.ENV == "production"
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"] if is_prod else ["*"],
    allow_headers=["Authorization", "Content-Type"] if is_prod else ["*"],
)


app.include_router(api_router, prefix="/api/v1")

os.makedirs(settings.LOCAL_STORAGE_DIR, exist_ok=True)
app.mount("/media", StaticFiles(directory=settings.LOCAL_STORAGE_DIR), name="media")


def run_replica_safe_job(lock_id: int, job_fn):
    """Executes a background job acquiring a PostgreSQL advisory lock when running
    on Postgres, preventing duplicate execution across multiple server replicas."""
    db = SessionLocal()
    try:
        if db.bind.dialect.name == "postgresql":
            acquired = db.execute(text("SELECT pg_try_advisory_lock(:lock_id)"), {"lock_id": lock_id}).scalar()
            if not acquired:
                return  # Another replica is running this job
            try:
                job_fn(db)
            finally:
                db.execute(text("SELECT pg_advisory_unlock(:lock_id)"), {"lock_id": lock_id})
        else:
            job_fn(db)
    finally:
        db.close()


@app.on_event("startup")
def on_startup():
    if settings.AUTO_CREATE_TABLES:
        Base.metadata.create_all(bind=engine)

    def _run_leetcode_reminders_job():
        run_replica_safe_job(1001, send_daily_leetcode_reminders)

    def _run_weekly_quiz_reminders_job():
        run_replica_safe_job(1002, send_weekly_quiz_reminders)

    def _run_weekly_prep_plan_job():
        run_replica_safe_job(1003, generate_weekly_prep_plans)

    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(_run_leetcode_reminders_job, "cron", hour=15, minute=0, id="leetcode_daily_reminders")
    scheduler.add_job(_run_weekly_quiz_reminders_job, "cron", day_of_week="mon", hour=3, minute=30, id="weekly_quiz_reminders")
    scheduler.add_job(_run_weekly_prep_plan_job, "cron", day_of_week="mon", hour=4, minute=0, id="weekly_prep_plans")
    scheduler.start()
    app.state.scheduler = scheduler


@app.on_event("shutdown")
def on_shutdown():
    scheduler = getattr(app.state, "scheduler", None)
    if scheduler:
        scheduler.shutdown(wait=False)


@app.get("/health")
def health_check():
    return {"status": "ok"}