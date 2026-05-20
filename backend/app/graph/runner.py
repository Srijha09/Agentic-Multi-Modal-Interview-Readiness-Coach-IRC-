"""
GraphRunner — invokes compiled LangGraph workflows with DB session context.
"""
import logging
from datetime import date, datetime
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.graph.state import CoachState
from app.graph import graphs
from app.core.tracing import build_run_config, is_langsmith_enabled

logger = logging.getLogger(__name__)


class GraphRunner:
    """Facade for running LangGraph workflows."""

    def _invoke(
        self,
        graph,
        initial: CoachState,
        *,
        run_name: str,
        extra_metadata: Optional[dict] = None,
    ) -> CoachState:
        user_id = initial.get("user_id")
        if user_id == 0:
            user_id = None

        invoke_kwargs = {}
        if is_langsmith_enabled():
            invoke_kwargs["config"] = build_run_config(
                run_name,
                user_id=user_id,
                metadata=extra_metadata,
            )

        result = graph.invoke(initial, **invoke_kwargs)
        if result.get("error"):
            logger.error("Graph workflow error: %s", result["error"])
        return result

    def run_gap_analysis(
        self,
        db: Session,
        user_id: int,
        resume_document_id: int,
        jd_document_id: int,
    ) -> CoachState:
        state: CoachState = {
            "user_id": user_id,
            "db_session": db,
            "resume_document_id": resume_document_id,
            "jd_document_id": jd_document_id,
            "run_plan_after_gap": False,
            "messages": [],
        }
        return self._invoke(
            graphs.gap_analysis_graph,
            state,
            run_name="gap_analysis",
            extra_metadata={
                "resume_document_id": resume_document_id,
                "jd_document_id": jd_document_id,
            },
        )

    def run_onboarding(
        self,
        db: Session,
        user_id: int,
        resume_document_id: int,
        jd_document_id: int,
        *,
        weeks: int = 4,
        hours_per_week: float = 10.0,
        interview_date: Optional[datetime] = None,
        generate_plan: bool = True,
    ) -> CoachState:
        state: CoachState = {
            "user_id": user_id,
            "db_session": db,
            "resume_document_id": resume_document_id,
            "jd_document_id": jd_document_id,
            "weeks": weeks,
            "hours_per_week": hours_per_week,
            "interview_date": interview_date,
            "run_plan_after_gap": generate_plan,
            "messages": [],
        }
        return self._invoke(
            graphs.onboarding_graph,
            state,
            run_name="onboarding",
            extra_metadata={
                "resume_document_id": resume_document_id,
                "jd_document_id": jd_document_id,
                "generate_plan": generate_plan,
            },
        )

    def run_plan_generation(
        self,
        db: Session,
        user_id: int,
        *,
        weeks: int = 4,
        hours_per_week: float = 10.0,
        interview_date: Optional[datetime] = None,
    ) -> CoachState:
        state: CoachState = {
            "user_id": user_id,
            "db_session": db,
            "weeks": weeks,
            "hours_per_week": hours_per_week,
            "interview_date": interview_date,
            "messages": [],
        }
        return self._invoke(
            graphs.plan_graph,
            state,
            run_name="plan_generation",
            extra_metadata={"weeks": weeks, "hours_per_week": hours_per_week},
        )

    def run_daily_briefing(
        self,
        db: Session,
        user_id: int,
        *,
        target_date: Optional[date] = None,
        study_plan_id: Optional[int] = None,
    ) -> CoachState:
        state: CoachState = {
            "user_id": user_id,
            "db_session": db,
            "target_date": target_date,
            "study_plan_id": study_plan_id,
            "messages": [],
        }
        return self._invoke(
            graphs.daily_coach_graph,
            state,
            run_name="daily_briefing",
            extra_metadata={"study_plan_id": study_plan_id},
        )

    def run_practice_generation(
        self,
        db: Session,
        task_id: int,
        practice_type: str,
        count: int = 1,
    ) -> CoachState:
        state: CoachState = {
            "user_id": 0,  # resolved from task inside node
            "db_session": db,
            "task_id": task_id,
            "practice_type": practice_type,
            "practice_count": count,
            "messages": [],
        }
        return self._invoke(
            graphs.practice_graph,
            state,
            run_name="practice_generation",
            extra_metadata={"task_id": task_id, "practice_type": practice_type},
        )

    def run_learning_loop(
        self,
        db: Session,
        attempt: Any,
        *,
        run_adapt: bool = False,
        study_plan_id: Optional[int] = None,
        user_id: Optional[int] = None,
    ) -> CoachState:
        state: CoachState = {
            "user_id": user_id or attempt.user_id,
            "db_session": db,
            "attempt": attempt,
            "attempt_id": attempt.id,
            "study_plan_id": study_plan_id,
            "run_adapt_after_eval": run_adapt,
            "apply_adaptations": True,
            "messages": [],
        }
        return self._invoke(
            graphs.learning_loop_graph,
            state,
            run_name="learning_loop",
            extra_metadata={
                "attempt_id": attempt.id,
                "run_adapt": run_adapt,
            },
        )

    def run_adaptive_planning(
        self,
        db: Session,
        user_id: int,
        study_plan_id: Optional[int] = None,
        apply_recommendations: bool = True,
    ) -> CoachState:
        state: CoachState = {
            "user_id": user_id,
            "db_session": db,
            "study_plan_id": study_plan_id,
            "apply_adaptations": apply_recommendations,
            "messages": [],
        }
        return self._invoke(
            graphs.adaptive_graph,
            state,
            run_name="adaptive_planning",
            extra_metadata={"study_plan_id": study_plan_id},
        )


_runner: Optional[GraphRunner] = None


def get_graph_runner() -> GraphRunner:
    global _runner
    if _runner is None:
        _runner = GraphRunner()
    return _runner
