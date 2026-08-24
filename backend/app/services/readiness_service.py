"""
Placement Readiness Index (v1) Engine.

Transparent, deterministic, multi-dimensional evaluation of student readiness.
Dimensions (Weights sum to 1.0):
- DSA (0.25)
- CS Fundamentals (0.15)
- Aptitude (0.15)
- Communication (0.10)
- Resume (0.15)
- Technical Interview (0.10)
- Company Preparation (0.10)

Weights are re-normalized if specific signals are absent so absence does not unfairly penalize a student.
"""
from statistics import mean
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.models.user import QuizResult
from app.models.resume import Resume
from app.models.mock_interview import MockInterviewSession
from app.models.prep_plan import PrepPlan

ALGORITHM_VERSION = "v1"

WEIGHTS = {
    "dsa": 0.25,
    "cs_fundamentals": 0.15,
    "aptitude": 0.15,
    "communication": 0.10,
    "resume": 0.15,
    "interview": 0.10,
    "company_prep": 0.10,
}


def compute_readiness_score(user_id, db: Session) -> Dict[str, Any]:
    """Computes the 7-dimension Placement Readiness Index (v1)."""

    quiz_results = db.query(QuizResult).filter(QuizResult.user_id == user_id).all()

    # 1. DSA Score
    dsa_quizzes = [q.score_percent for q in quiz_results if q.subject and "dsa" in q.subject.lower()]
    dsa_score = mean(dsa_quizzes) if dsa_quizzes else None

    # 2. CS Fundamentals Score (DBMS, OS, CN, OOP)
    cs_subjects = ["dbms", "os", "cn", "oop", "computer networks", "operating systems"]
    cs_quizzes = [q.score_percent for q in quiz_results if q.subject and any(s in q.subject.lower() for s in cs_subjects)]
    cs_score = mean(cs_quizzes) if cs_quizzes else None

    # 3. Aptitude Score
    aptitude_quizzes = [q.score_percent for q in quiz_results if q.subject and "aptitude" in q.subject.lower()]
    aptitude_score = mean(aptitude_quizzes) if aptitude_quizzes else None

    # NOTE: we deliberately do NOT fall back an uncategorized/general quiz
    # average into dsa_score / cs_score / aptitude_score. A quiz that isn't
    # tagged with a matching `subject` is not evidence about that specific
    # dimension - treating it as if it were would mislabel a student's real
    # skill gaps (e.g. showing "DSA: 72%" for a student who has never taken
    # a DSA quiz). If a dimension has no matching category data, it stays
    # None and is reported as "Not Assessed" below.

    # 4. Resume Score - ONLY from an actual AI match_result. Simply having
    # uploaded a resume is not a score; an unanalyzed resume stays None
    # ("Not Analyzed"), never a guessed 70.
    resumes = (
        db.query(Resume)
        .filter(Resume.user_id == user_id, Resume.match_result.isnot(None))
        .all()
    )
    resume_scores = [
        r.match_result.get("match_score_percent")
        for r in resumes
        if r.match_result and r.match_result.get("match_score_percent") is not None
    ]
    resume_score = mean(resume_scores) if resume_scores else None

    # 5. Technical Interview Score & 6. Communication Score
    completed_interviews = (
        db.query(MockInterviewSession)
        .filter(
            MockInterviewSession.user_id == user_id,
            MockInterviewSession.status == "completed",
            MockInterviewSession.overall_score.isnot(None),
        )
        .all()
    )
    interview_score = mean([s.overall_score for s in completed_interviews]) if completed_interviews else None
    
    # Extract communication feedback from interviews if available, else fallback
    comm_scores = []
    for s in completed_interviews:
        if s.feedback and isinstance(s.feedback, dict) and "communication_score" in s.feedback:
            comm_scores.append(s.feedback["communication_score"])
    comm_quizzes = [q.score_percent for q in quiz_results if q.subject and "communication" in q.subject.lower()]
    all_comm = comm_scores + comm_quizzes
    # No fallback to interview_score here either - communication is its own
    # dimension and must come from actual communication signal (a tagged
    # quiz, or explicit communication_score feedback from a scored mock
    # interview), not borrowed wholesale from the unrelated interview score.
    communication_score = mean(all_comm) if all_comm else None

    # 7. Company Prep Progress
    prep_plans = db.query(PrepPlan).filter(PrepPlan.user_id == user_id).all()
    prep_scores = [p.progress_percent for p in prep_plans if p.progress_percent is not None]
    company_prep_score = mean(prep_scores) if prep_scores else None

    # Calculate weighted composite index
    components_used = []
    weighted_sum = 0.0
    weight_total = 0.0

    scores_map = {
        "dsa": dsa_score,
        "cs_fundamentals": cs_score,
        "aptitude": aptitude_score,
        "communication": communication_score,
        "resume": resume_score,
        "interview": interview_score,
        "company_prep": company_prep_score,
    }

    for key, val in scores_map.items():
        if val is not None:
            weighted_sum += val * WEIGHTS[key]
            weight_total += WEIGHTS[key]
            components_used.append(key)

    # A composite score built from only a sliver of the 7 dimensions is
    # misleading precision - e.g. a single easy quiz shouldn't be allowed to
    # produce a confident-looking "82/100". Require coverage of at least
    # MIN_WEIGHT_COVERAGE of the total weight (roughly 2+ real dimensions)
    # before publishing a composite at all.
    MIN_WEIGHT_COVERAGE = 0.30
    has_sufficient_data = weight_total >= MIN_WEIGHT_COVERAGE
    composite = round(weighted_sum / weight_total) if has_sufficient_data else None
    data_status = "sufficient" if has_sufficient_data else "insufficient"

    # Identify top weaknesses (sorted lowest scores first) - only from
    # dimensions that actually have data. No invented default list when
    # nothing has been assessed yet.
    dimension_names = {
        "dsa": "DSA & Problem Solving",
        "cs_fundamentals": "CS Fundamentals",
        "aptitude": "Aptitude & Reasoning",
        "communication": "Communication Skills",
        "resume": "Resume Impact",
        "interview": "Technical Interviewing",
        "company_prep": "Target Company Preparation",
    }

    valid_scores = [(dimension_names[k], round(v)) for k, v in scores_map.items() if v is not None]
    valid_scores.sort(key=lambda x: x[1])
    top_weaknesses = [item[0] for item in valid_scores[:3]]

    def dim_value(v):
        """None (not a fabricated 0) so the frontend can render 'Not
        Assessed' distinctly from an actual score of 0."""
        return round(v) if v is not None else None

    return {
        "composite_score": composite,
        "data_status": data_status,  # "sufficient" | "insufficient" - UI must show "Readiness score unavailable - complete more assessments." when insufficient
        "algorithm_version": ALGORITHM_VERSION,
        "breakdown": {
            "dsa": dim_value(dsa_score),
            "cs_fundamentals": dim_value(cs_score),
            "aptitude": dim_value(aptitude_score),
            "communication": dim_value(communication_score),
            "resume": dim_value(resume_score),
            "interview": dim_value(interview_score),
            "company_prep": dim_value(company_prep_score),
            "components_used": components_used,
            "top_weaknesses": top_weaknesses,
            "algorithm_version": ALGORITHM_VERSION,
        },
    }
