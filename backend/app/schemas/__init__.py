"""Pydantic schemas for API validation and serialization."""

from app.schemas.user import UserCreate, UserResponse
from app.schemas.skill import (
    SkillCreate,
    SkillResponse,
    SkillEvidenceCreate,
    SkillEvidenceResponse,
    GapCreate,
    GapResponse,
    GapReportResponse,
)
from app.schemas.plan import (
    StudyPlanCreate,
    StudyPlanResponse,
    WeekResponse,
    DayResponse,
    TaskCreate,
    TaskResponse,
)
from app.schemas.practice import (
    PracticeItemCreate,
    PracticeItemResponse,
    PracticeAttemptCreate,
    PracticeAttemptResponse,
)
from app.schemas.evaluation import (
    EvaluationCreate,
    EvaluationResponse,
    RubricResponse,
)
from app.schemas.mastery import MasteryResponse, MasteryUpdate
from app.schemas.calendar import CalendarEventCreate, CalendarEventResponse
from app.schemas.document import DocumentCreate, DocumentResponse

__all__ = [
    # User
    "UserCreate",
    "UserResponse",
    # Skill
    "SkillCreate",
    "SkillResponse",
    "SkillEvidenceCreate",
    "SkillEvidenceResponse",
    "GapCreate",
    "GapResponse",
    "GapReportResponse",
    # Plan
    "StudyPlanCreate",
    "StudyPlanResponse",
    "WeekResponse",
    "DayResponse",
    "TaskCreate",
    "TaskResponse",
    # Practice
    "PracticeItemCreate",
    "PracticeItemResponse",
    "PracticeAttemptCreate",
    "PracticeAttemptResponse",
    # Evaluation
    "EvaluationCreate",
    "EvaluationResponse",
    "RubricResponse",
    # Mastery
    "MasteryResponse",
    "MasteryUpdate",
    # Calendar
    "CalendarEventCreate",
    "CalendarEventResponse",
    # Document
    "DocumentCreate",
    "DocumentResponse",
]

