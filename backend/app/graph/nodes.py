"""
LangGraph node implementations — each node delegates to an existing service.
"""
import logging
from typing import Any, Dict, Optional

from app.graph.state import CoachState
from app.db.models import (
    Document as DocumentModel,
    Gap,
    User,
    DailyTask,
    PracticeAttempt,
    PracticeTypeEnum,
    StudyPlan,
    Skill,
    SkillEvidence,
)
from app.schemas.skill import SkillCategory
from app.services.gap_analysis import GapAnalyzer
from app.services.skill_extraction import SkillExtractor
from app.services.planner import StudyPlanner
from app.services.daily_coach import DailyCoach
from app.services.practice_generator import PracticeGenerator
from app.services.evaluator import EvaluationAgent
from app.services.mastery_tracker import MasteryTracker
from app.services.adaptive_planner import AdaptivePlanner

logger = logging.getLogger(__name__)

_gap_analyzer: Optional[GapAnalyzer] = None
_skill_extractor: Optional[SkillExtractor] = None
_planner: Optional[StudyPlanner] = None
_daily_coach: Optional[DailyCoach] = None
_practice_generator: Optional[PracticeGenerator] = None
_evaluator: Optional[EvaluationAgent] = None
_mastery_tracker: Optional[MasteryTracker] = None
_adaptive_planner: Optional[AdaptivePlanner] = None


def _db(state: CoachState):
    db = state.get("db_session")
    if db is None:
        raise RuntimeError("db_session missing from CoachState")
    return db


def _append_message(state: CoachState, message: str) -> Dict[str, Any]:
    messages = list(state.get("messages") or [])
    messages.append(message)
    return {"messages": messages}


def validate_intake_node(state: CoachState) -> Dict[str, Any]:
    """Validate user and uploaded documents exist."""
    db = _db(state)
    user_id = state["user_id"]
    resume_id = state.get("resume_document_id")
    jd_id = state.get("jd_document_id")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"error": f"User {user_id} not found"}

    if not resume_id or not jd_id:
        return {"error": "resume_document_id and jd_document_id are required"}

    resume_doc = db.query(DocumentModel).filter(
        DocumentModel.id == resume_id,
        DocumentModel.user_id == user_id,
        DocumentModel.document_type == "resume",
    ).first()
    if not resume_doc:
        return {"error": f"Resume document {resume_id} not found"}

    jd_doc = db.query(DocumentModel).filter(
        DocumentModel.id == jd_id,
        DocumentModel.user_id == user_id,
        DocumentModel.document_type == "job_description",
    ).first()
    if not jd_doc:
        return {"error": f"Job description document {jd_id} not found"}

    return _append_message(state, "Intake validated")


def gap_analysis_node(state: CoachState) -> Dict[str, Any]:
    """Run gap analysis and persist gaps + resume skill evidence."""
    if state.get("error"):
        return {}

    db = _db(state)
    user_id = state["user_id"]
    resume_id = state["resume_document_id"]
    jd_id = state["jd_document_id"]

    resume_doc = db.query(DocumentModel).filter(DocumentModel.id == resume_id).first()
    jd_doc = db.query(DocumentModel).filter(DocumentModel.id == jd_id).first()

    existing_gaps = db.query(Gap).filter(Gap.user_id == user_id).all()
    for gap in existing_gaps:
        db.delete(gap)
    db.commit()

    global _gap_analyzer, _skill_extractor
    if _gap_analyzer is None:
        _gap_analyzer = GapAnalyzer()
    if _skill_extractor is None:
        _skill_extractor = SkillExtractor()

    try:
        gaps = _gap_analyzer.analyze_gaps(
            user_id=user_id,
            resume_document=resume_doc,
            jd_document=jd_doc,
            db_session=db,
        )
    except Exception as exc:
        logger.exception("Gap analysis failed")
        return {"error": str(exc)}

    for gap in gaps:
        db.add(gap)

    resume_skills = _skill_extractor.extract_skills_from_document(
        resume_doc,
        resume_doc.content or "",
    )
    for extracted_skill in resume_skills.skills:
        try:
            skill_category = SkillCategory(extracted_skill.category.lower())
        except ValueError:
            skill_category = SkillCategory.OTHER

        skill = db.query(Skill).filter(Skill.name.ilike(extracted_skill.name)).first()
        if not skill:
            skill = Skill(
                name=extracted_skill.name,
                category=skill_category,
                description=None,
            )
            db.add(skill)
            db.flush()

        evidence = SkillEvidence(
            skill_id=skill.id,
            document_id=resume_doc.id,
            evidence_text=extracted_skill.evidence,
            section_name=extracted_skill.section_name,
            confidence_score=extracted_skill.confidence,
        )
        db.add(evidence)

    db.commit()
    for gap in gaps:
        db.refresh(gap)

    updates = {"gaps": gaps}
    updates.update(_append_message(state, f"Gap analysis complete ({len(gaps)} gaps)"))
    return updates


def planner_node(state: CoachState) -> Dict[str, Any]:
    """Generate a study plan from analyzed gaps."""
    if state.get("error"):
        return {}

    db = _db(state)
    user_id = state["user_id"]
    gaps = state.get("gaps")

    if not gaps:
        gaps = db.query(Gap).filter(Gap.user_id == user_id).all()
    if not gaps:
        return {"error": "No skill gaps found. Run gap analysis first."}

    global _planner
    if _planner is None:
        _planner = StudyPlanner()

    try:
        study_plan = _planner.generate_plan(
            user_id=user_id,
            gaps=gaps,
            interview_date=state.get("interview_date"),
            weeks=state.get("weeks", 4),
            hours_per_week=state.get("hours_per_week", 10.0),
            db_session=db,
        )
        db.commit()
        db.refresh(study_plan)
    except Exception as exc:
        logger.exception("Plan generation failed")
        return {"error": str(exc)}

    updates = {
        "study_plan": study_plan,
        "study_plan_id": study_plan.id,
    }
    updates.update(_append_message(state, f"Study plan {study_plan.id} generated"))
    return updates


def daily_coach_node(state: CoachState) -> Dict[str, Any]:
    """Produce daily briefing via Daily Coach agent."""
    if state.get("error"):
        return {}

    db = _db(state)
    global _daily_coach
    if _daily_coach is None:
        _daily_coach = DailyCoach()

    try:
        briefing = _daily_coach.get_daily_briefing(
            user_id=state["user_id"],
            target_date=state.get("target_date"),
            study_plan_id=state.get("study_plan_id"),
            db_session=db,
        )
    except Exception as exc:
        logger.exception("Daily coach briefing failed")
        return {"error": str(exc)}

    updates = {"briefing": briefing}
    updates.update(_append_message(state, "Daily briefing ready"))
    return updates


def practice_generator_node(state: CoachState) -> Dict[str, Any]:
    """Generate practice items for a task."""
    if state.get("error"):
        return {}

    db = _db(state)
    task_id = state.get("task_id")
    if not task_id:
        return {"error": "task_id is required"}

    task = db.query(DailyTask).filter(DailyTask.id == task_id).first()
    if not task:
        return {"error": f"Task {task_id} not found"}

    practice_type = (state.get("practice_type") or "quiz").lower()
    try:
        practice_type_enum = PracticeTypeEnum(practice_type)
    except ValueError:
        return {"error": f"Invalid practice type: {practice_type}"}

    global _practice_generator
    if _practice_generator is None:
        _practice_generator = PracticeGenerator()

    user_id = task.study_plan.user_id
    count = state.get("practice_count", 1)

    try:
        items = _practice_generator.generate_for_task(
            task=task,
            practice_type=practice_type_enum,
            user_id=user_id,
            db=db,
            count=count,
        )
        db.commit()
    except Exception as exc:
        logger.exception("Practice generation failed")
        return {"error": str(exc)}

    updates = {"practice_items": items}
    updates.update(_append_message(state, f"Generated {len(items)} practice item(s)"))
    return updates


def evaluation_node(state: CoachState) -> Dict[str, Any]:
    """Evaluate a practice attempt."""
    if state.get("error"):
        return {}

    db = _db(state)
    attempt = state.get("attempt")
    if not attempt and state.get("attempt_id"):
        attempt = db.query(PracticeAttempt).filter(
            PracticeAttempt.id == state["attempt_id"]
        ).first()
    if not attempt:
        return {"error": "No practice attempt to evaluate"}

    global _evaluator
    if _evaluator is None:
        _evaluator = EvaluationAgent()

    try:
        evaluation = _evaluator.evaluate_attempt(attempt, db)
        attempt.score = evaluation.overall_score
        attempt.feedback = evaluation.feedback
        db.commit()
        db.refresh(attempt)
    except Exception as exc:
        logger.exception("Evaluation failed")
        return {"error": str(exc)}

    updates = {"evaluation": evaluation, "attempt": attempt}
    updates.update(_append_message(state, "Attempt evaluated"))
    return updates


def mastery_update_node(state: CoachState) -> Dict[str, Any]:
    """Update mastery scores from evaluation."""
    if state.get("error"):
        return {}

    evaluation = state.get("evaluation")
    if not evaluation:
        return _append_message(state, "Skipped mastery update (no evaluation)")

    db = _db(state)
    global _mastery_tracker
    if _mastery_tracker is None:
        _mastery_tracker = MasteryTracker()

    try:
        _mastery_tracker.update_mastery_from_evaluation(evaluation, db)
        db.commit()
    except Exception as exc:
        logger.warning("Mastery update failed: %s", exc)
        return _append_message(state, f"Mastery update warning: {exc}")

    return _append_message(state, "Mastery scores updated")


def adaptive_planner_node(state: CoachState) -> Dict[str, Any]:
    """Adapt study plan based on mastery performance."""
    if state.get("error"):
        return {}

    if not state.get("apply_adaptations", True):
        return _append_message(state, "Adaptation skipped")

    db = _db(state)
    user_id = state["user_id"]
    study_plan_id = state.get("study_plan_id")

    if study_plan_id:
        study_plan = db.query(StudyPlan).filter(
            StudyPlan.id == study_plan_id,
            StudyPlan.user_id == user_id,
        ).first()
    else:
        study_plan = (
            db.query(StudyPlan)
            .filter(StudyPlan.user_id == user_id)
            .order_by(StudyPlan.created_at.desc())
            .first()
        )

    if not study_plan:
        return {"error": "No study plan found for adaptation"}

    global _adaptive_planner
    if _adaptive_planner is None:
        _adaptive_planner = AdaptivePlanner()

    try:
        result = _adaptive_planner.adapt_plan(
            user_id,
            study_plan.id,
            state.get("apply_adaptations", True),
            db,
        )
        db.commit()
    except Exception as exc:
        logger.exception("Adaptive planning failed")
        return {"error": str(exc)}

    updates = {
        "adaptation_result": result,
        "study_plan_id": study_plan.id,
    }
    updates.update(_append_message(state, "Study plan adapted"))
    return updates


def route_after_gap(state: CoachState) -> str:
    if state.get("error"):
        return "end"
    if state.get("run_plan_after_gap"):
        return "planner"
    return "end"


def route_after_eval(state: CoachState) -> str:
    if state.get("error"):
        return "end"
    if state.get("run_adapt_after_eval"):
        return "adapt"
    return "end"
