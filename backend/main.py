"""
FastAPI application entry point for Interview Readiness Coach.
"""
import logging

# Configure logging before other app imports
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# LangSmith must be configured before LangChain / LangGraph imports
from app.core.tracing import configure_langsmith_tracing

configure_langsmith_tracing()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.router import api_router
from app.db.database import engine, Base

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Interview Readiness Coach API",
    description="Agentic multi-modal interview preparation system",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Interview Readiness Coach API", "status": "healthy"}


@app.get("/health")
async def health():
    """Detailed health check."""
    from app.core.tracing import is_langsmith_enabled

    return {
        "status": "healthy",
        "version": "0.1.0",
        "database": "connected",
        "langsmith_tracing": is_langsmith_enabled(),
        "langsmith_project": settings.LANGSMITH_PROJECT,
    }
