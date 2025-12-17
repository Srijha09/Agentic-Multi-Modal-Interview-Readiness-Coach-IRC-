"""
Main API router for v1 endpoints.
"""
from fastapi import APIRouter
from app.api.v1.endpoints import health, documents, plans, practice

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(plans.router, prefix="/plans", tags=["plans"])
api_router.include_router(practice.router, prefix="/practice", tags=["practice"])



