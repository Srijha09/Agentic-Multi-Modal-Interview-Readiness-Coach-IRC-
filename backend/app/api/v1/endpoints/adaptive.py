"""
Adaptive Planning API endpoints - Phase 10
"""
from typing import Optional
from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User, StudyPlan
from app.services.adaptive_planner import AdaptivePlanner

router = APIRouter()


@router.get("/analyze")
async def analyze_plan_adaptation(
    user_id: int = Query(..., description="User ID"),
    study_plan_id: Optional[int] = Query(None, description="Study plan ID (uses latest if not provided)"),
    db: Session = Depends(get_db),
):
    """
    Analyze study plan and mastery data to determine adaptation needs.
    
    Returns recommendations for:
    - Adding reinforcement tasks for weak skills
    - Reducing repetition for strong skills
    """
    try:
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
        
        # Analyze adaptation needs
        planner = AdaptivePlanner()
        analysis = planner.analyze_plan_adaptation_needs(
            user_id, study_plan.id, db
        )
        
        return {
            "study_plan_id": study_plan.id,
            "analysis": analysis,
            "recommendations_count": len(analysis["recommendations"])
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@router.post("/adapt")
async def adapt_study_plan(
    user_id: int = Query(..., description="User ID"),
    study_plan_id: Optional[int] = Query(None, description="Study plan ID (uses latest if not provided)"),
    apply_recommendations: bool = Query(True, description="Automatically apply recommendations"),
    db: Session = Depends(get_db),
):
    """
    Adapt study plan based on mastery data.
    
    - Analyzes weak/strong skills
    - Adds reinforcement tasks for weak skills
    - Reduces repetition for strong skills
    - Logs all changes
    """
    try:
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
        
        # Adapt plan
        planner = AdaptivePlanner()
        result = planner.adapt_plan(
            user_id, study_plan.id, apply_recommendations, db
        )
        
        db.commit()
        
        return {
            "study_plan_id": study_plan.id,
            "success": True,
            "summary": result["summary"],
            "changes": result["changes"],
            "analysis": result["analysis"]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@router.post("/reinforce")
async def add_reinforcement_tasks(
    user_id: int = Query(..., description="User ID"),
    study_plan_id: Optional[int] = Query(None, description="Study plan ID (uses latest if not provided)"),
    skill_name: str = Query(..., description="Skill name to reinforce"),
    count: int = Query(2, description="Number of reinforcement tasks to add"),
    db: Session = Depends(get_db),
):
    """
    Add reinforcement practice tasks for a specific weak skill.
    """
    try:
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
        
        # Add reinforcement tasks
        planner = AdaptivePlanner()
        tasks = planner.add_reinforcement_tasks(
            user_id, study_plan.id, skill_name, count, db
        )
        
        db.commit()
        
        return {
            "study_plan_id": study_plan.id,
            "skill_name": skill_name,
            "tasks_added": len(tasks),
            "task_ids": [t.id for t in tasks],
            "tasks": [
                {
                    "id": t.id,
                    "title": t.title,
                    "task_date": t.task_date.isoformat() if t.task_date else None,
                    "estimated_minutes": t.estimated_minutes
                }
                for t in tasks
            ]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

