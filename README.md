# StudentHelp — Institutional Placement Readiness & Intervention Platform

StudentHelp is a production-ready, secure, institutional placement-readiness and intervention SaaS platform designed for Students and Institutional Placement Cells (TPOs).

---

## Key Capabilities

### For Students
- **Placement Readiness Index (v1)**: 7-dimensional evaluation engine (DSA, CS Fundamentals, Aptitude, Resume, Communication, Technical Interviewing, Company Prep).
- **Personalized Day-Wise Prep Plans**: Sequence study plans aligned with target company recruitment rounds.
- **Interactive AI Mock Interviews**: Turn-by-turn technical/behavioral interview practice with score breakdowns.
- **Target Company Intelligence**: Recruitment rounds, CGPA cutoffs, and verified provenance badges.

### For Placement Cells (TPOs)
- **Batch Readiness Analytics**: Real-time batch average score, total assessed count, and branch-wide performance distribution.
- **Risk Category Classification**: Automatic student segmentation (`Interview Ready`, `On Track`, `Needs Attention`, `Needs Significant Support`, `Not Assessed`).
- **Targeted Interventions & Pre/Post Impact Measurement**: Measure baseline score vs post-intervention score, using each student's real reassessment data — an intervention that hasn't been reassessed yet is shown as "Post-assessment not completed," never a guessed number.
- **One-Click Institutional CSV Export**: Download complete student batch rosters for placement committee reports.

---

## Quick Start — Demonstration Seed Data

### 1. Backend Setup
```bash
cd backend
python -m venv venv
# On Windows: venv\Scripts\activate
# On Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Set DATABASE_URL in .env to a real Postgres instance, then:
alembic upgrade head
python -m pytest   # Run full test suite (118 tests)
python scripts/seed_demo_data.py
uvicorn app.main:app --reload
```

### 2. Demo Accounts (Created by `seed_demo_data.py`)
- **Student Demo Account**: `demo.student@studenthelp.local` / `DemoStudent123!`
- **TPO Admin Account**: `demo.tpo@studenthelp.local` / `DemoTpo123!`

### 3. Frontend Web Setup
```bash
cd web
npm install
npm run dev
```
Access app at `http://localhost:3000`.

---

## Documentation

- [`docs/PRODUCT.md`](docs/PRODUCT.md) — Institutional architecture & product breakdown
- [`docs/SECURITY.md`](docs/SECURITY.md) — Security guardrails, secret protection & RBAC
- [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) — Production deployment & Docker guide
