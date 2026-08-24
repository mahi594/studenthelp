# StudentHelp — Full Functionality Reference

This document describes everything currently built in the scaffold: what each
feature does, how it works end-to-end, the API endpoints involved, and what's
intentionally left for later. Use this as the single source of truth for
"what does this app actually do right now."

---

## 1. Core Design Principle

**Company facts are always curated by humans (admins/seniors). AI only
personalizes, sequences, and calibrates — it never invents facts about what a
specific company asks in its interview process.**

This rule is enforced in every AI-touching feature below (prep plans,
roadmaps, resume matching, quiz generation, the chat bot). Anywhere the AI is
given a company's data, the prompt explicitly instructs it not to add new
factual claims beyond what's stored in the curated `Company`/`Round`
database rows.

**Readiness Score is deliberately NOT AI-computed** — it's a plain weighted
formula — so the number stays transparent and trustworthy enough for a TPO
dashboard to rely on.

---

## 2. User Roles

| Role | Can do |
|---|---|
| `student` (default on registration) | Everything student-facing: quizzes, plans, roadmap, resume, chat, their own readiness score |
| `admin` | Everything a student can, plus: add/edit companies, generate & approve quiz questions, view the TPO dashboard |
| `tpo_admin` | View the TPO dashboard only (placement-cell / institutional role, doesn't need content-curation access) |

There's no self-serve way to become admin/tpo_admin (by design). Promote a
user manually:
```sql
UPDATE users SET role = 'admin' WHERE email = 'someone@example.com';
```

---

## 3. Feature-by-Feature Breakdown

### 3.1 Authentication
- `POST /api/v1/auth/register` — create an account (student by default)
- `POST /api/v1/auth/login` — OAuth2 password flow, returns a JWT bearer token
- All other endpoints (except register/login) require `Authorization: Bearer <token>`

### 3.2 Curated Company Profiles
The factual backbone of the whole app. An admin manually enters:
- Company name, roles hired for, tags (e.g. "product-based")
- Resume filter criteria: min CGPA, preferred branches, resume keywords
- **Rounds**: ordered list of interview stages (OA, Technical, HR, etc.), each with subjects tested, difficulty, notes
- **Questions**: real past questions tied to a round, with attribution (`senior_submitted`, `curated`, or `ai_generated`)
- **Learning Resources**: curated links (video/article/notes) per subject/topic, ranked

Endpoints: `GET /companies/` (supports `?name=` and `?role=` search), `GET /companies/{id}`, `POST /companies/` (admin only)

### 3.3 Diagnostic Quiz (AI-generated, admin-approved)
This is the "skill signal" that drives personalization everywhere else.

**Admin side:**
1. `POST /admin/quiz/generate` — AI drafts N multiple-choice questions for a subject (optionally calibrated to a company's curated round data for difficulty/style — never invents company facts). Questions land as `pending_approval`.
2. `GET /admin/quiz/pending` — review drafts
3. `POST /admin/quiz/{id}/approve` or `/reject` — only approved questions ever reach students

**Student side:**
1. `GET /quiz/questions?subject=DSA` — fetch a shuffled set of approved questions (correct answers withheld)
2. `POST /quiz/submit-answers` — submit answers, auto-graded server-side, `score_percent` computed and saved as a `QuizResult`
3. `POST /quiz/submit` — manual override to directly log a score (useful for testing, bulk import, or quizzes taken outside the app)

### 3.4 Resume Matching
- `POST /resume/upload-and-match` — upload a PDF resume + target company. Text is extracted (`pypdf`), then AI compares it against that company's curated `resume_keywords`/`min_cgpa`/`preferred_branches` only (no invented requirements). Returns a match score, missing keywords, and specific suggestions.

### 3.5 Prep Plan (short-term, company-specific)
- `POST /prep-plan/generate` — given a target company + days remaining, combines: curated round/subject data for that company + the student's quiz scores (weak subjects prioritized) + curated learning resources → AI sequences this into a day-wise task list (JSON, not free text, so the UI renders it as a checklist).
- `GET /prep-plan/{id}` — fetch a previously generated plan
- Requires at least one `QuizResult` to exist first (won't generate a plan on zero signal)

### 3.6 Roadmap (long-term, performance-driven)
- `POST /roadmap/generate` — a multi-month plan (e.g. semester-wise) driven purely by quiz score trends, not tied to a single company countdown. Meant to be re-generated periodically as new quiz results come in.
- `GET /roadmap/user/latest`, `GET /roadmap/{id}`

### 3.7 AI Chat Bot
- `POST /chat/ask` — general placement/study Q&A with persistent conversation history (`ChatMessage` table). If a `company_id` is passed, the system prompt is restricted to that company's curated round data only; if no curated data exists, the bot says so rather than guessing. Off-topic questions are redirected back to placement-prep scope.
- `GET /chat/history`

### 3.8 Readiness Score (the core differentiator)
- `POST /readiness/compute` — computes a composite 0-100 score from quiz mastery average (60% weight) + resume match average (40% weight), saved as a new timestamped snapshot (not overwritten — this builds a trend line)
- `GET /readiness/latest` — most recent score (auto-computes on first call if none exists)
- `GET /readiness/history` — full trend, for charting over time

### 3.9 TPO Dashboard (institutional differentiator)
- `GET /tpo/dashboard` (role: `admin` or `tpo_admin`) — batch-wide view:
  - Total students, how many have a readiness score yet
  - Batch average score
  - **Flagged students**: anyone with `composite_score < 50` (threshold set in `tpo.py`)
  - Branch-wise average breakdown
  - Full list of all students with their latest score
  - Optional `?branch=` / `?grad_year=` filters for a focused view

This is what turns the app from "another student cram app" into a
college-integrated system — see `docs/architecture.md` for the competitive
reasoning behind this.

### 3.10 Job Listings (live openings, auto-fetched)
- **On hold per product decision** — built (Adzuna integration) but not
  wired into the frontend or called automatically, to avoid depending on a
  scraping/aggregator source for now. Endpoints exist
  (`POST /job-listings/refresh`, `GET /job-listings/`) if you want to revisit
  this later; see `docs/architecture.md` for the original design.

### 3.11 Applications (applied / not-applied tracking)
- `Company.apply_url` — admin sets a direct application link per company
  when creating/editing it (`POST /companies/`, field `apply_url`)
- `POST /applications/mark` — student marks their status for a company
  (`not_applied` / `applied` / `interviewing` / `offered` / `rejected`).
  Upserts — one row per (student, company) pair.
- `GET /applications/` — student's full application list, used to build a
  `{company_id: status}` map on the frontend
- On the Companies page (`web/app/companies/page.tsx`), each card shows the
  apply link (opens in a new tab) and an "Applied" badge once marked

### 3.12 AI Provider Strategy
All AI calls go through `app/services/ai_service.py`. Gemini
(`gemini-1.5-flash`) is primary — free daily quota, good for development.
If Gemini's quota or rate limit is hit specifically, calls automatically fall
back to Groq (`llama-3.3-70b-versatile`). Genuine bugs (bad prompts, auth
failures) are never silently masked by the fallback — only quota/rate-limit
errors trigger it.

### 3.13 Mock Interview Module
- `POST /mock-interview/start` (role/subject + optional company for
  calibration) — AI opens with a question
- `POST /mock-interview/{id}/respond` — student answers, AI asks a follow-up,
  full turn stored in `transcript`
- `POST /mock-interview/{id}/finish` — AI scores the full transcript
  (0-100 + strengths/improvements), session marked completed, **Readiness
  Score is immediately recomputed** so the result counts right away
- Becomes the third weighted Readiness Score component (see 3.8) — weights
  are now quiz 45%, resume 30%, mock interview 25%, re-normalized when any
  are missing

### 3.14 Rate Limiting
`app/core/rate_limit.py` — global default 120/min per IP, with stricter
per-endpoint limits on anything AI-calling (these burn real quota/credits):
prep-plan generate (5/min), roadmap generate (3/min), resume match (5/min),
chat (15/min), admin quiz generate (10/min), mock interview start/finish (5/min).

### 3.15 Password Reset
- `POST /auth/forgot-password` — sends a reset email via SMTP if configured;
  otherwise returns the token directly in the response (`dev_reset_token`)
  for local testing. Always returns a generic message either way (doesn't
  reveal whether an email is registered).
- `POST /auth/reset-password` — validates a 30-minute JWT scoped specifically
  to password resets, updates the password.
- Email verification on signup is **not** built — only reset is.

### 3.16 Automated Tests
`tests/` (pytest) — covers auth, admin/RBAC guards, the full quiz
generate→approve→take→autograde pipeline, readiness score computation and
re-normalization, TPO dashboard flagging, and mock interview → readiness
integration. AI calls are mocked, so running tests costs no real API credits.
**Runs against a real Postgres test database** (`TEST_DATABASE_URL`), not
SQLite — our models use Postgres-specific column types. See
`docs/architecture.md` for setup. Not yet covered: prep-plan/roadmap
generation, resume upload, chat, applications, job listings.

---

## 4. Data Model Summary

| Table | Purpose |
|---|---|
| `users` | Accounts; `role` field gates admin/TPO access |
| `companies`, `rounds`, `questions`, `learning_resources` | The curated facts layer |
| `quiz_questions` | AI-drafted, admin-approved MCQ bank |
| `quiz_results` | Per-subject scores (from quiz or manual entry) — the core skill signal |
| `resumes` | Uploaded resume text + AI match result per company + S3/R2 storage key |
| `prep_plans` | Generated short-term, company-specific day-wise plans |
| `roadmaps` | Generated long-term, performance-driven phase plans |
| `chat_messages` | Chat bot conversation history |
| `readiness_scores` | Timestamped composite score snapshots |
| `job_listings` | Live openings fetched from Adzuna, with apply link + expiry (on hold) |
| `applications` | Per-student applied/not-applied status per company |
| `mock_interview_sessions` | AI interview transcript, score, and feedback |

---

## 5. What's Explicitly NOT Built Yet

- **Mobile app (React Native)** — not started
- **Community/peer Q&A, notifications** — Phase 2/3 features, not started
- **Starter quiz question content** — the generation pipeline works, but you need to actually run `/admin/quiz/generate` + approve questions per subject before students can take any quiz
- **Email verification on signup** — password reset exists; verifying a new account's email is real does not
- **Test coverage** for prep-plan/roadmap generation, resume upload, chat, applications, job listings (auth/RBAC/quiz/readiness/mock-interview are covered)

---

## 6. Suggested Order for What's Left

1. Run `pytest` yourself and fix anything that surfaces — it was written carefully but never actually executed (no Postgres in the environment it was built in)
2. Populate real quiz content for 3-5 subjects via the generate+approve flow
3. Extend test coverage to the remaining endpoints
4. Mobile app
