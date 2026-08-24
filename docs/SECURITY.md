# StudentHelp — Security & Compliance Blueprint

This document describes what is ACTUALLY implemented and tested, not an
aspirational target. See `docs/PRODUCTION_CHECKLIST.md` for the full,
per-phase PASS/PARTIAL/FAIL audit trail this file is derived from.

---

## 1. Authentication & Token Hardening
- **JWT Scope Enforcement**: Tokens carry explicit scopes (`access`, `password_reset`, `email_verify`, `password_change`). Endpoints strictly validate token scopes to prevent token misuse.
- **Python 3.13 / Bcrypt 4.0+ Compatibility**: Safe password handling prevents secret truncation crashes and enforces password strength checks.
- **Production Guardrails**:
  - Dev token return endpoints (`dev_reset_token`, `dev_verify_token`) are strictly disabled when `ENV=production`.
  - Application startup verifies secret key strength (`SECRET_KEY` cannot be a default placeholder in production).

## 2. Multi-Tenancy & Authorization Boundaries
- **What's actually enforced**: every institution-owned TPO-facing resource — the student roster (`/tpo/dashboard`), interventions (create/list/get/complete), CSV export, and the LeetCode admin tracker/notification fanout — is scoped server-side to the authenticated TPO's `institution_id`, never to `college_name` (a free-text field kept only for display). A `tpo_admin` with no `institution_id` is refused (403) rather than silently shown every institution's data. Cross-institution access returns 404 (not 403) so a caller can't distinguish "doesn't exist" from "belongs to someone else." This is tested end-to-end in `tests/test_tpo.py` and `tests/test_leetcode_isolation.py` — two institutions, two TPOs, cross-access attempts asserted to fail.
- **Ownership scoping**: resumes, roadmaps, prep plans, and quiz results are scoped to the owning student's `user_id`. A previously-real bug (`GET /roadmap/{id}` had no authentication dependency at all) was found and fixed this hardening pass — see `tests/test_roadmap.py`.
- **Intentionally NOT institution-scoped**: companies, Q&A posts, and job listings are a shared platform-wide catalog (a real company recruits across colleges) — this is a deliberate design choice, not a gap.
- Role-Based Access Control (RBAC) enforced across endpoints:
  - `student`: personal dashboard, quizzes, mock interviews, resume, applications.
  - `tpo_admin`: their own institution's batch analytics, risk categories, interventions, and CSV exports — never another institution's.
  - `admin`: a platform-level operator role (content moderation, account creation), not tied to a single institution.

## 3. Storage & Upload Validation
- PDF resume uploads are validated against: extension allow-list, declared MIME type, and the PDF magic-byte signature (`b"%PDF"`) — non-PDF/spoofed files are rejected with HTTP 400 before any parsing happens.
- `MAX_RESUME_UPLOAD_BYTES` is enforced before parsing (previously defined but never actually checked — fixed).
- Storage keys are generated from a sanitized filename fragment (`os.path.basename` + allow-listed characters only) plus a random UUID, never the raw uploaded filename — this closes a path-traversal hole where a filename like `../../etc/cron.d/x.pdf` could previously influence the on-disk path. A defense-in-depth `commonpath` check in the local storage writer refuses to write anywhere outside the configured upload directory.
- Files are stored in S3/R2-compatible cloud buckets or isolated local storage with randomized keys.

## 4. Background Job & Replica Safety
- APScheduler jobs utilize PostgreSQL advisory locks (`pg_try_advisory_lock`) in production.
- Prevents duplicate cron job runs across multiple server replicas.

## 5. Error Handling
- FastAPI's default unhandled-exception path returns a generic 500 with no traceback (the app does not run with `debug=True`).
- One real leak was found and fixed: `job_listings.py`'s refresh endpoint was returning the raw exception string in the HTTP response body. Now logs server-side and returns a generic message.

## 6. Schema Integrity (found via real Postgres testing, not assumed)
- The automated test suite historically built its schema with SQLAlchemy's `Base.metadata.create_all()` rather than the real Alembic migrations, which meant model/migration drift was invisible to it. Running the real migration chain against an actual PostgreSQL database surfaced several columns that existed on models (and were actively read/written by app code) but were never migrated — including a `JSON` vs Postgres `ARRAY` type mismatch on several list-valued columns that broke inserts outright. All found instances were fixed (see migration `c3f7e9a21d5b`), and a permanent regression test (`tests/test_migration_schema_drift.py`) now runs the real migration chain and diffs it against the models on every test run, so this class of bug can't silently reappear.

