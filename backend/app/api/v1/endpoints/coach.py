"""
Daily Coach Agent endpoints (Phase 6).
"""
import logging
from typing import Optional
from datetime import date

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User, DailyTask
from app.schemas.coach import (
    DailyBriefingResponse,
    TaskUpdateRequest,
    TaskRescheduleRequest,
    TaskRescheduleResponse,
    CarryOverSummary,
)
from app.services.daily_coach import DailyCoach

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/briefing", response_model=DailyBriefingResponse)
async def get_daily_briefing(
    user_id: int = Query(..., description="User ID"),
    target_date: Optional[date] = Query(None, description="Date for briefing (defaults to today)"),
    study_plan_id: Optional[int] = Query(None, description="Specific study plan ID (uses latest if not provided)"),
    db: Session = Depends(get_db),
):
    """
    Get daily briefing for a user.
    
    Returns:
        DailyBriefingResponse with tasks, progress, and motivational message
    """
    try:
        # Validate user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        coach = DailyCoach()
        briefing = coach.get_daily_briefing(
            user_id=user_id,
            target_date=target_date,
            study_plan_id=study_plan_id,
            db_session=db
        )
        
        return briefing
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting daily briefing: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@router.post("/tasks/{task_id}/complete")
async def complete_task(
    task_id: int,
    actual_minutes: Optional[int] = Query(None, description="Actual minutes spent"),
    db: Session = Depends(get_db),
):
    """
    Mark a task as completed.
    
    - **task_id**: Task ID to mark as completed
    - **actual_minutes**: Optional actual time spent
    """
    try:
        coach = DailyCoach()
        task = coach.update_task_status(
            task_id=task_id,
            status="completed",
            actual_minutes=actual_minutes,
            db_session=db
        )
        
        return {
            "task_id": task.id,
            "status": task.status.value,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "message": "Task marked as completed"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error completing task: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@router.post("/tasks/{task_id}/update", response_model=dict)
async def update_task(
    task_id: int,
    request: TaskUpdateRequest,
    db: Session = Depends(get_db),
):
    """
    Update task status.
    
    - **task_id**: Task ID
    - **status**: New status (pending, in_progress, completed, skipped)
    - **actual_minutes**: Optional actual time spent
    """
    try:
        coach = DailyCoach()
        task = coach.update_task_status(
            task_id=task_id,
            status=request.status,
            actual_minutes=request.actual_minutes,
            db_session=db
        )
        
        return {
            "task_id": task.id,
            "status": task.status.value,
            "actual_minutes": task.actual_minutes,
            "message": f"Task updated to {request.status}"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating task: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@router.post("/tasks/{task_id}/reschedule", response_model=TaskRescheduleResponse)
async def reschedule_task(
    task_id: int,
    request: TaskRescheduleRequest,
    db: Session = Depends(get_db),
):
    """
    Reschedule a task to a new date.
    
    - **task_id**: Task ID
    - **new_date**: New date for the task
    - **reason**: Optional reason for rescheduling
    """
    try:
        coach = DailyCoach()
        response = coach.reschedule_task(
            task_id=task_id,
            new_date=request.new_date,
            reason=request.reason,
            db_session=db
        )
        
        return response
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error rescheduling task: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@router.post("/carry-over", response_model=CarryOverSummary)
async def carry_over_tasks(
    user_id: int = Query(..., description="User ID"),
    from_date: date = Query(..., description="Date to carry tasks from"),
    to_date: date = Query(..., description="Date to carry tasks to"),
    study_plan_id: Optional[int] = Query(None, description="Specific study plan ID (uses latest if not provided)"),
    db: Session = Depends(get_db),
):
    """
    Carry over incomplete tasks from one date to another.
    
    - **user_id**: User ID
    - **from_date**: Date to carry tasks from
    - **to_date**: Date to carry tasks to
    - **study_plan_id**: Optional specific study plan ID
    """
    try:
        # Validate user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        coach = DailyCoach()
        summary = coach.process_carry_over(
            user_id=user_id,
            from_date=from_date,
            to_date=to_date,
            study_plan_id=study_plan_id,
            db_session=db
        )
        
        return summary
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error carrying over tasks: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@router.post("/auto-reschedule", response_model=dict)
async def auto_reschedule_overdue(
    user_id: int = Query(..., description="User ID"),
    target_date: Optional[date] = Query(None, description="Target date to reschedule to (defaults to today)"),
    study_plan_id: Optional[int] = Query(None, description="Specific study plan ID (uses latest if not provided)"),
    db: Session = Depends(get_db),
):
    """
    Automatically reschedule overdue tasks.
    
    - **user_id**: User ID
    - **target_date**: Target date to reschedule to (defaults to today)
    - **study_plan_id**: Optional specific study plan ID
    """
    try:
        # Validate user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        coach = DailyCoach()
        rescheduled = coach.auto_reschedule_overdue_tasks(
            user_id=user_id,
            target_date=target_date,
            study_plan_id=study_plan_id,
            db_session=db
        )
        
        return {
            "rescheduled_count": len(rescheduled),
            "rescheduled_tasks": [r.model_dump() for r in rescheduled],
            "message": f"Successfully rescheduled {len(rescheduled)} overdue task(s)"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error auto-rescheduling tasks: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@router.post("/enrich-tasks", response_model=dict)
async def enrich_tasks_with_content(
    user_id: int = Query(..., description="User ID"),
    study_plan_id: Optional[int] = Query(None, description="Specific study plan ID (uses latest if not provided)"),
    db: Session = Depends(get_db),
):
    """
    Enrich tasks with study materials and resources.
    Updates tasks that don't have content populated.
    
    - **user_id**: User ID
    - **study_plan_id**: Optional specific study plan ID
    """
    try:
        from app.db.models import StudyPlan
        from app.services.planner import StudyPlanner
        
        # Validate user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get study plan
        if study_plan_id:
            study_plan = db.query(StudyPlan).filter(
                StudyPlan.id == study_plan_id,
                StudyPlan.user_id == user_id
            ).first()
        else:
            study_plan = db.query(StudyPlan).filter(
                StudyPlan.user_id == user_id
            ).order_by(StudyPlan.created_at.desc()).first()
        
        if not study_plan:
            raise HTTPException(status_code=404, detail="No study plan found for user")
        
        # Get tasks without content
        from app.db.models import DailyTask
        tasks = db.query(DailyTask).filter(
            DailyTask.study_plan_id == study_plan.id,
            ((DailyTask.content == {}) | (DailyTask.content == None))
        ).all()
        
        if not tasks:
            return {
                "enriched_count": 0,
                "message": "All tasks already have content"
            }
        
        planner = StudyPlanner()
        enriched_count = 0
        
        for task in tasks:
            try:
                # Generate content for this task
                content = planner._generate_task_content(
                    title=task.title,
                    description=task.description,
                    skill_names=task.skill_names if task.skill_names else [],
                    task_type=task.task_type.value
                )
                
                # Update task
                task.content = content
                enriched_count += 1
            except Exception as e:
                logger.warning(f"Failed to enrich task {task.id}: {e}")
                continue
        
        db.commit()
        
        return {
            "enriched_count": enriched_count,
            "total_tasks": len(tasks),
            "message": f"Successfully enriched {enriched_count} task(s) with study materials and resources"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enriching tasks: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

