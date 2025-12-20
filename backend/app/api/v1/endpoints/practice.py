"""
Practice endpoints (quizzes, flashcards, prompts) - Phase 7 & 8.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import Optional, List

from app.db.database import get_db
from app.db.models import (
    PracticeItem, PracticeAttempt, PracticeTypeEnum,
    DailyTask, User, Evaluation
)
from app.schemas.practice import (
    PracticeItemResponse, PracticeAttemptCreate,
    PracticeAttemptResponse
)
from app.schemas.evaluation import EvaluationResponse
from app.services.practice_generator import PracticeGenerator
from app.services.evaluator import EvaluationAgent

router = APIRouter()
practice_generator = PracticeGenerator()
evaluator = EvaluationAgent()


@router.post("/items/generate", response_model=List[PracticeItemResponse])
async def generate_practice_items(
    task_id: int,
    practice_type: str,
    count: int = 1,
    db: Session = Depends(get_db)
):
    """
    Generate practice items for a task.
    
    - **task_id**: Daily task ID
    - **practice_type**: quiz, flashcard, behavioral, system_design
    - **count**: Number of items to generate
    """
    task = db.query(DailyTask).filter(DailyTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    try:
        practice_type_enum = PracticeTypeEnum(practice_type.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid practice type. Must be one of: {[e.value for e in PracticeTypeEnum]}"
        )
    
    user_id = task.study_plan.user_id
    
    practice_items = practice_generator.generate_for_task(
        task=task,
        practice_type=practice_type_enum,
        user_id=user_id,
        db=db,
        count=count
    )
    
    db.commit()
    
    return [PracticeItemResponse.model_validate(item) for item in practice_items]


@router.get("/items/task/{task_id}", response_model=List[PracticeItemResponse])
async def get_practice_items_for_task(
    task_id: int,
    practice_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all practice items for a task."""
    query = db.query(PracticeItem).filter(PracticeItem.task_id == task_id)
    
    if practice_type:
        try:
            practice_type_enum = PracticeTypeEnum(practice_type.lower())
            query = query.filter(PracticeItem.practice_type == practice_type_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid practice type")
    
    items = query.all()
    return [PracticeItemResponse.model_validate(item) for item in items]


@router.get("/items/{item_id}", response_model=PracticeItemResponse)
async def get_practice_item(
    item_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific practice item."""
    item = db.query(PracticeItem).filter(PracticeItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Practice item not found")
    
    return PracticeItemResponse.model_validate(item)


@router.post("/attempts/submit", response_model=PracticeAttemptResponse)
async def submit_attempt(
    attempt_data: PracticeAttemptCreate,
    db: Session = Depends(get_db)
):
    """
    Submit a practice attempt and automatically evaluate it (Phase 8).
    
    The attempt is immediately evaluated using the Evaluation Agent.
    """
    try:
        # Verify practice item exists
        practice_item = db.query(PracticeItem).filter(
            PracticeItem.id == attempt_data.practice_item_id
        ).first()
        if not practice_item:
            raise HTTPException(status_code=404, detail="Practice item not found")
        
        # Verify user exists
        user = db.query(User).filter(User.id == attempt_data.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Verify task exists if task_id is provided
        if attempt_data.task_id is not None:
            task = db.query(DailyTask).filter(DailyTask.id == attempt_data.task_id).first()
            if not task:
                raise HTTPException(status_code=404, detail="Task not found")
        
        # Create attempt
        attempt = PracticeAttempt(
            user_id=attempt_data.user_id,
            practice_item_id=attempt_data.practice_item_id,
            task_id=attempt_data.task_id,
            answer=attempt_data.answer,
            time_spent_seconds=attempt_data.time_spent_seconds,
            score=None,  # Will be set by evaluation
            feedback=None  # Will be set by evaluation
        )
        
        db.add(attempt)
        db.commit()
        db.refresh(attempt)
        
        # Phase 8: Automatically evaluate the attempt
        try:
            evaluation = evaluator.evaluate_attempt(attempt, db)
            # Update attempt with evaluation scores
            attempt.score = evaluation.overall_score
            attempt.feedback = evaluation.feedback
            db.commit()
            db.refresh(attempt)
            # Reload with evaluation relationship
            db.refresh(attempt)
            attempt = db.query(PracticeAttempt).options(
                joinedload(PracticeAttempt.evaluation)
            ).filter(PracticeAttempt.id == attempt.id).first()
        except Exception as eval_error:
            # Log evaluation error but don't fail the submission
            import logging
            logging.error(f"Evaluation failed for attempt {attempt.id}: {eval_error}")
            # Attempt is still saved, just without evaluation
        
        # Build response with evaluation
        response_data = PracticeAttemptResponse.model_validate(attempt)
        if attempt.evaluation:
            from app.schemas.evaluation import EvaluationResponse
            response_data.evaluation = EvaluationResponse.model_validate(attempt.evaluation)
        return response_data
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        import traceback
        error_detail = str(e)
        print(f"Error submitting practice attempt: {error_detail}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit practice attempt: {error_detail}"
        )


@router.get("/attempts/{attempt_id}", response_model=PracticeAttemptResponse)
async def get_attempt(
    attempt_id: int,
    db: Session = Depends(get_db)
):
    """Get practice attempt by ID with evaluation (Phase 8)."""
    attempt = db.query(PracticeAttempt).options(
        joinedload(PracticeAttempt.evaluation)
    ).filter(
        PracticeAttempt.id == attempt_id
    ).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    
    response = PracticeAttemptResponse.model_validate(attempt)
    if attempt.evaluation:
        from app.schemas.evaluation import EvaluationResponse
        response.evaluation = EvaluationResponse.model_validate(attempt.evaluation)
    return response


@router.get("/attempts/{attempt_id}/evaluation", response_model=EvaluationResponse)
async def get_attempt_evaluation(
    attempt_id: int,
    db: Session = Depends(get_db)
):
    """Get evaluation for a practice attempt (Phase 8)."""
    attempt = db.query(PracticeAttempt).filter(
        PracticeAttempt.id == attempt_id
    ).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    
    evaluation = db.query(Evaluation).filter(
        Evaluation.practice_attempt_id == attempt_id
    ).first()
    
    if not evaluation:
        raise HTTPException(
            status_code=404, 
            detail="Evaluation not found. The attempt may not have been evaluated yet."
        )
    
    return EvaluationResponse.model_validate(evaluation)


@router.post("/attempts/{attempt_id}/evaluate", response_model=EvaluationResponse)
async def evaluate_attempt(
    attempt_id: int,
    db: Session = Depends(get_db)
):
    """Manually trigger evaluation for a practice attempt (Phase 8)."""
    attempt = db.query(PracticeAttempt).filter(
        PracticeAttempt.id == attempt_id
    ).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    
    # Check if evaluation already exists
    existing_eval = db.query(Evaluation).filter(
        Evaluation.practice_attempt_id == attempt_id
    ).first()
    
    if existing_eval:
        return EvaluationResponse.model_validate(existing_eval)
    
    # Create new evaluation
    try:
        evaluation = evaluator.evaluate_attempt(attempt, db)
        # Update attempt with evaluation scores
        attempt.score = evaluation.overall_score
        attempt.feedback = evaluation.feedback
        db.commit()
        db.refresh(attempt)
        return EvaluationResponse.model_validate(evaluation)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to evaluate attempt: {str(e)}"
        )




