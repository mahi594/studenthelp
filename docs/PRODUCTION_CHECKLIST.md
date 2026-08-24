# StudentHelp Production Hardening — Checklist

Living document. Update the status + notes for a phase whenever you actually
change and test something — never mark PASS because code merely exists.
Last updated: 2026-08-23 (session 5).

## Session 5 — headline finding

Every prior session's "117/117 tests pass against real Postgres" claim in
this document, while true, was less meaningful than it sounded: the test
suite's schema is built with `Base.metadata.create_all()` **from the
models**, never from the real Alembic migrations. This session ran the
actual migration chain against a real, empty Postgres database (not just
`alembic upgrade head --sql` for syntax-checking, but a real `alembic
upgrade head` followed by real ORM inserts via `scripts/seed_demo_data.py`)
and found **5 real, previously-invisible bugs** that would have broken the
application immediately in any real deployment:

1. `users.target_company_ids`, `companies.roles/tags/preferred_branches/resume_keywords`, `rounds.subjects_tested`, `questions.tags`, `qa_questions.tags` were all declared `JSON` on the model but migrated as real Postgres `ARRAY` columns — every insert against any of them failed with `psycopg2.errors.InvalidTextRepresentation: malformed array literal`. This would have broken **user registration itself**.
2. `companies.source_type/verified_by/verified_at/confidence` — columns the model declares (the exact fields Phase 10 needs) were never migrated at all.
3. `readiness_scores.algorithm_version` — never migrated. Every readiness computation would fail outright.
4. `roadmaps.target_company_ids/target_company_names` — never migrated. Every `POST /roadmap/generate` would fail.

All fixed via model corrections + new migration `c3f7e9a21d5b`, verified by dropping/recreating the Postgres database from scratch multiple times and running the seed script + full test suite against it. A **permanent regression test** (`tests/test_migration_schema_drift.py`) now runs the real migration chain and diffs every model column (including a type-family check, ARRAY vs JSON specifically) against what actually got created — verified to actually catch this exact bug class by deliberately reintroducing one and watching the test fail, then confirming it passes with the fix restored.

Also rewrote `scripts/seed_demo_data.py`: the old version hardcoded `pre_avg_score=48, post_avg_score=66, improvement_delta=18` directly into the database — literally the exact fabrication pattern the original spec named as forbidden. The new version computes readiness via the real `compute_readiness_score()` engine and completes the intervention via the same latest-score-per-student logic `tpo.py` uses, so the "+N points" story is whatever the engine actually computes (a real run produced +9, not a fixed +18).


Legend: ✅ PASS (implemented + tested)  🟡 PARTIAL (some done, gaps remain)  ❌ FAIL (not started / broken)

| 6 | TPO student filtering | ✅ | **Frontend wired this session.** `/admin/tpo-dashboard` now sends all the new filter params (CGPA/readiness range, risk, assessment/interview status, skill topic, page) to the server and paginates through `total_pages`/`page` from the response, instead of fetching everything and filtering client-side. Verified with a real `next build` (see Phase 20/27 below) - compiles clean, no type errors. |
| 7 | TPO student detail page | ✅ | **New frontend page this session:** `/admin/tpo-dashboard/students/[id]` consumes `GET /tpo/students/{id}` and renders all 7 sections from the spec (profile, readiness+trend+algorithm version, skill breakdown, assessment history, target companies with real resume-match data, preparation, mock interviews, interventions). Student names in the roster table now link here. Verified via a real `next build` - compiles clean. Also fixed a fabrication bug found while wiring this: the dashboard's intervention card was rendering "+0 pts Improvement" when `improvement_delta` was `null` (no reassessment yet) - now renders "Post-assessment not completed" with eligible/reassessed counts, matching Phase 2's required wording exactly. |
| 8 | TPO dashboard redesign | ❌ | Not started (the widgets/layout described in the spec - readiness distribution, skill gaps, branch performance as a distinct widget from what exists, etc). |
| 9 | Student dashboard UX | 🟡 | Unchanged from session 2. |
| 10 | Target company experience | ❌ | Not started. |
| 11 | Preparation plan | ❌ | Not audited. |
| 12 | Mock interview | 🟡 | Unchanged from session 2. |
| 13 | Resume analysis | 🟡 | Unchanged from session 3. |
| 14 | Exports | 🟡 | Unchanged from session 2. |
| 15 | Audit logging | ❌ | Not started. |
| 16 | Authorization audit (all endpoints) | ✅ | Unchanged from session 3 - full sweep done, one real bug (unauthenticated roadmap read) found and fixed. |
| 17 | Database migrations | ✅ | **Session 4** verified the chain runs end-to-end against real Postgres. **Session 5 went further and found the chain was incomplete**: 5 real model/migration drift bugs (see headline finding above) that column-existence-only inspection in session 4 didn't catch because it never actually tried inserting data. Fixed via migration `c3f7e9a21d5b` and now covered by a permanent automated test, not just manual `psql` inspection. |
| 18 | Demo data | ✅ | **Done this session.** `scripts/seed_demo_data.py` rewritten: creates a real `Institution` row (previously it set `college_name` only, never `institution_id` — would have been invisible to every institution-scoped query), and computes readiness/intervention numbers via the real engine instead of hardcoding `pre_avg_score=48, post_avg_score=66, improvement_delta=18` as the old script did. Verified by actually running it against real Postgres (produced a real, non-fabricated `+9` in one run). |
| 19 | Frontend polish | ❌ | Beyond the honesty-fix work, no dedicated visual polish pass. |
| 20 | Responsive testing | ❌ | Still not done - `next build` was run (proves the app compiles and type-checks) but no dev server was started and no viewport/breakpoint testing was done. |
| 21 | Security (secrets) | ✅ | Unchanged from session 3. |
| 22 | File upload security | ✅ | Unchanged from session 3. |
| 23 | AI safety / cost control | 🟡 | Unchanged from session 3. |
| 24 | Error handling | 🟡 | Unchanged from session 3. |
| 25 | Health checks | ✅ | Unchanged from session 3 (confirmed by reading the Dockerfile/compose config, not yet by hitting a running container's `/health` over HTTP - Docker itself isn't installed in this sandbox, only Postgres). |
| 26 | Performance (N+1, pagination) | 🟡 | Unchanged from session 3. |
| 27 | Docker | 🟡 | Postgres 16 continues to run standalone in this sandbox across sessions 4-5, giving strong confidence in the migration/data layer specifically. `docker` itself (the daemon/binary) is still not installed here, so `docker compose up` / container networking / the backend's `alembic upgrade head && uvicorn ...` startup command / the curl-based HEALTHCHECK have still never actually been exercised end-to-end in THIS environment. Given session 5 found 5 real bugs that only surfaced by actually running things against real Postgres (not just inspecting config), the same caution applies here: Dockerfiles/compose looking correct on inspection is not sufficient evidence, so this stays 🟡 until `docker compose up` is actually run somewhere. |
| 28 | End-to-end acceptance test | ❌ | Still not run manually end-to-end through a browser. Automated coverage exists for the security-relevant subset (Phase 29). |
| 29 | Tests | ✅ | **118/118 passing against real PostgreSQL 16** (117 + the new `test_migration_schema_drift.py`, which is itself verified to actually catch drift, not just always pass - confirmed by deliberately reintroducing a bug and watching it fail). `npm install` + `npm run build` also succeeded cleanly for the frontend (session 4). `npm test`/E2E frontend tests still not run (none appear to exist in the project). |
| 30 | Documentation | ✅ | **Updated this session.** `README.md` (setup steps now include `alembic upgrade head`, corrected test count, removed the "+X points" phrasing that implied a fixed number), `docs/SECURITY.md` (rewritten to describe what's actually enforced, added the schema-drift finding), `docs/DEPLOYMENT.md` (added a "Verification Status" section stating plainly what has and hasn't been run). `docs/PRODUCT.md` not yet reviewed. |
| 31 | Final product check | 🟡 | Updated below. |

## Phase 31 answers (honest, as of session 5)

1. Is tenant isolation enforced server-side? **Yes**, for every institution-owned resource identified so far.
2. Can one institution access another's data? **No** - tested against real Postgres.
3. Can an arbitrary user ID access another user's data? **No**, for everything audited (Phase 16).
4. Can intervention improvement be fabricated? **No** - tested, and the demo seed script no longer hardcodes it either (was the exact "+18" pattern the original spec named as forbidden).
5. Are missing assessments shown as missing instead of fake scores? **Yes**, in the readiness engine, student dashboard, and TPO student detail page.
6. Does TPO filtering actually work? **Yes** - backend tested, frontend wired and builds cleanly.
7. Does TPO student detail work? **Yes** - backend tested, frontend built and compiles cleanly.
8. Does CSV export contain useful readiness dimensions? **Yes.**
9. Does the student dashboard clearly show next actions? Partially - unchanged.
10. Does the company workflow work? Not touched.
11. Does reassessment actually change readiness? **Yes**, tested end-to-end against real Postgres, including via the real demo seed script.
12. Does Docker work from a clean environment? **Still unverified** - the `docker` binary/daemon itself is not available in this sandbox. This is now the single largest remaining verification gap, made more important by session 5's finding that "looks correct on inspection" was not sufficient for the migration layer either.
13. Do migrations work from an empty database? **Yes, and now more rigorously than before** - not just schema inspection, but real ORM inserts via the demo seed script, plus a permanent automated test that would have caught every bug found this session.
14. Do tests pass? **Yes - 118/118**, against real Postgres.
15. Are secrets removed? **Yes.**
16. Are production errors hidden? **Mostly** - one real leak found and fixed.
17. Are all important APIs authorized? **Yes**, full sweep done.

## What to do in the next session (priority order)

1. **Phase 27**: if a future environment has `docker` available, run the actual `docker compose down && build --no-cache && up -d && ps && logs` sequence. Given session 5's findings, do NOT skip this by reasoning "the config looks right" - actually run it.
2. **Phase 8**: TPO dashboard visual redesign (the specific widget layout from the spec).
3. **Phase 15**: audit logging - no audit-log table/model exists yet.
4. **Phase 10**: now that `companies.source_type/verified_by/verified_at/confidence` actually exist in the DB (session 5), wire them into the company endpoints/schema/frontend for the Verified/Student-Reported/AI-Recommended distinction the spec asks for - the groundwork is now real, but nothing reads or writes these columns yet.
5. Phases 9, 11-13 (student-facing UX, prep plan, mock interview dimensions, resume analysis UI), 19-20 (frontend polish, responsive breakpoint testing with a running dev server), 26 (broader N+1 audit beyond the TPO dashboard).
6. `docs/PRODUCT.md` still needs a review pass for accuracy.
