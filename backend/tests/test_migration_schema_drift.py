"""
Guards against model/migration schema drift.

This session found multiple real, previously-invisible bugs where a
SQLAlchemy model column existed and was actively used by app code, but the
Alembic migrations never actually created it (or created it with an
incompatible type, e.g. JSON vs Postgres ARRAY) - because the rest of the
test suite builds its schema with `Base.metadata.create_all()` (straight
from the models), it never touched the migrations at all, so this drift was
completely invisible until migrations were run against a real Postgres
database by hand.

This test runs the REAL Alembic migration chain against a throwaway
Postgres database (skipped if Postgres isn't reachable - CI/deployment
environments should make sure it is) and asserts every column the models
declare actually exists afterward. It intentionally does not check the
reverse direction (extra DB columns not on any model) - a migration is
allowed to add a column a model hasn't picked up yet without failing this
check, but a model must never reference a column the migrations never
created.
"""
import os
import subprocess

import pytest
from sqlalchemy import create_engine, inspect

from app.db.database import Base
import app.models  # noqa: F401 - registers all models on Base.metadata


MIGRATION_TEST_DB_URL = os.environ.get(
    "MIGRATION_DRIFT_TEST_DATABASE_URL",
    "postgresql://studenthelp:studenthelp@localhost:5432/studenthelp_migration_drift_test",
)


def _postgres_reachable(url: str) -> bool:
    try:
        engine = create_engine(url, connect_args={"connect_timeout": 2})
        with engine.connect():
            return True
    except Exception:
        return False


@pytest.mark.skipif(
    not _postgres_reachable(MIGRATION_TEST_DB_URL.rsplit("/", 1)[0] + "/postgres"),
    reason="Postgres not reachable in this environment - schema-drift check needs a real Postgres instance.",
)
def test_migrations_create_every_column_the_models_expect():
    admin_url = MIGRATION_TEST_DB_URL.rsplit("/", 1)[0] + "/postgres"
    db_name = MIGRATION_TEST_DB_URL.rsplit("/", 1)[1]

    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        conn.exec_driver_sql(f'DROP DATABASE IF EXISTS "{db_name}"')
        conn.exec_driver_sql(f'CREATE DATABASE "{db_name}"')

    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env = dict(os.environ, DATABASE_URL=MIGRATION_TEST_DB_URL)
    result = subprocess.run(
        ["python", "-m", "alembic", "upgrade", "head"],
        cwd=backend_dir, env=env, capture_output=True, text=True,
    )
    assert result.returncode == 0, f"alembic upgrade head failed:\n{result.stdout}\n{result.stderr}"

    engine = create_engine(MIGRATION_TEST_DB_URL)
    insp = inspect(engine)
    db_columns = {t: {c["name"]: c["type"] for c in insp.get_columns(t)} for t in insp.get_table_names()}

    def _type_family(sqla_type) -> str:
        """Collapses a SQLAlchemy/DB type to a coarse family so we can catch
        the exact bug this test exists for: a model declaring a column as
        generic JSON when the real migrated column is a Postgres ARRAY (or
        vice versa). Column-name-only comparison would miss this entirely -
        both sides have a column called e.g. 'target_company_ids', just with
        incompatible physical types, which only breaks at INSERT time."""
        # Unwrap Variant (e.g. ARRAY(...).with_variant(JSON(), "sqlite")) to
        # its Postgres-dialect implementation for this comparison.
        if hasattr(sqla_type, "impl") and hasattr(sqla_type, "mapping"):
            sqla_type = sqla_type.mapping.get("postgresql", sqla_type.impl)
        name = type(sqla_type).__name__.upper()
        if "ARRAY" in name:
            return "ARRAY"
        if "JSON" in name:
            return "JSON"
        return name

    problems = []
    for table in Base.metadata.sorted_tables:
        if table.name not in db_columns:
            problems.append(f"table '{table.name}' exists as a model but was never migrated")
            continue
        db_cols = db_columns[table.name]
        model_col_names = {c.name for c in table.columns}
        missing = model_col_names - set(db_cols.keys())
        if missing:
            problems.append(f"table '{table.name}' is missing columns in the real migrated schema: {sorted(missing)}")

        for col in table.columns:
            if col.name not in db_cols:
                continue
            model_family = _type_family(col.type)
            db_family = _type_family(db_cols[col.name])
            if {model_family, db_family} == {"ARRAY", "JSON"}:
                problems.append(
                    f"table '{table.name}' column '{col.name}': model declares {model_family} "
                    f"but the real migrated column is {db_family} - these are NOT insert-compatible "
                    f"(this is the exact bug class found in session 5 - e.g. inserting a Python list "
                    f"into a JSON-typed model column that's actually a Postgres ARRAY fails with "
                    f"'malformed array literal')"
                )
    engine.dispose()  # release the connection before dropping the database below

    with admin_engine.connect() as conn:
        conn.exec_driver_sql(f'DROP DATABASE IF EXISTS "{db_name}"')

    assert not problems, "Model/migration schema drift detected:\n" + "\n".join(problems)
