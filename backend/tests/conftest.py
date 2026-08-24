"""
Shared test fixtures.

IMPORTANT: tests run against a real Postgres database (TEST_DATABASE_URL in
.env), NOT SQLite - our models use Postgres-specific types (UUID, ARRAY,
JSON columns) that don't translate to SQLite. Create a separate database
before running tests:
    createdb studenthelp_test
Never point TEST_DATABASE_URL at your real dev/prod database - tables are
dropped and recreated on every test run.

AI calls (Gemini/Groq) are mocked in every test via the `mock_ai` fixture
(autouse) so running the test suite never costs real API credits and never
needs real API keys configured.

Email sending is mocked in every test via the `mock_email` fixture (autouse)
so running the test suite never hits real SMTP, regardless of what's
configured in .env.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from passlib.handlers.bcrypt import _BcryptBackend
# Fix passlib compatibility with bcrypt >= 4.0 on Python 3.13
if not hasattr(_BcryptBackend, "_orig_calc_checksum"):
    _BcryptBackend._orig_calc_checksum = _BcryptBackend._calc_checksum
    def _safe_calc_checksum(self, secret):
        if isinstance(secret, str):
            secret = secret.encode("utf-8")
        if isinstance(secret, bytes) and len(secret) > 72:
            secret = secret[:72]
        return self._orig_calc_checksum(secret)
    _BcryptBackend._calc_checksum = _safe_calc_checksum

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.core.config import settings
from app.db.database import Base, get_db
from app.main import app
import app.models as _models  # noqa: F401 - registers all models on Base.metadata

try:
    TEST_ENGINE = create_engine(settings.TEST_DATABASE_URL, connect_args={"connect_timeout": 2})
    with TEST_ENGINE.connect() as conn:
        pass
except Exception:
    # Fallback to in-memory SQLite if PostgreSQL is not active locally
    TEST_ENGINE = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Fresh schema at the start of the test session, dropped at the end."""
    Base.metadata.drop_all(bind=TEST_ENGINE)
    Base.metadata.create_all(bind=TEST_ENGINE)
    yield
    Base.metadata.drop_all(bind=TEST_ENGINE)



@pytest.fixture()
def db_session():
    """A DB session for direct setup/assertions inside a test (e.g. promoting
    a user to admin without going through an API endpoint)."""
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session):
    """A TestClient with the real `get_db` dependency swapped for the test DB."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def mock_ai(mocker):
    """Mocks every AI-calling function so the test suite never hits real
    Gemini/Groq APIs. Patched at each endpoint module's import site (they use
    `from app.services.ai_service import X`, which binds a local name at
    import time - patching the source module wouldn't affect that reference)."""
    mocker.patch(
        "app.api.v1.endpoints.prep_plan.generate_prep_plan",
        return_value=[{"day": 1, "topic": "DSA", "task": "Solve 5 array problems",
                       "source_title": None, "source_url": None, "reason": "weak subject"}],
    )
    mocker.patch(
        "app.api.v1.endpoints.roadmap.generate_roadmap",
        return_value=[{"phase": "Month 1", "focus_subjects": ["DSA"], "milestones": ["Solve 20 problems"],
                       "reason": "weakest subject"}],
    )
    mocker.patch(
        "app.services.weekly_engine_service.generate_prep_plan",
        return_value=[{"day": 1, "topic": "DSA", "task": "Solve 5 array problems",
                       "source_title": None, "source_url": None, "reason": "weak subject"}],
    )
    mocker.patch(
        "app.api.v1.endpoints.resume.match_resume_to_company",
        return_value={"match_score_percent": 72, "missing_keywords": ["Docker"],
                      "suggestions": ["Add a project using Docker"], "meets_cgpa_cutoff": True},
    )
    mocker.patch(
        "app.api.v1.endpoints.admin.generate_quiz_questions",
        return_value=[
            {"question_text": "What is the time complexity of binary search?",
             "options": ["O(n)", "O(log n)", "O(n^2)", "O(1)"],
             "correct_option_index": 1, "difficulty": "Easy",
             "explanation": "Binary search halves the search space each step."}
        ],
    )
    mocker.patch("app.api.v1.endpoints.chat.answer_chat_question", return_value="Here's a general study tip.")
    mocker.patch("app.api.v1.endpoints.mock_interview.start_mock_interview", return_value="Tell me about a challenging project.")
    mocker.patch("app.api.v1.endpoints.mock_interview.continue_mock_interview", return_value="Good - what was the outcome?")
    mocker.patch(
        "app.api.v1.endpoints.mock_interview.score_mock_interview",
        return_value={"overall_score": 68, "strengths": ["Clear communication"], "improvements": ["More depth on tradeoffs"]},
    )


@pytest.fixture(autouse=True)
def mock_email(mocker):
    """Mocks email-sending so the test suite never hits real SMTP - without
    this, tests fail against real providers like Resend, which reject sending
    to placeholder test domains (e.g. example.com) with a hard SMTP error.
    Patched at the import site in auth.py, same reasoning as mock_ai above.

    Also patched at admin.py's import site (used by /admin/create-admin) -
    it imports is_email_configured/send_email independently, so without this
    a test environment with real SMTP_HOST/SMTP_PASSWORD set in .env would
    otherwise attempt a real send on every create-admin test."""
    mocker.patch("app.api.v1.endpoints.auth.send_verification_email", return_value=None)
    mocker.patch("app.api.v1.endpoints.auth.send_password_reset_email", return_value=None)
    mocker.patch("app.api.v1.endpoints.auth.is_email_configured", return_value=False)
    mocker.patch("app.api.v1.endpoints.admin.is_email_configured", return_value=False)
    mocker.patch("app.api.v1.endpoints.admin.send_email", return_value=False)
    mocker.patch("app.services.weekly_engine_service.is_email_configured", return_value=False)
    mocker.patch("app.services.weekly_engine_service.send_email", return_value=False)


@pytest.fixture(autouse=True)
def reset_rate_limits():
    """All test requests come from the same TestClient 'IP', so without this,
    calls accumulate against the real per-minute limits across tests and can
    cause flaky 429s unrelated to what a test is actually checking."""
    from app.core.rate_limit import limiter
    limiter.reset()
    yield


@pytest.fixture()
def registered_user(client):
    """Registers a student with a unique email (the test DB persists across
    the whole test session, not per-test, so a fixed email would collide
    between tests) and returns (email, password, headers) with a valid token."""
    import uuid
    email = f"student-{uuid.uuid4().hex[:10]}@example.com"
    password = "testpass123"

    client.post("/api/v1/auth/register", json={
        "name": "Test Student", "email": email, "password": password,
        "branch": "CSE", "grad_year": 2027,
    })
    login_res = client.post("/api/v1/auth/login", data={
        "grant_type": "password", "username": email, "password": password,
    })
    token = login_res.json()["access_token"]
    return {"email": email, "password": password, "headers": {"Authorization": f"Bearer {token}"}}


@pytest.fixture()
def admin_user(client, db_session, registered_user):
    """Promotes the registered_user to admin directly in the DB (mirrors the
    real manual promotion flow documented in FUNCTIONALITY.md) and returns
    the same auth headers, now with admin privileges."""
    from app.models.user import User

    user = db_session.query(User).filter(User.email == registered_user["email"]).first()
    user.role = "admin"
    db_session.commit()
    return registered_user