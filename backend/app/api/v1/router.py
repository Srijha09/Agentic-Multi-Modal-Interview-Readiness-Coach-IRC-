"""
Main API router for v1 endpoints.
"""
from fastapi import APIRouter
from app.api.v1.endpoints import health, documents, plans, practice, gaps, coach, mastery, adaptive, calendar

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(gaps.router, prefix="/gaps", tags=["gaps"])
api_router.include_router(plans.router, prefix="/plans", tags=["plans"])
api_router.include_router(practice.router, prefix="/practice", tags=["practice"])
api_router.include_router(coach.router, prefix="/coach", tags=["coach"])
api_router.include_router(mastery.router, prefix="/mastery", tags=["mastery"])
api_router.include_router(adaptive.router, prefix="/adaptive", tags=["adaptive"])
api_router.include_router(calendar.router, prefix="/calendar", tags=["calendar"])




