"""
Observability API endpoints - Phase 12
Provides system health, performance metrics, and trace information.
"""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, text

from app.db.database import get_db
from app.db.models import (
    User, StudyPlan, DailyTask, PracticeAttempt, Evaluation,
    SkillMastery, CalendarEvent
)
from app.core.config import settings

router = APIRouter()


@router.get("/health")
async def get_system_health(db: Session = Depends(get_db)):
    """
    Get system health status.
    
    Returns:
        System health metrics including database connectivity,
        LLM configuration, and service status.
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {}
    }
    
    # Check database connectivity
    try:
        db.execute(text("SELECT 1"))
        health_status["services"]["database"] = "connected"
    except Exception as e:
        health_status["services"]["database"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check LLM configuration
    llm_status = "configured" if settings.OPENAI_API_KEY or settings.ANTHROPIC_API_KEY else "not_configured"
    health_status["services"]["llm"] = llm_status
    
    # Check LangSmith tracing
    langsmith_status = "enabled" if settings.LANGSMITH_TRACING and settings.LANGSMITH_API_KEY else "disabled"
    health_status["services"]["langsmith"] = langsmith_status
    
    return health_status


@router.get("/metrics")
async def get_system_metrics(
    user_id: Optional[int] = Query(None, description="User ID (optional, for user-specific metrics)"),
    db: Session = Depends(get_db),
):
    """
    Get system performance metrics.
    
    Returns:
        Metrics including:
        - Total users, plans, tasks
        - Practice attempts and evaluations
        - Mastery tracking stats
        - Calendar events
    """
    metrics = {
        "timestamp": datetime.now().isoformat(),
        "system": {},
        "user": {}
    }
    
    # System-wide metrics
    metrics["system"] = {
        "total_users": db.query(func.count(User.id)).scalar() or 0,
        "total_study_plans": db.query(func.count(StudyPlan.id)).scalar() or 0,
        "total_tasks": db.query(func.count(DailyTask.id)).scalar() or 0,
        "total_practice_attempts": db.query(func.count(PracticeAttempt.id)).scalar() or 0,
        "total_evaluations": db.query(func.count(Evaluation.id)).scalar() or 0,
        "total_mastery_records": db.query(func.count(SkillMastery.id)).scalar() or 0,
        "total_calendar_events": db.query(func.count(CalendarEvent.id)).scalar() or 0,
    }
    
    # User-specific metrics (if user_id provided)
    if user_id:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            metrics["user"] = {
                "user_id": user_id,
                "study_plans": db.query(func.count(StudyPlan.id)).filter(
                    StudyPlan.user_id == user_id
                ).scalar() or 0,
                "tasks": db.query(func.count(DailyTask.id)).join(
                    StudyPlan
                ).filter(StudyPlan.user_id == user_id).scalar() or 0,
                "practice_attempts": db.query(func.count(PracticeAttempt.id)).filter(
                    PracticeAttempt.user_id == user_id
                ).scalar() or 0,
                "evaluations": db.query(func.count(Evaluation.id)).join(
                    PracticeAttempt
                ).filter(PracticeAttempt.user_id == user_id).scalar() or 0,
                "mastery_records": db.query(func.count(SkillMastery.id)).filter(
                    SkillMastery.user_id == user_id
                ).scalar() or 0,
            }
        else:
            raise HTTPException(status_code=404, detail="User not found")
    
    return metrics


@router.get("/performance")
async def get_performance_metrics(
    days: int = Query(7, description="Number of days to look back"),
    db: Session = Depends(get_db),
):
    """
    Get performance metrics over time.
    
    Returns:
        Performance data including:
        - Tasks completed per day
        - Practice attempts per day
        - Average evaluation scores
        - Mastery improvements
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Tasks completed per day
    completed_tasks = db.query(
        func.date(DailyTask.completed_at).label("date"),
        func.count(DailyTask.id).label("count")
    ).filter(
        DailyTask.completed_at >= start_date,
        DailyTask.completed_at <= end_date
    ).group_by(func.date(DailyTask.completed_at)).all()
    
    # Practice attempts per day
    attempts = db.query(
        func.date(PracticeAttempt.created_at).label("date"),
        func.count(PracticeAttempt.id).label("count")
    ).filter(
        PracticeAttempt.created_at >= start_date,
        PracticeAttempt.created_at <= end_date
    ).group_by(func.date(PracticeAttempt.created_at)).all()
    
    # Average evaluation scores
    avg_score = db.query(
        func.avg(Evaluation.overall_score)
    ).join(PracticeAttempt).filter(
        Evaluation.created_at >= start_date,
        Evaluation.created_at <= end_date
    ).scalar() or 0.0
    
    return {
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "days": days
        },
        "tasks_completed": [
            {"date": str(row.date), "count": row.count}
            for row in completed_tasks
        ],
        "practice_attempts": [
            {"date": str(row.date), "count": row.count}
            for row in attempts
        ],
        "average_evaluation_score": float(avg_score),
        "langsmith_tracing": "enabled" if settings.LANGSMITH_TRACING else "disabled"
    }


@router.get("/traces")
async def get_trace_info():
    """
    Get LangSmith tracing information.
    
    Returns:
        Information about LangSmith tracing configuration.
    """
    return {
        "langsmith_enabled": settings.LANGSMITH_TRACING and bool(settings.LANGSMITH_API_KEY),
        "langsmith_project": settings.LANGSMITH_PROJECT,
        "langsmith_endpoint": "https://api.smith.langchain.com",
        "instructions": {
            "setup": "Set LANGSMITH_API_KEY and LANGSMITH_TRACING=true in .env",
            "view_traces": f"Visit https://smith.langchain.com and select project '{settings.LANGSMITH_PROJECT}'"
        }
    }

