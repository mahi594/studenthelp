# StudentHelp

StudentHelp is a full-stack student career and placement-support platform. It combines student authentication, job discovery, resume/ATS analysis, personalized roadmaps, preparation plans, AI plan customization/chat, application tracking, notifications, and TPO/admin tools.

---

## 🌐 Live Links
- **Frontend App**: [https://studenthelp-hl9z.vercel.app](https://studenthelp-hl9z.vercel.app)
- **Backend API**: [https://studenthelp-8dhh.onrender.com](https://studenthelp-8dhh.onrender.com)
- **Backend Health**: [https://studenthelp-8dhh.onrender.com/health](https://studenthelp-8dhh.onrender.com/health)
- **GitHub Repository**: [https://github.com/mahi594/studenthelp](https://github.com/mahi594/studenthelp)
- **Interactive OpenAPI/Swagger Docs**: [https://studenthelp-8dhh.onrender.com/docs](https://studenthelp-8dhh.onrender.com/docs)

---

## 🏗️ Technology Stack

### Frontend
- **Framework**: Next.js 14 (App Router)
- **Core**: React, TypeScript
- **Styling**: Modern CSS / Design System
- **Hosting & Deployment**: Vercel

### Backend
- **Framework**: FastAPI (Python 3.12)
- **Server**: Uvicorn
- **ORM & DB Access**: SQLAlchemy 2.0
- **Database Migrations**: Alembic
- **Containerization**: Docker & Docker Compose
- **Hosting & Deployment**: Render

### Database
- **Production**: PostgreSQL on Supabase
- **Local Development**: PostgreSQL in Docker container

### AI Services
- **Generative AI**: Google Gemini & Groq API

### Job Search Integration
- **Provider**: Adzuna Jobs API (server-side proxying for security)

### Email Delivery
- **Production Email**: Google Apps Script Web App + Gmail `MailApp` over HTTPS (bypasses Render Free SMTP port 25/465/587 blocking)
- **Development Fallback**: Local console/token response fallback

### Deployment Architecture
- **GitHub**: Source code repository & automated deployment trigger
- **Vercel**: Production Next.js frontend
- **Render**: Production Dockerized FastAPI backend
- **Supabase**: Managed PostgreSQL database
- **Google Apps Script**: HTTPS transactional email relay

---

## 🧩 System Architecture

```
                                    +---> Google Gemini / Groq API
                                    |
Browser  --->  Next.js (Vercel)  --->  FastAPI (Render)  --->  Adzuna Jobs API
                                    |
                                    +---> Supabase PostgreSQL DB
                                    |
                                    +---> Google Apps Script (HTTPS) ---> Gmail MailApp
```

---

## ✨ Main Features

### Student Portal
- **Authentication**: Registration with college code validation, email verification, and login/logout.
- **Password Security**: Password visibility Eye button (show/hide toggle) on Login, Register, Reset Password, and Change Password pages.
- **Forgot Password**: Password reset email workflow protected against account enumeration.
- **Direct Job Search**: Live job search powered by Adzuna with role, location, and criteria filters without exposing API credentials client-side.
- **ATS Resume Analyzer & Tracker**: Comprehensive resume scan with ATS score, section breakdown (Education, Experience, Skills, Certifications), matched/missing keywords, formatting quality checks, and historical scan progress tracking.
- **LeetCode Practice & Progress Tracker**: Track solved LeetCode problems (Easy, Medium, Hard), receive automated problem recommendations based on quiz weakness, and log completed problems to boost DSA readiness scores.
- **Placement Roadmap Generation**: Long-term career roadmap generation ordered by diagnostic quiz performance.
- **Roadmap AI Customization**: Conversational AI chatbot panel allowing students to request roadmap adjustments (e.g. shift timelines, reorder priorities).
- **Preparation Plan Generation**: Day-wise targeted prep plan tailored to student goals and specific company round structures.
- **Prep Plan AI Customization**: Conversational AI chatbot panel to dynamically update prep plan tasks, daily hours, and topics with server-side progress recalculation.
- **Application Tracker**: Track job applications across stages (`Saved`, `Applied`, `Interviewing`, `Offered`, `Rejected`).
- **Student Notifications**: In-app alerts for quiz reminders, LeetCode recommendations, and TPO intervention updates.

### Admin / TPO Portal
- **Institution Management**: Scope accounts and data isolation by educational institution.
- **User & Admin Creation**: Admin user creation generating secure temporary passwords sent directly to the new user's email address.
- **LeetCode Batch Analytics Tracker**: Institutional view of student LeetCode practice metrics, solved problem counts, and institution-scoped practice activity.
- **TPO Placement Cell Dashboard**: Real-time batch readiness scores, risk category classification, and student status.
- **TPO Targeted Interventions Across Multiple Pages**: Create, manage, and assign custom interventions (workshops, mock tests, 1-on-1 counseling) targeting specific students or low-readiness cohorts across multiple dashboard views and student detail pages.
- **Intervention Pre/Post Impact Tracker**: Measure baseline score vs post-intervention score using real student reassessment data — an intervention that hasn't been reassessed yet is reported as "Post-assessment not completed" (never a fabricated number).
- **Institutional Report Export**: One-click CSV export (`GET /api/v1/tpo/export`) robustly formatted with null-score safeguards.

---

## 🔐 Authentication and Email Workflow

```
1. Registration Flow:
   Student -> Register -> FastAPI -> Account Created -> Verification Token -> Google Apps Script (HTTPS) -> Gmail -> Student Verifies Email

2. Forgot Password Flow:
   Login -> Forgot Password -> Email Submitted -> FastAPI Reset Token -> Google Apps Script (HTTPS) -> Gmail Reset Email -> Student Clicks Link -> New Password Saved

3. Admin-Created User Flow:
   Admin Creates User -> Temporary Password Generated -> Email Dispatched to New User's Email Address -> Forced Change Password on First Login
```

### Google Apps Script Security
1. Receives an HTTPS POST payload from the FastAPI backend.
2. Reads `SHARED_SECRET` securely from **Google Script Properties** (`PropertiesService`).
3. Validates the incoming secret against the request payload.
4. Validates recipient, subject, and body fields.
5. Dispatches email via Gmail `MailApp.sendEmail()`.
6. Returns clean JSON response.
7. Secrets are never exposed to the frontend client or committed to GitHub.

---

## 📁 Repository Structure

```
studenthelp/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/
│   │   │   ├── auth.py
│   │   │   ├── admin.py
│   │   │   ├── job_listings.py
│   │   │   ├── resume.py
│   │   │   ├── roadmap.py
│   │   │   ├── prep_plan.py
│   │   │   └── tpo.py
│   │   ├── core/
│   │   │   └── config.py
│   │   ├── services/
│   │   │   ├── ai_service.py
│   │   │   └── email_service.py
│   │   └── main.py
│   ├── migrations/
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── web/
│   ├── app/
│   │   ├── jobs/
│   │   ├── resume/
│   │   ├── roadmap/
│   │   ├── prep-plan/
│   │   ├── login/
│   │   ├── register/
│   │   └── forgot-password/
│   ├── components/
│   │   ├── Sidebar.tsx
│   │   ├── PlanChatPanel.tsx
│   │   └── PasswordInput.tsx
│   ├── lib/
│   │   └── api.ts
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🐳 Local Docker Setup

### Start Environment
```bash
docker compose up -d
```

### Check Container Status
```bash
docker compose ps
```

### Local URLs
- **Frontend Application**: `http://localhost:3000`
- **Backend API**: `http://localhost:8080`
- **Backend Health Check**: `http://localhost:8080/health`
- **Local PostgreSQL**: `localhost:5434`

### View Container Logs
```bash
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f postgres
```

### Stop Environment
```bash
docker compose stop
```
*(Do **NOT** run `docker compose down -v` unless you explicitly intend to remove the persistent PostgreSQL volume).*

---

## 🗄️ Database & Alembic Migrations

- **Production DB**: PostgreSQL hosted on Supabase.
- **Schema Management**: Managed via Alembic migrations.
- **Docker Startup**: Runs `alembic upgrade head` automatically on container start.

### Local Database Backup Example
```bash
docker exec studenthelp-postgres pg_dump -U studenthelp -d studenthelp > studenthelp_backup.sql
```

---

## 💼 Job Search Integration

- **Route**: `GET /api/v1/job-listings/search`
- **Security**: The backend proxies requests to the Adzuna Jobs API so API keys are never exposed client-side.
- **Docs**: [Adzuna Developer Overview](https://developer.adzuna.com/overview)

---

## 📄 Resume & ATS System

- **Route**: `GET /api/v1/resume/history`
- **Features**: Section breakdown, missing/matched keywords, readability & formatting quality alerts, and historical score progression.

---

## 🗺️ Placement Roadmaps & Preparation Plans

- **Roadmap Customization**: `POST /api/v1/roadmap/{roadmap_id}/customize`
- **Prep Plan Customization**: `POST /api/v1/prep-plan/{plan_id}/customize`
- **AI Customization Panel**: Integrated directly on `/roadmap` and `/prep-plan` pages to process natural language plan adjustments.

---

## 📋 TPO / Admin Export

- **Route**: `GET /api/v1/tpo/export`
- Includes explicit handling for unassessed students and missing scores to prevent CSV generation errors.

---

## 🔗 Useful API Endpoints

- **API Base**: `https://studenthelp-8dhh.onrender.com/api/v1`
- **Authentication**:
  - `POST /auth/register`
  - `POST /auth/login`
  - `GET /auth/me`
  - `POST /auth/forgot-password`
  - `POST /auth/reset-password`
- **Job Search**: `GET /job-listings/search`
- **Resume History**: `GET /resume/history`
- **Roadmap Customization**: `POST /roadmap/{roadmap_id}/customize`
- **Prep Plan Customization**: `POST /prep-plan/{plan_id}/customize`
- **TPO CSV Export**: `GET /tpo/export`

---

## 🚀 Deployment Overview

### Frontend (Vercel)
- **Live URL**: [https://studenthelp-hl9z.vercel.app](https://studenthelp-hl9z.vercel.app)
- **Root Directory**: `web`
- **Build Command**: `npm run build`
- **Docs**: [Vercel Next.js Deployment](https://vercel.com/docs/frameworks/full-stack/nextjs)

### Backend (Render)
- **Live URL**: [https://studenthelp-8dhh.onrender.com](https://studenthelp-8dhh.onrender.com)
- **Dockerfile**: `backend/Dockerfile`
- **Docs**: [Render Web Services](https://render.com/docs/web-services)

### Database (Supabase)
- **Docs**: [Supabase Documentation](https://supabase.com/docs)

### Email Relay (Google Apps Script)
- **Docs**: [Google Apps Script Web Apps Guide](https://developers.google.com/apps-script/guides/web)
- Deployed as Web App (`Execute as: Me`, `Who has access: Anyone`).

---

## 🧪 Testing

### Backend Unit & Integration Tests
```bash
cd backend
python -m pytest
```

### Email & Auth Test Suite
```bash
python -m pytest tests/test_email_verification.py tests/test_auth.py
```

### Frontend Production Build Test
```bash
cd web
npm run build
```

---

## 🔐 Security Checklist
- [x] `.env` files added to `.gitignore`.
- [x] Database credentials, JWT secrets, and AI API keys kept server-side.
- [x] Adzuna credentials proxied server-side.
- [x] Google Apps Script `SHARED_SECRET` stored in Google Script Properties.
- [x] CORS configured for production frontend domain.
- [x] Input validation and password truncation (72-byte bcrypt limit) enforced.

---

## 📄 License
This project is licensed under the MIT License - see the `LICENSE` file for details.
