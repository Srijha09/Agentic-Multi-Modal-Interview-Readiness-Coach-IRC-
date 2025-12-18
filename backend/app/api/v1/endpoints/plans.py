"""
Study plan endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import datetime

from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User, Gap, StudyPlan
from app.schemas.plan import StudyPlanResponse, StudyPlanCreate
from app.services.planner import StudyPlanner
from app.core.serializers import serialize_study_plan

router = APIRouter()


@router.post("/generate", response_model=StudyPlanResponse)
async def generate_plan(
    user_id: int,
    interview_date: Optional[datetime] = None,
    weeks: int = 4,
    hours_per_week: float = 10.0,
    db: Session = Depends(get_db),
):
    """
    Generate a study plan for a user based on their skill gaps.
    
    - **user_id**: User ID
    - **interview_date**: Target interview date (optional)
    - **weeks**: Number of weeks for the plan (default: 4)
    - **hours_per_week**: Hours available per week (default: 10.0)
    """
    # Validate user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user's gaps
    gaps = db.query(Gap).filter(Gap.user_id == user_id).all()
    
    if not gaps:
        raise HTTPException(
            status_code=400,
            detail="No skill gaps found. Please run gap analysis first (/api/v1/gaps/analyze)"
        )
    
    # Check if plan already exists for this user
    existing_plan = db.query(StudyPlan).filter(
        StudyPlan.user_id == user_id
    ).order_by(StudyPlan.created_at.desc()).first()
    
    # Generate new plan
    planner = StudyPlanner()
    study_plan = planner.generate_plan(
        user_id=user_id,
        gaps=gaps,
        interview_date=interview_date,
        weeks=weeks,
        hours_per_week=hours_per_week,
        db_session=db
    )
    
    db.commit()
    db.refresh(study_plan)
    
    # Serialize and return
    plan_dict = serialize_study_plan(study_plan, include_relations=True)
    return StudyPlanResponse.model_validate(plan_dict)


@router.get("/{plan_id}", response_model=StudyPlanResponse)
async def get_plan(plan_id: int, db: Session = Depends(get_db)):
    """Get study plan by ID."""
    plan = db.query(StudyPlan).filter(StudyPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Study plan not found")
    
    plan_dict = serialize_study_plan(plan, include_relations=True)
    return StudyPlanResponse.model_validate(plan_dict)


@router.get("/user/{user_id}/latest")
async def get_latest_plan(user_id: int, db: Session = Depends(get_db)):
    """Get the latest study plan for a user."""
    plan = db.query(StudyPlan).filter(
        StudyPlan.user_id == user_id
    ).order_by(StudyPlan.created_at.desc()).first()
    
    if not plan:
        raise HTTPException(
            status_code=404,
            detail=f"No study plan found for user {user_id}. Generate one first."
        )
    
    plan_dict = serialize_study_plan(plan, include_relations=True)
    return StudyPlanResponse.model_validate(plan_dict)




