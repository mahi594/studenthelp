# StudentHelp — Institutional Data Privacy & Governance Policy

## 1. Overview
StudentHelp is an institutional placement readiness & intervention platform designed for college placement cells (TPOs) and students. Protecting student data, maintaining strict multi-tenant isolation, and ensuring transparent processing are core principles of the platform.

---

## 2. Data Collected & Purpose

| Data Category | Specific Data Points | Purpose | Storage & Access |
| :--- | :--- | :--- | :--- |
| **Identity & Account** | Name, institutional email, branch, graduation year, CGPA | User authentication, institution scoping, batch filtering | Scoped to `institution_id`. Accessible by student & authorized TPOs. |
| **Assessment & Readiness** | Quiz answers, readiness scores, 7-dimension metrics, history snapshots | Measuring skill gaps and placement readiness over time | Accessible by student & authorized institutional TPOs. |
| **Resume Submissions** | Uploaded PDF resumes, extracted text, ATS match results | Resume analysis and skill gap recommendations | Stored privately in object storage or local private storage. Never exposed publicly. |
| **Mock Interviews** | Transcripts, AI evaluation indicators (5 dimensions), feedback | Practice evaluation and interview preparation | Accessible strictly by the student. |
| **Audit Logs** | Action, actor ID, resource ID, timestamp, metadata | Security audit trail for institutional compliance | Accessible strictly by TPO / Admin of the same institution. |

---

## 3. Multi-Tenant Scoping & Access Control
- All student data, intervention metrics, export files, and audit logs are bound to an `institution_id`.
- Server-side authorization guards enforce multi-tenant isolation (`TPO A` cannot read or modify `Institution B` data).
- Credentials, raw passwords, JWT tokens, and API secrets are **never** logged in audit records or included in CSV exports.

---

## 4. AI Processing Disclosure
- AI features (Mock Interview Feedback, Resume ATS Analysis, Preparation Plan Generation, Chat Assistance) use AI model APIs.
- Personal identity data is stripped or minimized prior to AI analysis.
- AI evaluation indicators and resume feedback are clearly labeled as **"AI Evaluation Indicators"** and **"AI-Generated Analysis"**. They do not guarantee job selection or replace placement cell human evaluation.
- AI recommendations for target companies remain marked as `AI RECOMMENDED` until explicitly verified by the institution (`is_curated_verified: true`).

---

## 5. Data Retention & Deletion
- Student records are retained for the duration of the academic enrollment period and institutional placement cycle.
- Upon student offboarding or graduation archive requests, placement cells may export institutional analytics and trigger record anonymization/deletion.
- Uploaded resumes can be replaced or deleted by the student at any time via the `/resume` interface.
