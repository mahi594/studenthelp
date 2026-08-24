from fastapi import APIRouter

from app.api.v1.endpoints import auth, companies, prep_plan, resume, quiz, roadmap, chat, admin, readiness, tpo, job_listings, applications, mock_interview, users, notifications, qa, leetcode, audit_logs

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(notifications.router)
api_router.include_router(qa.router)
api_router.include_router(companies.router)
api_router.include_router(prep_plan.router)
api_router.include_router(resume.router)
api_router.include_router(quiz.router)
api_router.include_router(roadmap.router)
api_router.include_router(chat.router)
api_router.include_router(admin.router)
api_router.include_router(readiness.router)
api_router.include_router(tpo.router)
api_router.include_router(job_listings.router)
api_router.include_router(applications.router)
api_router.include_router(mock_interview.router)
api_router.include_router(leetcode.router)
api_router.include_router(audit_logs.router)


