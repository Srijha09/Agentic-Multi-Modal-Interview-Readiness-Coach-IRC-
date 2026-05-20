"""
LangGraph orchestration endpoints.
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User
from app.graph.runner import get_graph_runner
from app.core.serializers import serialize_study_plan
from app.schemas.plan import StudyPlanResponse

router = APIRouter()


@router.post("/onboarding")
async def run_onboarding_graph(
    user_id: int = Query(...),
    resume_document_id: int = Query(...),
    jd_document_id: int = Query(...),
    weeks: int = Query(4, ge=1, le=52),
    hours_per_week: float = Query(10.0, ge=0.5),
    interview_date: Optional[datetime] = Query(None),
    generate_plan: bool = Query(True),
    db: Session = Depends(get_db),
):
    """
    Run the full onboarding LangGraph workflow:
    validate intake → gap analysis → (optional) study plan generation.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    runner = get_graph_runner()
    try:
        result = runner.run_onboarding(
            db=db,
            user_id=user_id,
            resume_document_id=resume_document_id,
            jd_document_id=jd_document_id,
            weeks=weeks,
            hours_per_week=hours_per_week,
            interview_date=interview_date,
            generate_plan=generate_plan,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["error"])

    gaps = result.get("gaps") or []
    study_plan = result.get("study_plan")

    response = {
        "workflow": "onboarding",
        "messages": result.get("messages", []),
        "gap_count": len(gaps),
        "study_plan_id": study_plan.id if study_plan else None,
    }

    if study_plan:
        plan_dict = serialize_study_plan(study_plan, include_relations=True)
        response["study_plan"] = StudyPlanResponse.model_validate(plan_dict)

    return response
