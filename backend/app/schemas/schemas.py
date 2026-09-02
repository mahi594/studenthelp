import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, EmailStr


# ---------- User ----------
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    branch: Optional[str] = None
    grad_year: Optional[int] = None
    # The student's college/institution. Required in practice: a student with
    # no institution can never appear on any TPO dashboard, be assigned an
    # intervention, or be included in any institution-scoped export, since
    # every one of those queries filters on institution_id. See
    # app.services.institution_service.get_or_create_institution.
    college_name: Optional[str] = None
    institution_code: Optional[str] = None



class UserOut(BaseModel):
    id: uuid.UUID
    name: str
    email: EmailStr
    role: str
    branch: Optional[str]
    grad_year: Optional[int]
    cgpa: Optional[str] = None
    college_name: Optional[str] = None
    email_verified: bool = False
    target_company_ids: List[uuid.UUID] = []
    leetcode_username: Optional[str] = None
    leetcode_daily_goal: int = 1
    leetcode_total_solved: int = 0
    leetcode_easy_solved: int = 0
    leetcode_medium_solved: int = 0
    leetcode_hard_solved: int = 0
    leetcode_streak: int = 0
    leetcode_last_solved_date: Optional[str] = None
    must_change_password: bool = False

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    name: Optional[str] = None
    branch: Optional[str] = None
    grad_year: Optional[int] = None
    cgpa: Optional[str] = None
    college_name: Optional[str] = None
    leetcode_username: Optional[str] = None
    leetcode_daily_goal: Optional[int] = None

    class Config:
        from_attributes = True


# ---------- LeetCode ----------
class LeetCodeLogCreate(BaseModel):
    problem_title: str
    problem_slug: Optional[str] = None
    difficulty: str = "Easy"
    topic: Optional[str] = "General"
    notes: Optional[str] = None


class LeetCodeLogOut(BaseModel):
    id: uuid.UUID
    problem_title: str
    problem_slug: Optional[str]
    difficulty: str
    topic: Optional[str]
    notes: Optional[str]
    solved_at: datetime

    class Config:
        from_attributes = True


class LeetCodeProfileOut(BaseModel):
    username: Optional[str]
    daily_goal: int
    total_solved: int
    easy_solved: int
    medium_solved: int
    hard_solved: int
    streak: int
    last_solved_date: Optional[str]
    solved_today: bool
    recent_logs: List[LeetCodeLogOut] = []


class LeetCodeRecommendationOut(BaseModel):
    id: str
    title: str
    slug: str
    difficulty: str  # "Easy" | "Medium" | "Hard"
    topic: str
    level: str      # "Beginner" | "Intermediate" | "Advanced"
    description: str
    leetcode_url: str
    tags: List[str] = []


class LeetCodeStudentSummary(BaseModel):
    user_id: uuid.UUID
    name: str
    email: str
    leetcode_username: Optional[str]
    total_solved: int
    streak: int
    solved_today: bool
    last_solved_date: Optional[str]
    latest_problem: Optional[str] = None



# ---------- Password Reset ----------
class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str
    # Only populated when SMTP isn't configured (dev fallback) - never sent
    # alongside a real email in production. See auth.py.
    dev_reset_token: Optional[str] = None


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class ChangePasswordRequest(BaseModel):
    """Used with a restricted 'password_change' scope token issued at login
    when must_change_password is set (see /auth/change-password). No
    current-password field needed - possession of that scoped token already
    proves the login credentials were correct."""
    new_password: str


# ---------- Admin account creation ----------
class AdminCreateRequest(BaseModel):
    name: str
    email: EmailStr
    role: str = "admin"  # "admin" | "tpo_admin"
    college_name: Optional[str] = None  # required in practice for tpo_admin, to scope their dashboard


class AdminCreateResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: EmailStr
    role: str
    # Shown once, at creation time only - never retrievable again. If email
    # isn't configured, the caller (an existing admin) is responsible for
    # passing it along to the new admin out-of-band.
    temp_password: str
    email_sent: bool


# ---------- Quiz ----------
class QuizResultCreate(BaseModel):
    subject: str
    score_percent: int


class QuizResultOut(BaseModel):
    id: uuid.UUID
    subject: str
    score_percent: int
    taken_at: datetime

    class Config:
        from_attributes = True


class QuizWeeklySubjectStatus(BaseModel):
    subject: str
    last_taken_at: Optional[datetime] = None
    last_score_percent: Optional[int] = None
    next_eligible_at: Optional[datetime] = None
    is_due: bool  # True if never taken, or 7+ days since last attempt


# ---------- Company / Round / Question ----------
class QuestionOut(BaseModel):
    id: uuid.UUID
    subject: str
    difficulty: Optional[str]
    text: str
    answer_or_hint: Optional[str]
    source: str

    class Config:
        from_attributes = True


class RoundOut(BaseModel):
    id: uuid.UUID
    order_index: int
    round_type: str
    subjects_tested: List[str]
    difficulty: Optional[str]
    notes: Optional[str]
    questions: List[QuestionOut] = []

    class Config:
        from_attributes = True


class CompanyOut(BaseModel):
    id: uuid.UUID
    name: str
    roles: List[str]
    tags: List[str]
    min_cgpa: Optional[str]
    preferred_branches: List[str]
    resume_keywords: List[str]
    apply_url: Optional[str] = None
    is_curated_verified: bool = False
    source_type: str = "placement_cell"
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    confidence: str = "High"
    rounds: List[RoundOut] = []

    class Config:
        from_attributes = True


class CompanyCreate(BaseModel):
    name: str
    roles: List[str] = []
    tags: List[str] = []
    min_cgpa: Optional[str] = None
    preferred_branches: List[str] = []
    resume_keywords: List[str] = []
    apply_url: Optional[str] = None
    source_type: Optional[str] = "placement_cell"
    confidence: Optional[str] = "High"


class CompanyVerifyRequest(BaseModel):
    verified_by: str
    confidence: str = "High"  # "High" | "Medium" | "Low"
    source_type: str = "placement_cell"  # "placement_cell" | "alumni_report" | "ai_recommended"


class RoundCreate(BaseModel):
    order_index: int
    round_type: str
    subjects_tested: List[str] = []
    difficulty: Optional[str] = None
    notes: Optional[str] = None


# ---------- Prep Plan ----------
class PrepPlanGenerateRequest(BaseModel):
    target_company_id: uuid.UUID
    days_total: int


class TaskStatusUpdate(BaseModel):
    completed: Optional[bool] = None
    status: Optional[str] = None  # "planned" | "started" | "completed" | "skipped"


class PrepPlanOut(BaseModel):
    id: uuid.UUID
    target_company_id: Optional[uuid.UUID]
    days_total: int
    tasks: List[Dict[str, Any]]
    progress_percent: int
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Audit Log ----------
class AuditLogOut(BaseModel):
    id: uuid.UUID
    institution_id: uuid.UUID
    actor_user_id: uuid.UUID
    action: str
    resource_type: str
    resource_id: Optional[str]
    timestamp: datetime
    metadata_json: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True



# ---------- Resume ----------
class ResumeMatchOut(BaseModel):
    id: uuid.UUID
    file_url: str
    target_company_id: Optional[uuid.UUID] = None
    match_result: Optional[Dict[str, Any]]
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ---------- Roadmap ----------
class RoadmapGenerateRequest(BaseModel):
    horizon_months: int = 6
    target_company_ids: List[uuid.UUID] = []


class RoadmapOut(BaseModel):
    id: uuid.UUID
    horizon_months: int
    phases: List[Dict[str, Any]]
    target_company_ids: List[uuid.UUID] = []
    target_company_names: List[str] = []
    created_at: datetime

    class Config:
        from_attributes = True


class PlanCustomizeRequest(BaseModel):
    message: str
    conversation_history: List[Dict[str, str]] = []


class PlanCustomizeResponse(BaseModel):
    explanation: str
    plan_modified: bool
    roadmap: Optional[RoadmapOut] = None
    prep_plan: Optional[PrepPlanOut] = None


# ---------- Quiz Questions (AI-generated, admin-approved) ----------
class QuizGenerateRequest(BaseModel):
    subject: str
    num_questions: int = 10
    company_id: Optional[uuid.UUID] = None


class QuizQuestionAdminOut(BaseModel):
    """Full view for admins - includes the correct answer for review."""
    id: uuid.UUID
    company_id: Optional[uuid.UUID]
    subject: str
    difficulty: Optional[str]
    question_text: str
    options: List[str]
    correct_option_index: int
    explanation: Optional[str]
    status: str
    generated_by: str
    created_at: datetime

    class Config:
        from_attributes = True


class QuizQuestionStudentOut(BaseModel):
    """Student-facing view - deliberately omits correct_option_index so the
    answer isn't visible before they submit."""
    id: uuid.UUID
    subject: str
    difficulty: Optional[str]
    question_text: str
    options: List[str]

    class Config:
        from_attributes = True


class QuizAnswerSubmit(BaseModel):
    question_id: uuid.UUID
    selected_option_index: int


class QuizQuestionReviewItem(BaseModel):
    question_id: uuid.UUID
    question_text: str
    options: List[str]
    selected_option_index: int
    correct_option_index: int
    is_correct: bool
    explanation: Optional[str] = None


class QuizSubmitAnswersRequest(BaseModel):
    subject: str
    answers: List[QuizAnswerSubmit]


class QuizSubmitAnswersResponse(BaseModel):
    subject: str
    score_percent: int
    correct_count: int
    total_count: int
    is_weak_subject: bool = False  # score_percent < WEAK_SUBJECT_THRESHOLD, see quiz.py
    recommended_leetcode: List[LeetCodeRecommendationOut] = []
    question_breakdown: List[QuizQuestionReviewItem] = []


# ---------- Readiness Score ----------
class ReadinessScoreOut(BaseModel):
    id: uuid.UUID
    # None when data_status == "insufficient" - the frontend must render
    # "Readiness score unavailable - complete more assessments." in that
    # case rather than treating a missing value as 0.
    composite_score: Optional[int]
    data_status: str = "sufficient"  # "sufficient" | "insufficient"
    algorithm_version: str = "v1"
    breakdown: Dict[str, Any]
    biggest_gaps: List[str] = []
    explanation: Optional[str] = None
    computed_at: datetime

    class Config:
        from_attributes = True



# ---------- TPO Dashboard ----------
class StudentReadinessSummary(BaseModel):
    user_id: uuid.UUID
    name: str
    email: str
    branch: Optional[str]
    grad_year: Optional[int]
    latest_composite_score: Optional[int]
    flagged_low_readiness: bool
    risk_category: str = "Not Assessed"


class InterventionCreate(BaseModel):
    title: str
    skill_topic: str
    intervention_type: str = "workshop"
    target_branch: Optional[str] = None
    target_grad_year: Optional[int] = None
    target_readiness_min: Optional[int] = None
    target_readiness_max: Optional[int] = None
    target_risk: Optional[str] = None
    target_company_id: Optional[uuid.UUID] = None
    target_student_ids: List[uuid.UUID] = []


class InterventionOut(BaseModel):
    id: uuid.UUID
    title: str
    skill_topic: str
    intervention_type: str
    target_branch: Optional[str]
    target_student_ids: List[uuid.UUID]
    status: str
    # Sample sizes - always show these alongside the scores below so a
    # "before/after" number is never read as covering every target student.
    eligible_count: int
    pre_assessed_count: int
    reassessed_count: int
    # These are ONLY populated from real ReadinessScore data for the target
    # students. pre_avg_score is None until at least one target student has
    # been assessed; post_avg_score/improvement_delta stay None until the
    # intervention is completed AND at least one target student has been
    # reassessed after completion started.
    pre_avg_score: Optional[int]
    post_avg_score: Optional[int]
    improvement_delta: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True



class BranchBreakdown(BaseModel):
    branch: str
    average_score: float
    student_count: int


class TpoStudentAssessmentEntry(BaseModel):
    date: datetime
    subject: str
    score_percent: int


class TpoStudentTargetCompany(BaseModel):
    company_id: uuid.UUID
    name: str
    roles: List[str] = []
    application_status: Optional[str] = None
    # Real, AI-computed resume match score for THIS company, if the student
    # has uploaded/matched a resume against it - never a fabricated number.
    resume_match_percent: Optional[int] = None
    resume_match_note: Optional[str] = None  # e.g. "AI-generated resume match" or "No resume matched to this company yet"


class TpoStudentPreparation(BaseModel):
    has_plan: bool
    target_company_name: Optional[str] = None
    days_total: Optional[int] = None
    progress_percent: Optional[int] = None
    created_at: Optional[datetime] = None


class TpoStudentMockInterview(BaseModel):
    date: datetime
    overall_score: Optional[int]
    strengths: List[str] = []
    improvements: List[str] = []
    is_ai_generated_feedback: bool = True


class TpoStudentInterventionEntry(BaseModel):
    id: uuid.UUID
    title: str
    status: str
    pre_avg_score: Optional[int]
    post_avg_score: Optional[int]
    improvement_delta: Optional[int]


class TpoStudentDetailOut(BaseModel):
    # Profile
    user_id: uuid.UUID
    name: str
    email: str
    branch: Optional[str]
    grad_year: Optional[int]
    cgpa: Optional[str]

    # Placement readiness
    composite_score: Optional[int]
    data_status: str = "insufficient"
    algorithm_version: str = "v1"
    breakdown: Dict[str, Any] = {}
    risk_category: str = "Not Assessed"
    readiness_trend: List[Dict[str, Any]] = []  # [{date, composite_score}], oldest first

    # Assessment history
    assessment_history: List[TpoStudentAssessmentEntry] = []

    # Target companies
    target_companies: List[TpoStudentTargetCompany] = []

    # Preparation
    preparation: TpoStudentPreparation

    # Mock interviews
    mock_interviews: List[TpoStudentMockInterview] = []

    # Interventions targeting this student
    interventions: List[TpoStudentInterventionEntry] = []


class TpoDashboardOut(BaseModel):
    total_students: int
    students_with_score: int = 0
    batch_average_score: Optional[float] = None
    low_readiness_threshold: int = 50
    flagged_students: List[StudentReadinessSummary] = []
    branch_breakdown: List[BranchBreakdown] = []
    all_students: List[StudentReadinessSummary] = []
    students: List[StudentReadinessSummary] = []
    total_matching: int = 0
    filtered_students_count: int = 0
    flagged_students_count: int = 0
    average_readiness_score: Optional[float] = None
    institution_name: Optional[str] = None
    page: int = 1
    page_size: int = 20
    total_pages: int = 1


# ---------- Job Listings (live openings, auto-fetched) ----------
class JobListingRefreshRequest(BaseModel):
    keywords: str = "software engineer"
    location: str = ""
    results_per_page: int = 20


class JobListingRefreshResponse(BaseModel):
    fetched: int
    created: int
    skipped_duplicates: int
    expired_deleted: int


class JobListingOut(BaseModel):
    id: uuid.UUID
    company_name: str
    role_title: str
    location: Optional[str]
    description_snippet: Optional[str]
    apply_url: str
    posted_at: Optional[datetime]
    expires_at: datetime

    class Config:
        from_attributes = True


# ---------- Applications (applied/not-applied tracking per company) ----------
class ApplicationMarkRequest(BaseModel):
    company_id: uuid.UUID
    status: str = "applied"  # "not_applied" | "applied" | "interviewing" | "offered" | "rejected"


class ApplicationOut(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    status: str
    applied_at: Optional[datetime]
    updated_at: datetime

    class Config:
        from_attributes = True
class ChatAskRequest(BaseModel):
    message: str
    company_id: Optional[uuid.UUID] = None   # set if the question is about a specific company


class ChatMessageOut(BaseModel):
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatAskResponse(BaseModel):
    answer: str
    history: List[ChatMessageOut]


# ---------- Mock Interview ----------
class MockInterviewStartRequest(BaseModel):
    role_or_subject: str
    company_id: Optional[uuid.UUID] = None


class MockInterviewRespondRequest(BaseModel):
    answer: str


class MockInterviewTurnOut(BaseModel):
    role: str
    content: str


class MockInterviewSessionOut(BaseModel):
    id: uuid.UUID
    company_id: Optional[uuid.UUID]
    role_or_subject: str
    transcript: List[Dict[str, Any]]
    status: str
    overall_score: Optional[int]
    feedback: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Email verification ----------
class VerifyEmailRequest(BaseModel):
    token: str


class ResendVerificationResponse(BaseModel):
    message: str
    # Same dev-mode fallback pattern as ForgotPasswordResponse.dev_reset_token
    dev_verify_token: Optional[str] = None


# ---------- Notifications ----------
class NotificationOut(BaseModel):
    id: uuid.UUID
    type: str
    title: str
    body: Optional[str]
    link: Optional[str]
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Community Q&A ----------
class QAAnswerCreate(BaseModel):
    body: str


class QAAnswerOut(BaseModel):
    id: uuid.UUID
    author_id: uuid.UUID
    author_name: str
    body: str
    upvotes: int
    created_at: datetime

    class Config:
        from_attributes = True


class QAQuestionCreate(BaseModel):
    title: str
    body: str
    company_id: Optional[uuid.UUID] = None
    tags: List[str] = []


class QAQuestionListOut(BaseModel):
    """Lighter payload for the list view - no answers, just a count."""
    id: uuid.UUID
    author_id: uuid.UUID
    author_name: str
    title: str
    body: str
    company_id: Optional[uuid.UUID]
    tags: List[str]
    answer_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class QAQuestionDetailOut(BaseModel):
    id: uuid.UUID
    author_id: uuid.UUID
    author_name: str
    title: str
    body: str
    company_id: Optional[uuid.UUID]
    tags: List[str]
    answers: List[QAAnswerOut]
    created_at: datetime

    class Config:
        from_attributes = True
