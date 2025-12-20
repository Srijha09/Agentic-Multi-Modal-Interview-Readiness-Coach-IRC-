"""
Mastery tracking endpoints - Phase 9.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.database import get_db
from app.db.models import User, SkillMastery
from app.schemas.mastery import MasteryResponse
from app.services.mastery_tracker import MasteryTracker

router = APIRouter()
mastery_tracker = MasteryTracker()


@router.get("/user/{user_id}", response_model=List[MasteryResponse])
async def get_user_masteries(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get all mastery records for a user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    masteries = mastery_tracker.get_all_user_masteries(user_id, db)
    return [MasteryResponse.model_validate(m) for m in masteries]


@router.get("/user/{user_id}/skill/{skill_name}", response_model=MasteryResponse)
async def get_skill_mastery(
    user_id: int,
    skill_name: str,
    db: Session = Depends(get_db)
):
    """Get mastery for a specific skill."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    mastery = mastery_tracker.get_skill_mastery(user_id, skill_name, db)
    if not mastery:
        raise HTTPException(
            status_code=404,
            detail=f"Mastery record not found for skill: {skill_name}"
        )
    
    return MasteryResponse.model_validate(mastery)


@router.get("/user/{user_id}/stats")
async def get_user_mastery_stats(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get comprehensive mastery statistics for a user (Phase 9)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    stats = mastery_tracker.get_user_mastery_stats(user_id, db)
    return stats

