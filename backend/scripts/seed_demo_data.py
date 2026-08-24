"""
Institutional Demo Data Seed Script for StudentHelp.

IMPORTANT — how this script is different from a typical demo seed script:
every "before" and "after" number below (the readiness composite score, the
intervention's pre_avg_score/post_avg_score/improvement_delta) is COMPUTED
from the same real engine (`compute_readiness_score` in
app/services/readiness_service.py, and the same latest-score-per-student
logic `tpo.py` uses for interventions) that runs in production - never
hardcoded. If you change WEIGHTS or the readiness formula, re-running this
script will naturally produce different final numbers, because nothing here
is faked.

Populates:
- Demo Institution ("National Institute of Technology (Demo)")
- Demo TPO: demo.tpo@studenthelp.local (Password: DemoTpo123!)
- Demo Student: demo.student@studenthelp.local (Password: DemoStudent123!)
- Demo companies: Amazon, Microsoft, TCS, Infosys
- Diagnostic quiz questions
- A realistic "before" state (weak DSA/Communication/Interview) -> a real
  intervention -> real improved reassessment -> a real, computed impact
  number. The exact +N points is whatever the engine computes, not chosen
  in advance.

Safe to re-run: skips creation of anything that already exists by email/name.
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal, Base, engine
from app.models.user import User, QuizResult
from app.models.company import Company
from app.models.readiness import ReadinessScore
from app.models.quiz_question import QuizQuestion
from app.models.intervention import Intervention
from app.models.mock_interview import MockInterviewSession
from app.models.resume import Resume
from app.api.v1.endpoints.auth import pwd_context
from app.services.readiness_service import compute_readiness_score
from app.services.institution_service import get_or_create_institution
import app.models  # noqa: F401 - registers all models on Base.metadata

DEMO_INSTITUTION_NAME = "National Institute of Technology (Demo)"


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def _compute_and_save_readiness(db, user_id) -> ReadinessScore:
    """Runs the SAME engine production uses and persists the result exactly
    as-is - this is how every readiness number in this seed script is
    produced, never typed in by hand."""
    result = compute_readiness_score(user_id, db)
    score = ReadinessScore(
        user_id=user_id,
        composite_score=result["composite_score"],
        data_status=result["data_status"],
        algorithm_version=result["algorithm_version"],
        breakdown=result["breakdown"],
    )
    db.add(score)
    db.commit()
    db.refresh(score)
    return score


def seed_demo_data():
    db = SessionLocal()
    try:
        print("Seeding institutional demo data (DEMO DATA - clearly fictional accounts/emails)...")
        Base.metadata.create_all(bind=engine)

        # 0. Demo Institution - this is the real tenant boundary every
        # TPO-facing query filters on (see app/api/v1/endpoints/tpo.py).
        institution = get_or_create_institution(db, DEMO_INSTITUTION_NAME)
        db.commit()
        db.refresh(institution)
        print(f"  Institution ready: {institution.name} ({institution.id})")

        # 1. Demo TPO Admin
        tpo_email = "demo.tpo@studenthelp.local"
        tpo_user = db.query(User).filter(User.email == tpo_email).first()
        if not tpo_user:
            tpo_user = User(
                name="Demo TPO — Prof. Rajesh Sharma",
                email=tpo_email,
                hashed_password=get_password_hash("DemoTpo123!"),
                role="tpo_admin",
                college_name=institution.name,
                institution_id=institution.id,
                email_verified=True,
            )
            db.add(tpo_user)
            db.commit()
            db.refresh(tpo_user)
            print(f"  Created TPO Admin: {tpo_email}")
        elif tpo_user.institution_id is None:
            # Re-running against an older DB where this user predates
            # institution_id - backfill it so tenant scoping still works.
            tpo_user.institution_id = institution.id
            db.commit()

        # 2. Demo Student
        student_email = "demo.student@studenthelp.local"
        student_user = db.query(User).filter(User.email == student_email).first()
        if not student_user:
            student_user = User(
                name="Demo Student — Aarav Verma",
                email=student_email,
                hashed_password=get_password_hash("DemoStudent123!"),
                role="student",
                branch="CSE",
                grad_year=2027,
                cgpa="8.1",
                college_name=institution.name,
                institution_id=institution.id,
                email_verified=True,
            )
            db.add(student_user)
            db.commit()
            db.refresh(student_user)
            print(f"  Created Demo Student: {student_email}")
        elif student_user.institution_id is None:
            student_user.institution_id = institution.id
            db.commit()

        # 3. Demo Companies (shared/global catalog, not institution-scoped -
        # a real company recruits across colleges)
        demo_companies = [
            {"name": "Amazon", "roles": ["SDE-1", "Cloud Support Engineer"], "tags": ["Product-Based", "FAANG"],
             "min_cgpa": "7.5", "preferred_branches": ["CSE", "IT", "ECE"],
             "resume_keywords": ["DSA", "System Design", "AWS", "OOP"], "apply_url": "https://amazon.jobs"},
            {"name": "Microsoft", "roles": ["SDE-1"], "tags": ["Product-Based", "FAANG"],
             "min_cgpa": "7.5", "preferred_branches": ["CSE", "IT"],
             "resume_keywords": ["DSA", "C#", "Azure", "OOP"], "apply_url": "https://careers.microsoft.com"},
            {"name": "TCS", "roles": ["Assistant System Engineer"], "tags": ["Service-Based"],
             "min_cgpa": "6.0", "preferred_branches": ["CSE", "IT", "ECE", "Mechanical"],
             "resume_keywords": ["Java", "SQL", "Communication"], "apply_url": "https://www.tcs.com/careers"},
            {"name": "Infosys", "roles": ["Systems Engineer"], "tags": ["Service-Based"],
             "min_cgpa": "6.5", "preferred_branches": ["CSE", "IT", "ECE"],
             "resume_keywords": ["Java", "SQL", "Aptitude"], "apply_url": "https://www.infosys.com/careers"},
        ]
        companies_by_name = {}
        for c in demo_companies:
            existing = db.query(Company).filter(Company.name == c["name"]).first()
            if not existing:
                existing = Company(**c)
                db.add(existing)
                db.commit()
                db.refresh(existing)
                print(f"  Seeded company: {c['name']}")
            companies_by_name[c["name"]] = existing
        amazon = companies_by_name["Amazon"]

        # 4. Approved quiz questions (subjects match the readiness engine's
        # case-insensitive substring matching - see readiness_service.py)
        if not db.query(QuizQuestion).filter(QuizQuestion.subject == "DSA").first():
            db.add_all([
                QuizQuestion(subject="DSA", difficulty="Medium",
                             question_text="What is the time complexity of searching in a balanced Binary Search Tree?",
                             options=["O(n)", "O(log n)", "O(n^2)", "O(1)"], correct_option_index=1,
                             explanation="A balanced BST has height log(n), so lookup is O(log n).", status="approved"),
                QuizQuestion(subject="DSA", difficulty="Easy",
                             question_text="Which data structure operates on a First-In-First-Out (FIFO) basis?",
                             options=["Stack", "Queue", "Tree", "Graph"], correct_option_index=1,
                             explanation="Queues process elements in FIFO order.", status="approved"),
                QuizQuestion(subject="DBMS", difficulty="Medium",
                             question_text="Which normal form eliminates partial key dependencies?",
                             options=["1NF", "2NF", "3NF", "BCNF"], correct_option_index=1,
                             explanation="2NF ensures non-prime attributes are fully functionally dependent on the primary key.",
                             status="approved"),
            ])
            db.commit()
            print("  Seeded approved quiz questions")

        # 5. "BEFORE" state: a realistic weak profile - DSA, Communication,
        # and Interview are the three intended weaknesses for the demo
        # story, matching the spec's example.
        if not db.query(QuizResult).filter(QuizResult.user_id == student_user.id).first():
            db.add_all([
                QuizResult(user_id=student_user.id, subject="DSA", score_percent=38),
                QuizResult(user_id=student_user.id, subject="DBMS", score_percent=64),
                QuizResult(user_id=student_user.id, subject="OS", score_percent=60),
                QuizResult(user_id=student_user.id, subject="Aptitude", score_percent=58),
            ])
            db.commit()
            print("  Seeded initial (weak) quiz results")

        if not db.query(MockInterviewSession).filter(
            MockInterviewSession.user_id == student_user.id, MockInterviewSession.status == "completed"
        ).first():
            db.add(MockInterviewSession(
                user_id=student_user.id,
                role_or_subject="SDE-1",
                company_id=amazon.id,
                transcript=[
                    {"role": "interviewer", "content": "Walk me through how you'd design a rate limiter."},
                    {"role": "candidate", "content": "I'd use a token bucket... (demo transcript, truncated)"},
                ],
                status="completed",
                overall_score=42,  # intentionally weak, for the "before" story
                feedback={"strengths": ["Clear communication of basic ideas"],
                          "improvements": ["Needs deeper system design fundamentals", "Struggled under follow-up questions"]},
                completed_at=datetime.utcnow() - timedelta(days=10),
            ))
            db.commit()
            print("  Seeded initial (weak) mock interview")

        if not db.query(Resume).filter(Resume.user_id == student_user.id).first():
            db.add(Resume(
                user_id=student_user.id,
                file_url="https://example.com/demo-resume-placeholder.pdf",  # placeholder - demo only, not a real upload
                target_company_id=amazon.id,
                match_result={"match_score_percent": 58, "missing_keywords": ["System Design", "AWS"],
                              "meets_cgpa_cutoff": True},
            ))
            db.commit()
            print("  Seeded initial resume match (demo placeholder, not a real uploaded file)")

        before_score = _compute_and_save_readiness(db, student_user.id)
        print(f"  Computed BEFORE readiness: {before_score.composite_score} "
              f"(data_status={before_score.data_status}, algorithm_version={before_score.algorithm_version})")

        # 6. A real intervention, targeting the demo student, with a REAL
        # pre_avg_score pulled from the ReadinessScore just computed above -
        # exactly like tpo.create_intervention does.
        existing_intervention = db.query(Intervention).filter(
            Intervention.title == "7-Day Intensive DSA & Problem Solving Workshop",
            Intervention.institution_id == institution.id,
        ).first()
        if not existing_intervention:
            intervention = Intervention(
                title="7-Day Intensive DSA & Problem Solving Workshop",
                skill_topic="DSA",
                intervention_type="workshop",
                target_branch="CSE",
                target_student_ids=[str(student_user.id)],
                status="active",
                pre_avg_score=before_score.composite_score,
                eligible_count=1,
                pre_assessed_count=1 if before_score.composite_score is not None else 0,
                institution_id=institution.id,
                created_by_user_id=tpo_user.id,
            )
            db.add(intervention)
            db.commit()
            db.refresh(intervention)
            print(f"  Created intervention (pre_avg_score={intervention.pre_avg_score}, from real data)")

            # 7. "AFTER" state: the student genuinely improves their weakest
            # areas (DSA, communication signal via a better mock interview,
            # resume analysis) and reassesses. Every one of these numbers is
            # just a plausible improved score - the resulting composite,
            # post_avg_score, and improvement_delta are computed, not typed.
            db.add_all([
                QuizResult(user_id=student_user.id, subject="DSA", score_percent=74),
                QuizResult(user_id=student_user.id, subject="Aptitude", score_percent=71),
            ])
            db.add(MockInterviewSession(
                user_id=student_user.id,
                role_or_subject="SDE-1",
                company_id=amazon.id,
                transcript=[
                    {"role": "interviewer", "content": "Walk me through how you'd design a rate limiter."},
                    {"role": "candidate", "content": "I'd use a token bucket algorithm with a sliding window... (demo transcript, truncated)"},
                ],
                status="completed",
                overall_score=76,
                feedback={"strengths": ["Structured system design answer", "Clear trade-off discussion"],
                          "improvements": ["Could go deeper on distributed rate limiting"]},
                completed_at=datetime.utcnow(),
            ))
            db.commit()

            after_score = _compute_and_save_readiness(db, student_user.id)
            print(f"  Computed AFTER readiness: {after_score.composite_score}")

            # Complete the intervention using the SAME latest-score-per-student
            # logic tpo.py's complete_intervention endpoint uses - this is
            # what makes improvement_delta a real, reproducible number.
            intervention.status = "completed"
            intervention.completed_at = datetime.utcnow()
            intervention.post_avg_score = after_score.composite_score
            intervention.reassessed_count = 1 if after_score.composite_score is not None else 0
            if intervention.pre_avg_score is not None and intervention.post_avg_score is not None:
                intervention.improvement_delta = intervention.post_avg_score - intervention.pre_avg_score
            db.commit()
            print(f"  Completed intervention: before={intervention.pre_avg_score}, "
                  f"after={intervention.post_avg_score}, "
                  f"improvement={intervention.improvement_delta} points (COMPUTED, not hardcoded)")

        print("==================================================")
        print("Demo data seeded successfully.")
        print(f"Institution:  {institution.name}")
        print("Student login: demo.student@studenthelp.local / DemoStudent123!")
        print("TPO login:     demo.tpo@studenthelp.local / DemoTpo123!")
        print("==================================================")

    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()
