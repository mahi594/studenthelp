# StudentHelp — Institutional Product & Architecture Overview

StudentHelp is an institutional placement-readiness, personalized preparation, and intervention SaaS platform designed for Students and Placement Cells (TPOs).

---

## 1. Product Capabilities

### For Students
1. **Placement Readiness Index (v1)**:
   - A 7-dimensional evaluation engine measuring student readiness across:
     - DSA & Problem Solving (25%)
     - CS Fundamentals: DBMS, OS, CN (15%)
     - Aptitude & Logical Reasoning (15%)
     - Resume Quality & ATS Match (15%)
     - Communication Skills (10%)
     - Technical Interviewing (10%)
     - Target Company Preparation (10%)
   - Automatic weight re-normalization when signals are partially available.
   - Identified top 3 skill gaps and dynamic ladder visualization.

2. **Personalized Day-Wise Prep Plans**:
   - Generates sequenced day-wise study plans matching target company recruitment rounds.
   - Prioritizes weak topics without inventing non-curated company facts.

3. **Interactive Mock Interviews**:
   - Turn-by-turn AI interviewer probing technical & behavioral answers.
   - Evaluates overall interview performance score, strengths, and actionable improvements.

4. **Company Intelligence & Applications**:
   - Recruitment round breakdowns, CGPA cutoffs, and verified provenance badges.
   - Direct application tracking and status history.

---

### For Placement Cells & TPOs
1. **Batch Readiness Analytics**:
   - Real-time batch average score, total assessed count, and branch-wide performance distribution.

2. **Risk Category Classification**:
   - Automatically segments students into:
     - *Interview Ready* (Score 80+)
     - *On Track* (Score 65-79)
     - *Needs Attention* (Score 50-64)
     - *Needs Significant Support* (Score <50)
     - *Not Assessed*

3. **Targeted Interventions & Pre/Post Impact Tracking**:
   - TPOs create workshops, assignment suites, or mock tests for at-risk cohorts.
   - Automatically measures baseline score vs post-intervention score (+X points improvement story).

4. **One-Click Institutional CSV Export**:
   - Downloads complete student batch roster with contact info, branch, graduation year, readiness score, and risk tier for placement committee reports.

---

## 2. Multi-Tenancy & Data Model Architecture

- **`Institution`**: Stores college branding, domain, custom placement cell title, and academic year settings.
- **`User`**: Multi-tenant scoped with `institution_id`, `role` (`student`, `tpo_admin`, `admin`), `branch`, and `grad_year`.
- **`Company`**: High-integrity company records with provenance fields (`source_type`, `verified_by`, `verified_at`, `confidence`).
- **`ReadinessScore`**: Versioned snapshot (`algorithm_version="v1"`) with 7-dimension breakdown.
- **`Intervention`**: Tracks target student cohorts, pre/post average scores, and improvement delta.
