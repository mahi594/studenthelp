import os

from pydantic_settings import BaseSettings
from typing import List

# Absolute path to backend/.env, next to this file - NOT relative to the
# current working directory. A relative ".env" here silently resolves
# against whatever directory a command happens to be run from (repo root,
# backend/, etc.), and if it doesn't find a match there it fails silently
# and falls back to the hardcoded defaults below instead of raising - which
# is exactly what caused TEST_DATABASE_URL to appear "ignored".
_ENV_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")


class Settings(BaseSettings):
    ENV: str = "development"

    DATABASE_URL: str = "postgresql://studenthelp:studenthelp@localhost:5432/studenthelp"

    # True = call Base.metadata.create_all() on startup (fine for quick local
    # dev). Set to False once you're using Alembic migrations, since the two
    # can conflict (create_all won't know about migration history).
    AUTO_CREATE_TABLES: bool = True

    # Separate DB for running tests against (tables get created/dropped
    # freely here) - never point this at your real dev/prod database.
    TEST_DATABASE_URL: str = "postgresql://studenthelp:studenthelp@localhost:5432/studenthelp_test"

    SECRET_KEY: str = "change-this-to-a-random-secret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days

    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""

    # Job listings source (Adzuna - free tier: https://developer.adzuna.com)
    ADZUNA_APP_ID: str = ""
    ADZUNA_APP_KEY: str = ""
    ADZUNA_COUNTRY: str = "in"   # "in" = India; see Adzuna docs for other country codes

    # File storage - S3-compatible (works with AWS S3 or Cloudflare R2).
    # Leave S3_ENDPOINT_URL empty for AWS S3. For R2, set it to your
    # account's R2 endpoint (https://<account_id>.r2.cloudflarestorage.com).
    S3_ENDPOINT_URL: str = ""
    S3_ACCESS_KEY_ID: str = ""
    S3_SECRET_ACCESS_KEY: str = ""
    S3_BUCKET_NAME: str = "studenthelp-resumes"
    S3_REGION: str = "auto"   # "auto" works for R2; use a real AWS region (e.g. "ap-south-1") for S3
    # Base URL to construct public links from, e.g. your R2 public bucket URL
    # or a CloudFront/S3 URL. Leave empty to use presigned URLs instead (private bucket).
    S3_PUBLIC_URL_BASE: str = ""
    
    MAX_RESUME_UPLOAD_BYTES: int = 15 * 1024 * 1024

    # Dev-only fallback: when S3_ACCESS_KEY_ID/S3_SECRET_ACCESS_KEY are unset,
    # resumes are written to local disk (LOCAL_STORAGE_DIR) and served back
    # via /media, instead of raising "not configured". Not for production -
    # files won't survive a container rebuild unless that path is a mounted
    # volume, and BACKEND_PUBLIC_URL must be reachable from the browser.
    LOCAL_STORAGE_DIR: str = "local_uploads"
    BACKEND_PUBLIC_URL: str = "http://localhost:8080"

    # Email (for password reset). Leave SMTP_HOST empty to skip real sending -
    # /auth/forgot-password will return the reset token directly instead
    # (dev-only fallback, see email_service.py).
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""

    # Used to build the password reset link sent to the student
    FRONTEND_URL: str = "http://localhost:3000"

    CORS_ORIGINS: str = "http://localhost:3000"

    # Error monitoring. Leave empty to disable (default) - no Sentry account
    # needed to run the app. Get a DSN from https://sentry.io if you want it.
    SENTRY_DSN: str = ""

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    class Config:
        env_file = _ENV_FILE


settings = Settings()

if settings.ENV == "production":
    if not settings.SECRET_KEY or settings.SECRET_KEY in ["change-this-to-a-random-secret", "secret", "change_me"]:
        raise RuntimeError("Production deployment requires a secure, non-default SECRET_KEY")
    if not settings.SMTP_HOST:
        raise RuntimeError("SMTP_HOST must be configured in production to prevent fallback credential exposure")

MAX_RESUME_UPLOAD_BYTES: int = 15 * 1024 * 1024