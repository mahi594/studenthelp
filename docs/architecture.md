# StudentHelp — Architecture Notes

## Core design rule
Company facts (rounds, subjects tested, real questions, resume filters) are
**always curated** — entered by admins/seniors via `Company`, `Round`,
`Question`, `LearningResource` rows. The AI (Claude API, see
`app/services/ai_service.py`) is only ever given these facts as input and
asked to **sequence, prioritize, and personalize** them for a specific
student. It is never the source of truth for "what does company X ask."

This is enforced by prompt design (`build_plan_prompt`,
`build_resume_match_prompt`) — both explicitly instruct the model not to
invent facts, and only pass in data already in the database.

## Data flow: Prep Plan generation
1. Student takes diagnostic quiz → `QuizResult` rows (one per subject)
2. Student picks a target company → looked up from curated `Company`/`Round`
3. `POST /api/v1/prep-plan/generate` combines: company rounds/subjects
   (curated) + quiz scores (weak subjects first) + curated learning
   resources for those subjects
4. Claude sequences this into a day-wise task list (structured JSON)
5. Stored in `PrepPlan.tasks` — rendered as a checklist/progress UI, not
   free text

## Data flow: Resume matching
1. Student uploads resume PDF + picks target company
2. PDF parsed to text (`pypdf`)
3. Claude compares resume text against curated `Company.resume_keywords` /
   `min_cgpa` / `preferred_branches` — again, only curated facts as input
4. Returns match score + missing keywords + suggestions (structured JSON)

## Data flow: Roadmap (long-horizon, performance-driven)
Distinct from Prep Plan: Prep Plan is a short countdown for one target company;
Roadmap is a multi-month plan (e.g. semester-wise) driven purely by quiz score
trends over time. Re-generate it periodically (e.g. whenever new quiz results
come in) so it stays current with actual performance — see
`GET /api/v1/roadmap/user/latest` and `POST /api/v1/roadmap/generate`.

## Data flow: AI Chat bot
`POST /api/v1/chat/ask` — general placement/study Q&A with conversation memory
(`ChatMessage` table, capped history sent to the model). Same curated-facts
rule applies: if `company_id` is passed, the system prompt is only given that
company's curated `Round` data and is instructed to say "no verified data yet"
rather than guess if none exists. Off-topic questions are redirected — see
`CHAT_SYSTEM_PROMPT` in `app/services/ai_service.py`.

## AI Provider Strategy
Gemini (`gemini-1.5-flash`) is the primary provider — free daily quota, good
for development. If Gemini's quota or rate limit is hit, `ai_service.py`
automatically falls back to Groq (`llama-3.3-70b-versatile`, also has a free
tier). This fallback only triggers on quota/rate-limit errors specifically —
real bugs (bad prompt, auth failure) are re-raised normally rather than
silently masked. Requires both `GEMINI_API_KEY` and `GROQ_API_KEY` in `.env`;
get a free Groq key at console.groq.com.

## Data flow: Readiness Score + TPO Dashboard (the core differentiator)
`ReadinessScore` is a composite 0-100 number computed by a plain weighted
formula (NOT an AI call - see `app/services/readiness_service.py`) from:
quiz mastery average (60% weight) + resume match average (40% weight).
Deliberately non-AI so the number is transparent, reproducible, and
comparable across students - a black-box AI-scored "readiness" would
undermine the TPO dashboard's trustworthiness.

Each computation is saved as a new snapshot (`POST /readiness/compute`), not
overwritten, so `/readiness/history` renders a trend line over time.

`GET /tpo/dashboard` (role: `admin` or `tpo_admin` only) aggregates every
student's latest score: batch average, branch-wise breakdown, and a list of
students flagged below `LOW_READINESS_THRESHOLD` (50, in `tpo.py`) so a
placement cell can intervene early instead of discovering gaps in final year.

## Data flow: Job Listings (live openings — auto-fetched)
`JobListing` is deliberately SEPARATE from `Company`/`Round`: it's live,
temporary data (roles currently open, apply link, expiry), not the verified
interview-process facts admins curate. Fetched from Adzuna's free API
(https://developer.adzuna.com — sign up for a free `app_id`/`app_key`).

- `POST /admin/job-listings/refresh` (wait, actual path is `/job-listings/refresh`)
  fetches current listings for given keywords/location, dedupes by Adzuna's
  external ID, sets a 30-day expiry (`DEFAULT_LISTING_TTL_DAYS` in
  `job_listing_service.py`), and deletes anything already past expiry.
- `GET /job-listings/` — student-facing search by company/role/location.

**Important limitation - no built-in scheduler.** This scaffold has no cron/
background job runner, so `/refresh` only runs when something calls it. To
keep listings current automatically, schedule a call to that endpoint:
- **Windows**: Task Scheduler → run a script hourly/daily that does a POST
  request (e.g. via `curl` or a small PowerShell script) with an admin token
- **Linux/Mac**: a cron job doing the same with `curl`
- Or, once deployed, a simple hosted cron service (e.g. cron-job.org) hitting
  the endpoint on a schedule

Without scheduling this, listings will just go stale until someone manually
calls `/refresh` again - worth automating before this goes to real users.

## Alembic Migrations (set up, needs one manual step from you)
`migrations/env.py` is wired to `app.core.config.settings.DATABASE_URL` and
imports all models, so `--autogenerate` can diff against them. This couldn't
be finished end-to-end in the scaffold itself since generating the initial
migration requires a live DB connection.

**One-time setup (run this yourself):**
```bash
cd backend
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```
This creates `migrations/versions/<hash>_initial_schema.py` reflecting every
model, then applies it. After this, set `AUTO_CREATE_TABLES=false` in `.env`
so `main.py` stops calling `create_all()` on startup (the two approaches can
conflict since `create_all()` doesn't know about migration history).

**From then on, whenever you change a model:**
```bash
alembic revision --autogenerate -m "describe the change"
alembic upgrade head
```
Always read the generated migration file before running `upgrade` -
autogenerate is good but not perfect (e.g. it won't detect a column rename,
it'll see it as a drop+add and lose data unless you edit the migration by hand).

## File Storage (S3/R2 - resumes now actually saved)
`app/services/storage_service.py` wraps `boto3` in an S3-compatible way, so
it works with either real AWS S3 or Cloudflare R2 (same client, R2 just
needs `S3_ENDPOINT_URL` set). Resume uploads (`POST /resume/upload-and-match`)
now genuinely persist the PDF and return a real `file_url`, replacing the old
placeholder string.

Two modes, controlled by whether `S3_PUBLIC_URL_BASE` is set:
- **Public bucket** (`S3_PUBLIC_URL_BASE` set): `file_url` is a permanent
  direct link. Simplest, but the bucket/objects must allow public read.
- **Private bucket** (`S3_PUBLIC_URL_BASE` empty, the default): `file_url` is
  a presigned URL valid for 7 days. The `Resume.storage_key` column stores
  the object key so you can call `GET /resume/{id}/refresh-url` to get a
  fresh link once the old one expires - don't treat the stored `file_url` as
  permanent in this mode.

**Setup**: create a bucket (Cloudflare R2's free tier is generous and has no
egress fees - recommended over AWS S3 for this use case) and add credentials
to `.env`. See `.env.example` for the exact variables.

**Not done for you**: actually creating the bucket and generating API
credentials - that's a manual step in the R2/S3 dashboard, same as the
Gemini/Groq/Adzuna keys earlier.

## Mock Interview Module
`MockInterviewSession` - an AI-conducted turn-based interview. `start_mock_interview`
gives an opening question (calibrated to curated company data if provided,
same rule as everywhere else), `continue_mock_interview` handles each
follow-up turn, `score_mock_interview` reviews the full transcript once
finished and returns a score + feedback. This becomes the THIRD weighted
component of the Readiness Score (`readiness_service.py` - quiz 45%, resume
30%, mock interview 25%, re-normalized when any are missing).
Endpoints: `POST /mock-interview/start`, `POST /mock-interview/{id}/respond`,
`POST /mock-interview/{id}/finish`, `GET /mock-interview/{id}`.

## Rate Limiting
`app/core/rate_limit.py` - a shared `slowapi` limiter, default 120/min per
IP globally, with stricter per-endpoint limits on anything that calls an AI
provider (these cost real quota/credits): prep-plan generate (5/min), roadmap
generate (3/min), resume match (5/min), chat (15/min), admin quiz generate
(10/min), mock interview start/finish (5/min).

## Password Reset
`app/services/email_service.py` sends via SMTP if `SMTP_HOST` is configured;
otherwise `POST /auth/forgot-password` returns the reset token directly in
the response (`dev_reset_token`) for local testing - never rely on that in
production, it exists purely so you can test the flow without setting up
email. `POST /auth/reset-password` validates a short-lived (30 min) JWT
scoped specifically to password resets. The forgot-password response is
intentionally generic either way (doesn't reveal if an email is registered).

## Tests
`tests/` - pytest, covering auth, admin/RBAC guards, the full quiz
generate→approve→take→autograde pipeline, readiness score computation
(including re-normalization when components are missing), the TPO dashboard
flagging logic, and the mock interview flow feeding into readiness. AI calls
are mocked (`tests/conftest.py`) so the suite never costs real API credits.

**Runs against a real Postgres test database, not SQLite** - our models use
Postgres-specific types. Create it once:
```bash
createdb studenthelp_test
```
Set `TEST_DATABASE_URL` in `.env` (defaults to `studenthelp_test` on
localhost). Then:
```bash
cd backend
pytest
```
**This test suite was written and reviewed carefully but could not actually
be executed in the environment these files were generated in (no Postgres
available there) - run it yourself and treat the first run as the real
verification, not a formality.**

Not covered yet: prep-plan/roadmap generation endpoints, resume upload
(needs real PDF bytes + mocked storage), chat, applications, job listings.
Auth/RBAC/quiz/readiness/mock-interview - the highest-value core logic - are
covered.

## What's NOT in this scaffold yet (intentionally, for MVP focus)
- Community/Q&A, notifications (Phase 2/3 features)
- Mobile app (React Native) — build after the web + API loop is validated
- Diagnostic quiz question bank starter content (the generation pipeline
  exists; you need to run `/admin/quiz/generate` + approve questions per
  subject before students can take quizzes)
- Email verification (password reset exists; verifying an email is real on
  signup does not)
- Test coverage for prep-plan/roadmap/resume/chat/applications/job-listings endpoints

## Local setup
```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in DATABASE_URL, GEMINI_API_KEY, GROQ_API_KEY
uvicorn app.main:app --reload
```
Visit `http://localhost:8000/docs` for the interactive API explorer (FastAPI
auto-generates this — use it to test endpoints before building UI).

## Suggested immediate next step
Fill `docs/company_profile_template.json` for 3-5 real companies, then
`POST /api/v1/companies/` to load them, then test
`POST /api/v1/prep-plan/generate` via `/docs` to see a real generated plan
end-to-end before building any frontend screens.
