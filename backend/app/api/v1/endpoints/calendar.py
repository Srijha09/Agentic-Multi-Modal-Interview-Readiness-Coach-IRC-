"""
Calendar API endpoints - Phase 11
"""
from typing import Optional
from fastapi import APIRouter, Query, HTTPException, Depends, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from io import BytesIO

from app.db.database import get_db
from app.db.models import User, StudyPlan
from app.services.calendar_service import CalendarService

router = APIRouter()


@router.post("/generate")
async def generate_calendar_events(
    user_id: int = Query(..., description="User ID"),
    study_plan_id: Optional[int] = Query(None, description="Study plan ID (uses latest if not provided)"),
    regenerate: bool = Query(False, description="Regenerate existing events"),
    db: Session = Depends(get_db),
):
    """
    Generate calendar events from study plan tasks.
    
    - **user_id**: User ID
    - **study_plan_id**: Optional specific study plan ID
    - **regenerate**: If True, delete existing events and regenerate
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
        
        # Generate calendar events
        service = CalendarService()
        events = service.generate_calendar_events_from_plan(
            study_plan.id, user_id, db, regenerate=regenerate
        )
        
        db.commit()
        
        return {
            "study_plan_id": study_plan.id,
            "events_generated": len(events),
            "events": [
                {
                    "id": e.id,
                    "title": e.title,
                    "start_time": e.start_time.isoformat(),
                    "end_time": e.end_time.isoformat(),
                    "task_id": e.task_id
                }
                for e in events
            ]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@router.get("/export")
async def export_calendar_ics(
    user_id: int = Query(..., description="User ID"),
    study_plan_id: Optional[int] = Query(None, description="Study plan ID (uses latest if not provided)"),
    calendar_name: Optional[str] = Query(None, description="Calendar name"),
    db: Session = Depends(get_db),
):
    """
    Export study plan as ICS (iCalendar) file.
    
    - **user_id**: User ID
    - **study_plan_id**: Optional specific study plan ID
    - **calendar_name**: Optional calendar name
    
    Returns an ICS file that can be imported into Google Calendar, Outlook, etc.
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
        
        # Generate ICS file
        service = CalendarService()
        calendar_name = calendar_name or f"Study Plan {study_plan.id}"
        ics_content = service.generate_ics_file(
            study_plan.id, user_id, db, calendar_name
        )
        
        # Create file-like object
        ics_bytes = ics_content.encode('utf-8')
        ics_file = BytesIO(ics_bytes)
        
        # Return as downloadable file
        filename = f"study_plan_{study_plan.id}.ics"
        
        return StreamingResponse(
            iter([ics_bytes]),
            media_type="text/calendar",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": "text/calendar; charset=utf-8"
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@router.post("/regenerate")
async def regenerate_calendar(
    user_id: int = Query(..., description="User ID"),
    study_plan_id: Optional[int] = Query(None, description="Study plan ID (uses latest if not provided)"),
    db: Session = Depends(get_db),
):
    """
    Regenerate calendar events for a study plan.
    Useful when plan is updated.
    
    - **user_id**: User ID
    - **study_plan_id**: Optional specific study plan ID
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
        
        # Regenerate calendar
        service = CalendarService()
        result = service.regenerate_calendar(study_plan.id, user_id, db)
        
        db.commit()
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

