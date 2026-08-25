from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import UUID

from app.core.config import settings


@compiles(UUID, "sqlite")
def compile_uuid_sqlite(type_, compiler, **kw):
    return "VARCHAR(36)"


try:
    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
    with engine.connect() as conn:
        pass
except Exception as exc:
    env_str = str(getattr(settings, "ENVIRONMENT", "") or getattr(settings, "ENV", "")).lower()
    if env_str == "production":
        raise RuntimeError(f"Production mode requires PostgreSQL database connection. Cannot connect to {settings.DATABASE_URL}: {exc}") from exc
    # Local dev fallback to SQLite if PostgreSQL is not running or driver is missing
    engine = create_engine("sqlite:///./studenthelp_dev.db", connect_args={"check_same_thread": False})


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()



def get_db():
    """FastAPI dependency that yields a DB session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
