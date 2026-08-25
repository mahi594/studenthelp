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


def build_resume_match_prompt(resume_text: str, company: Company) -> str:
    return f"""Compare this resume against the target company's known requirements.
Only use the requirements listed below - do not assume requirements not given.

Company: {company.name}
Preferred branches: {company.preferred_branches}
Minimum CGPA: {company.min_cgpa}
Resume keywords they filter for: {company.resume_keywords}

Resume text:
---
{resume_text}
---

Return ONLY valid JSON (no markdown):
{{
  "match_score_percent": 0-100,
  "missing_keywords": ["string"],
  "suggestions": ["specific, actionable bullet-level suggestions"],
  "meets_cgpa_cutoff": true/false/null
}}"""


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


def match_resume_to_company(resume_text: str, company: Company) -> Dict[str, Any]:
    prompt = build_resume_match_prompt(resume_text, company)
    text = _generate(prompt, max_tokens=1500)
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