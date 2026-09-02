"""
AI service layer.

Design rule (see docs/architecture.md): the AI is only allowed to SEQUENCE and
PERSONALIZE facts that already exist in our curated database (company rounds,
subjects tested, real questions, learning resources). It is never the source
of truth for "what does company X ask" - that always comes from `Company`,
`Round`, `Question`, and `LearningResource` rows populated by admins/seniors.

Provider strategy: Gemini is the primary provider (free daily quota, good for
development). If Gemini's quota/rate limit is hit, calls automatically fall
back to Groq (also has a free tier) - this only happens on quota/rate-limit
errors specifically; genuine bugs (bad prompt, auth failure) are re-raised
rather than silently falling back. Requires GROQ_API_KEY to be set for the
fallback to work; without it, a quota error simply propagates as before.
"""
import json
import logging
from typing import List, Dict, Any, Optional

import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, GoogleAPICallError
from groq import Groq

from app.core.config import settings
from app.models.company import Company
from app.models.user import QuizResult

logger = logging.getLogger(__name__)

genai.configure(api_key=settings.GEMINI_API_KEY)
groq_client = Groq(api_key=settings.GROQ_API_KEY) if settings.GROQ_API_KEY else None

# "gemini-3.5-flash-lite" is Google's current low-latency, cost-effective GA
# model - closest match to the original intent (cheapest, generous free
# quota) now that the whole Gemini 1.5 family has been shut down (as of
# mid-2026, calls to gemini-1.5-flash return a 404, not an auth/quota error,
# so they don't trigger the Groq fallback below - they just fail outright).
GEMINI_MODEL_NAME = "gemini-3.5-flash-lite"

# Groq deprecated llama-3.3-70b-versatile on 2026-06-17; openai/gpt-oss-120b
# is their recommended replacement (see console.groq.com/docs/deprecations).
GROQ_MODEL_NAME = "openai/gpt-oss-120b"


def _is_quota_or_rate_limit_error(exc: Exception) -> bool:
    """Detects Gemini quota/rate-limit errors so we know when to fall back to Groq,
    as opposed to a genuine bug (bad prompt, auth error) which should surface normally."""
    if isinstance(exc, ResourceExhausted):
        return True
    message = str(exc).lower()
    return any(term in message for term in ["quota", "rate limit", "429", "resource_exhausted"])


def _generate(prompt: str, max_tokens: int = 4000, system_instruction: Optional[str] = None) -> str:
    """Single-turn generation. Tries Gemini first; falls back to Groq only if
    Gemini's daily/rate limit is hit and a Groq key is configured."""
    try:
        model = genai.GenerativeModel(
            model_name=GEMINI_MODEL_NAME,
            system_instruction=system_instruction,
        )
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(max_output_tokens=max_tokens),
        )
        return response.text.strip()

    except (ResourceExhausted, GoogleAPICallError, Exception) as exc:
        if not _is_quota_or_rate_limit_error(exc):
            raise  # a real bug, not a quota issue - don't mask it by falling back

        if not groq_client:
            raise RuntimeError(
                "Gemini quota exhausted and no GROQ_API_KEY configured for fallback"
            ) from exc

        logger.warning("Gemini quota/rate limit hit, falling back to Groq: %s", exc)
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        completion = groq_client.chat.completions.create(
            model=GROQ_MODEL_NAME,
            messages=messages,
            max_tokens=max_tokens,
        )
        return completion.choices[0].message.content.strip()


def _extract_json(text: str) -> Any:
    """Strips markdown code fences the model sometimes wraps JSON in, then parses.
    Safely raises a clean ValueError if the JSON is malformed."""
    if not text:
        raise ValueError("AI provider returned empty response")
    cleaned = text.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse AI JSON response: %s | Content: %s", exc, text[:200])
        raise ValueError("Malformed AI JSON response") from exc



def build_plan_prompt(
    company: Company,
    quiz_results: List[QuizResult],
    days_total: int,
    resources_by_subject: Dict[str, List[Dict[str, str]]],
) -> str:
    """Builds the prompt sent to the model for day-wise plan generation.

    Only curated facts (company rounds/subjects, quiz scores, resource links)
    are passed in. The model is instructed to sequence/prioritize, not invent facts.
    """
    rounds_summary = [
        {
            "round_type": r.round_type,
            "subjects_tested": r.subjects_tested,
            "difficulty": r.difficulty,
        }
        for r in sorted(company.rounds, key=lambda r: r.order_index)
    ]

    weak_subjects = sorted(quiz_results, key=lambda q: q.score_percent)

    return f"""You are generating a day-wise placement preparation plan.

STRICT RULE: Only use the company round/subject facts given below. Do not invent
information about what the company tests. Your job is to PRIORITIZE and SEQUENCE,
not to add new factual claims about the company.

Company: {company.name}
Rounds (in order): {json.dumps(rounds_summary)}

Student's quiz results (lower score = weaker subject, prioritize these):
{json.dumps([{"subject": q.subject, "score_percent": q.score_percent} for q in weak_subjects])}

Available curated learning resources per subject:
{json.dumps(resources_by_subject)}

Days available until the drive: {days_total}

Return ONLY valid JSON (no markdown, no preamble) as a list of task objects:
[
  {{
    "day": 1,
    "topic": "string",
    "task": "string - specific, actionable",
    "source_title": "string or null - pick from provided resources only",
    "source_url": "string or null - pick from provided resources only",
    "reason": "string - why this task now, referencing weak subject or company round"
  }}
]

Prioritize weak subjects that are also tested by this company's rounds. Balance
subject study with round-specific practice (e.g. OA practice closer to day 1 if
OA is round 1). Distribute across all {days_total} days."""


def generate_prep_plan(
    company: Company,
    quiz_results: List[QuizResult],
    days_total: int,
    resources_by_subject: Dict[str, List[Dict[str, str]]],
) -> List[Dict[str, Any]]:
    prompt = build_plan_prompt(company, quiz_results, days_total, resources_by_subject)
    text = _generate(prompt, max_tokens=4000)
    return _extract_json(text)


def build_resume_match_prompt(resume_text: str, company: Company, job_description: Optional[str] = None) -> str:
    target_info = f"Company: {company.name}\nPreferred branches: {company.preferred_branches}\nMinimum CGPA: {company.min_cgpa}\nResume keywords they filter for: {company.resume_keywords}"
    if job_description:
        target_info += f"\nJob Description / Role Requirements: {job_description}"

    return f"""Analyze this resume as a professional Applicant Tracking System (ATS) screening engine against the specified target company/job.

Target Context:
{target_info}

Resume Text:
---
{resume_text}
---

Perform a thorough, deterministic analysis and return ONLY valid JSON (no markdown or preamble) with this exact structure:
{{
  "ats_score": 0-100,
  "match_score_percent": 0-100,
  "keyword_match_percent": 0-100,
  "section_detection": {{
    "contact_info": true/false,
    "education": true/false,
    "experience": true/false,
    "projects": true/false,
    "skills": true/false,
    "certifications": true/false,
    "achievements": true/false
  }},
  "detected_sections": ["string"],
  "missing_sections": ["string"],
  "matched_skills": ["string"],
  "missing_skills": ["string"],
  "matched_keywords": ["string"],
  "missing_keywords": ["string"],
  "experience_alignment": "string - brief evaluation of relevance",
  "education_match": "string - brief evaluation",
  "role_alignment": "string - alignment with target role",
  "quality_warnings": ["specific formatting, ATS-readability, or bullet point quality warnings"],
  "recommendations": ["actionable numbered suggestions to improve the resume score"],
  "suggestions": ["bullet-level suggestions"],
  "meets_cgpa_cutoff": true/false/null
}}"""


def match_resume_to_company(resume_text: str, company: Company, job_description: Optional[str] = None) -> Dict[str, Any]:
    prompt = build_resume_match_prompt(resume_text, company, job_description)
    text = _generate(prompt, max_tokens=2500)
    result = _extract_json(text)
    # Guarantee backwards compatibility for existing frontend/test fields
    if "match_score_percent" in result and "ats_score" not in result:
        result["ats_score"] = result["match_score_percent"]
    elif "ats_score" in result and "match_score_percent" not in result:
        result["match_score_percent"] = result["ats_score"]
    return result


def build_quiz_generation_prompt(
    subject: str,
    num_questions: int,
    company: Optional[Company],
) -> str:
    company_context = ""
    if company:
        rounds_summary = [
            {
                "round_type": r.round_type,
                "subjects_tested": r.subjects_tested,
                "difficulty": r.difficulty,
                "notes": r.notes,
            }
            for r in sorted(company.rounds, key=lambda r: r.order_index)
        ]
        company_context = f"""
This quiz is being generated for a student targeting {company.name}. Use the
curated round data below ONLY to calibrate difficulty/style (e.g. if their OA
is described as medium-difficulty DSA, lean that direction) - do NOT claim
these are actual company exam questions, and do NOT invent facts about the
company beyond what's given here.
Curated round data: {json.dumps(rounds_summary)}
"""

    return f"""Generate {num_questions} multiple-choice quiz questions for the
subject "{subject}", aimed at assessing a college student's placement
readiness in this subject.
{company_context}
Return ONLY valid JSON (no markdown), a list of question objects:
[
  {{
    "question_text": "string",
    "options": ["string", "string", "string", "string"],
    "correct_option_index": 0,
    "difficulty": "Easy" | "Medium" | "Hard",
    "explanation": "brief explanation of the correct answer"
  }}
]

Make questions applied/practical, not pure definitions. Exactly 4 options each,
correct_option_index must be a valid index into options (0-3)."""


def generate_quiz_questions(
    subject: str,
    num_questions: int,
    company: Optional[Company] = None,
) -> List[Dict[str, Any]]:
    prompt = build_quiz_generation_prompt(subject, num_questions, company)
    text = _generate(prompt, max_tokens=4000)
    return _extract_json(text)


# ---------------------------------------------------------------------------
# Roadmap: longer-horizon, performance-driven plan (re-generated as scores change)
# ---------------------------------------------------------------------------

def build_roadmap_prompt(
    quiz_results: List[QuizResult],
    horizon_months: int,
    target_company_names: List[str],
) -> str:
    scores = [{"subject": q.subject, "score_percent": q.score_percent} for q in quiz_results]

    return f"""You are generating a long-term ({horizon_months}-month) placement
preparation roadmap for a student, broken into phases (e.g. monthly or by
semester chunks).

STRICT RULE: Base subject priority ONLY on the quiz scores given below (lower
score = weaker = higher priority). Do not claim specific facts about named
companies beyond that the student is targeting them generally - detailed
company facts belong in the short-term prep plan feature, not here.

Current quiz scores (performance signal): {json.dumps(scores)}
Student's general target companies (for context only, not fact source): {target_company_names}
Roadmap horizon: {horizon_months} months

Return ONLY valid JSON (no markdown), a list of phase objects:
[
  {{
    "phase": "string, e.g. 'Month 1-2'",
    "focus_subjects": ["string"],
    "milestones": ["specific, measurable, e.g. 'Solve 50 easy DSA problems'"],
    "reason": "why this phase now, referencing the quiz performance"
  }}
]

Order phases from foundational/weak-subject-first toward company-round-style
practice closer to the end of the horizon. Keep milestones measurable, not vague."""


def generate_roadmap(
    quiz_results: List[QuizResult],
    horizon_months: int,
    target_company_names: List[str],
) -> List[Dict[str, Any]]:
    prompt = build_roadmap_prompt(quiz_results, horizon_months, target_company_names)
    text = _generate(prompt, max_tokens=3000)
    return _extract_json(text)


PLAN_CUSTOMIZER_SYSTEM_PROMPT = """You are an expert AI plan customization agent for StudentHelp.
Your job is to assist a student in customizing their active Placement Roadmap or Day-wise Prep Plan based on their conversational input (e.g. daily hour constraints, known topics to skip, upcoming interview deadlines, weak subjects to prioritize, rest days, reordering tasks).

Rules:
1. Understand the student's request and current plan context.
2. If the student asks a question about the plan (e.g., "Why is DSA on day 3?"), explain clearly and set "plan_modified": false.
3. If the student requests a valid modification to their plan (e.g., "Reduce daily hours to 2", "Skip arrays", "I have an interview in 21 days", "Don't study on Sundays"):
   - Interpret the request
   - Modify the plan structure appropriately
   - Set "plan_modified": true in the response
   - Return the updated plan in the exact JSON schema requested below.
4. Do NOT hallucinate unverified company facts.
5. Return ONLY valid JSON (no markdown or preamble).

Required JSON Output Format:
{
  "explanation": "Friendly, conversational response explaining what was answered or modified",
  "plan_modified": true/false,
  "updated_plan_data": { ... } // Updated phases array for Roadmap OR updated tasks array + days_total for PrepPlan (or null if plan_modified is false)
}"""


def customize_plan_with_ai(
    plan_type: str,  # "roadmap" or "prep_plan"
    current_plan_data: Dict[str, Any],
    user_message: str,
    conversation_history: List[Dict[str, str]],
    student_profile: Dict[str, Any],
    company_name: Optional[str] = None,
) -> Dict[str, Any]:
    context_json = json.dumps({
        "plan_type": plan_type,
        "student_profile": student_profile,
        "company_name": company_name,
        "current_plan_data": current_plan_data,
        "conversation_history": conversation_history[-6:],
    })

    prompt = f"""Current Plan & Student Context:
{context_json}

Student Request: "{user_message}"

Return JSON adhering strictly to PLAN_CUSTOMIZER_SYSTEM_PROMPT."""

    text = _generate(prompt, max_tokens=3500, system_instruction=PLAN_CUSTOMIZER_SYSTEM_PROMPT)
    result = _extract_json(text)
    return result


# ---------------------------------------------------------------------------
# Chat bot: answers general placement/study questions, grounded on curated
# company data when a specific company is discussed.
# ---------------------------------------------------------------------------

CHAT_SYSTEM_PROMPT = """You are the StudentHelp placement preparation assistant.
Scope: answer questions about placement preparation, interview prep, resumes,
study subjects (DSA, DBMS, OS, aptitude, etc.), and career guidance for
students.

Rules:
1. If the question is about a SPECIFIC company's hiring process (rounds,
   difficulty, what they test), you MUST only use the curated company facts
   provided in the context below. If no curated data is provided for that
   company, say you don't have verified data on it yet instead of guessing.
2. For general study/interview/career questions with no curated data
   available, answer normally using your own knowledge.
3. If the question is unrelated to placement, interviews, study, or careers,
   politely say this assistant is scoped to placement preparation and redirect.
4. Keep answers concise and practical - this is a chat interface, not an essay."""


def build_chat_context(company: Optional[Company]) -> str:
    if not company:
        return "No specific curated company data is relevant to this question."

    rounds_summary = [
        {
            "round_type": r.round_type,
            "subjects_tested": r.subjects_tested,
            "difficulty": r.difficulty,
            "notes": r.notes,
        }
        for r in sorted(company.rounds, key=lambda r: r.order_index)
    ]
    return f"Curated data for {company.name}: rounds = {json.dumps(rounds_summary)}"


def answer_chat_question(
    conversation_history: List[Dict[str, str]],
    latest_question: str,
    relevant_company: Optional[Company],
) -> str:
    """conversation_history: list of {"role": "user"|"assistant", "content": str}

    Tries Gemini first (translating history to its "model"/"parts" format),
    falls back to Groq (OpenAI-style "assistant" format) if Gemini's quota is hit.
    """
    context = build_chat_context(relevant_company)
    user_turn = f"Context: {context}\n\nQuestion: {latest_question}"

    try:
        model = genai.GenerativeModel(
            model_name=GEMINI_MODEL_NAME,
            system_instruction=CHAT_SYSTEM_PROMPT,
        )
        gemini_history = [
            {
                "role": "model" if turn["role"] == "assistant" else "user",
                "parts": [turn["content"]],
            }
            for turn in conversation_history
        ]
        chat = model.start_chat(history=gemini_history)
        response = chat.send_message(
            user_turn,
            generation_config=genai.types.GenerationConfig(max_output_tokens=1000),
        )
        return response.text.strip()

    except (ResourceExhausted, GoogleAPICallError, Exception) as exc:
        if not _is_quota_or_rate_limit_error(exc):
            raise

        if not groq_client:
            raise RuntimeError(
                "Gemini quota exhausted and no GROQ_API_KEY configured for fallback"
            ) from exc

        logger.warning("Gemini quota/rate limit hit on chat, falling back to Groq: %s", exc)
        messages = [{"role": "system", "content": CHAT_SYSTEM_PROMPT}]
        messages += [{"role": turn["role"], "content": turn["content"]} for turn in conversation_history]
        messages.append({"role": "user", "content": user_turn})

        completion = groq_client.chat.completions.create(
            model=GROQ_MODEL_NAME,
            messages=messages,
            max_tokens=1000,
        )
        return completion.choices[0].message.content.strip()


# ---------------------------------------------------------------------------
# Mock Interview: AI conducts a turn-by-turn interview, then scores it.
# ---------------------------------------------------------------------------

MOCK_INTERVIEWER_SYSTEM_PROMPT = """You are an experienced technical interviewer
conducting a mock placement interview. Ask one question at a time, listen to
the candidate's answer, then ask a natural follow-up - the way a real
interviewer probes deeper on a weak answer or moves on after a strong one.

Rules:
1. If curated company round data is provided, calibrate your questions to
   match that company's style/difficulty/subjects - but never claim these are
   the company's actual real interview questions, and never invent facts
   about the company beyond what's given.
2. Keep questions realistic and one at a time - don't ask multiple questions
   in one turn.
3. Stay encouraging but honest in tone, like a real interviewer would be."""


def build_mock_interview_context(company: Optional[Company], role_or_subject: str) -> str:
    if not company:
        return f"No specific company selected - conduct a general interview for the role/subject: {role_or_subject}."

    rounds_summary = [
        {"round_type": r.round_type, "subjects_tested": r.subjects_tested, "difficulty": r.difficulty}
        for r in sorted(company.rounds, key=lambda r: r.order_index)
    ]
    return f"Target company: {company.name}, role: {role_or_subject}. Curated round data: {json.dumps(rounds_summary)}"


def start_mock_interview(company: Optional[Company], role_or_subject: str) -> str:
    """Returns the interviewer's opening question."""
    context = build_mock_interview_context(company, role_or_subject)
    prompt = f"{context}\n\nBegin the interview now with your first question."

    model = genai.GenerativeModel(model_name=GEMINI_MODEL_NAME, system_instruction=MOCK_INTERVIEWER_SYSTEM_PROMPT)
    try:
        response = model.generate_content(
            prompt, generation_config=genai.types.GenerationConfig(max_output_tokens=300)
        )
        return response.text.strip()
    except Exception as exc:
        if not _is_quota_or_rate_limit_error(exc) or not groq_client:
            raise
        completion = groq_client.chat.completions.create(
            model=GROQ_MODEL_NAME,
            messages=[
                {"role": "system", "content": MOCK_INTERVIEWER_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            max_tokens=300,
        )
        return completion.choices[0].message.content.strip()


def continue_mock_interview(transcript: List[Dict[str, str]], candidate_answer: str) -> str:
    """Sends the candidate's latest answer, gets the interviewer's next
    question/follow-up. `transcript` uses roles 'interviewer'/'candidate' -
    translated to Gemini's 'model'/'user' here."""
    gemini_history = [
        {
            "role": "model" if turn["role"] == "interviewer" else "user",
            "parts": [turn["content"]],
        }
        for turn in transcript
    ]

    model = genai.GenerativeModel(model_name=GEMINI_MODEL_NAME, system_instruction=MOCK_INTERVIEWER_SYSTEM_PROMPT)
    try:
        chat = model.start_chat(history=gemini_history)
        response = chat.send_message(
            candidate_answer, generation_config=genai.types.GenerationConfig(max_output_tokens=300)
        )
        return response.text.strip()
    except Exception as exc:
        if not _is_quota_or_rate_limit_error(exc) or not groq_client:
            raise
        messages = [{"role": "system", "content": MOCK_INTERVIEWER_SYSTEM_PROMPT}]
        messages += [
            {"role": "assistant" if t["role"] == "interviewer" else "user", "content": t["content"]}
            for t in transcript
        ]
        messages.append({"role": "user", "content": candidate_answer})
        completion = groq_client.chat.completions.create(model=GROQ_MODEL_NAME, messages=messages, max_tokens=300)
        return completion.choices[0].message.content.strip()


def score_mock_interview(transcript: List[Dict[str, str]]) -> Dict[str, Any]:
    """Called when the student ends the session - reviews the full transcript
    and returns 5 structured dimension scores + overall score + feedback."""
    prompt = f"""Review this mock interview transcript and evaluate the candidate across 5 structured dimensions (0-100 each) plus overall score and feedback.

Transcript: {json.dumps(transcript)}

Return ONLY valid JSON (no markdown):
{{
  "overall_score": 0-100,
  "technical_knowledge": 0-100,
  "problem_solving": 0-100,
  "communication_score": 0-100,
  "answer_structure": 0-100,
  "technical_depth": 0-100,
  "strengths": ["2-4 specific strengths"],
  "improvements": ["2-4 specific actionable areas to improve"]
}}"""
    text = _generate(prompt, max_tokens=1000)
    return _extract_json(text)