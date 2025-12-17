"""
Database models for Interview Readiness Coach.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, JSON, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum


# Enums for database
class SkillCategoryEnum(str, enum.Enum):
    PROGRAMMING = "programming"
    FRAMEWORK = "framework"
    DATABASE = "database"
    CLOUD = "cloud"
    TOOL = "tool"
    SOFT_SKILL = "soft_skill"
    DOMAIN = "domain"
    OTHER = "other"


class CoverageStatusEnum(str, enum.Enum):
    COVERED = "covered"
    PARTIAL = "partial"
    MISSING = "missing"


class GapPriorityEnum(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskTypeEnum(str, enum.Enum):
    LEARN = "learn"
    PRACTICE = "practice"
    REVIEW = "review"


class TaskStatusEnum(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class PracticeTypeEnum(str, enum.Enum):
    QUIZ = "quiz"
    FLASHCARD = "flashcard"
    CODING = "coding"
    BEHAVIORAL = "behavioral"
    SYSTEM_DESIGN = "system_design"


class DifficultyLevelEnum(str, enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class User(Base):
    """User model."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    study_plans = relationship("StudyPlan", back_populates="user", cascade="all, delete-orphan")
    practice_attempts = relationship("PracticeAttempt", back_populates="user", cascade="all, delete-orphan")
    skill_mastery = relationship("SkillMastery", back_populates="user", cascade="all, delete-orphan")
    gaps = relationship("Gap", back_populates="user", cascade="all, delete-orphan")


class Document(Base):
    """Document model for resumes and job descriptions."""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    document_type = Column(String, nullable=False)  # resume, job_description
    file_path = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    content = Column(Text, nullable=True)
    doc_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="documents")
    skill_evidence = relationship("SkillEvidence", back_populates="document", cascade="all, delete-orphan")


class Skill(Base):
    """Skill model."""
    __tablename__ = "skills"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, nullable=False, index=True)
    category = Column(SQLEnum(SkillCategoryEnum), nullable=False)
    description = Column(Text, nullable=True)
    parent_skill_id = Column(Integer, ForeignKey("skills.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    parent_skill = relationship("Skill", remote_side=[id], backref="child_skills")
    skill_evidence = relationship("SkillEvidence", back_populates="skill", cascade="all, delete-orphan")
    gaps = relationship("Gap", back_populates="skill", cascade="all, delete-orphan")


class SkillEvidence(Base):
    """Skill evidence model - links skills to document sections."""
    __tablename__ = "skill_evidence"
    
    id = Column(Integer, primary_key=True, index=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    evidence_text = Column(Text, nullable=False)
    section_name = Column(String, nullable=True)
    confidence_score = Column(Float, nullable=False, default=0.0)  # 0.0 to 1.0
    start_char = Column(Integer, nullable=True)
    end_char = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    skill = relationship("Skill", back_populates="skill_evidence")
    document = relationship("Document", back_populates="skill_evidence")
    
    # Indexes
    __table_args__ = (
        Index("idx_skill_document", "skill_id", "document_id"),
    )


class Gap(Base):
    """Gap model - represents skill gaps between resume and job requirements."""
    __tablename__ = "gaps"
    
    id = Column(Integer, primary_key=True, index=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    required_skill_name = Column(String(200), nullable=False)
    coverage_status = Column(SQLEnum(CoverageStatusEnum), nullable=False)
    priority = Column(SQLEnum(GapPriorityEnum), nullable=False)
    gap_reason = Column(Text, nullable=False)
    evidence_summary = Column(Text, nullable=True)
    estimated_learning_hours = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    skill = relationship("Skill", back_populates="gaps")
    user = relationship("User", back_populates="gaps")
    
    # Indexes
    __table_args__ = (
        Index("idx_user_skill_gap", "user_id", "skill_id"),
    )


class StudyPlan(Base):
    """Study plan model."""
    __tablename__ = "study_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    interview_date = Column(DateTime(timezone=True), nullable=True)
    weeks = Column(Integer, nullable=False)
    hours_per_week = Column(Float, nullable=False, default=10.0)
    focus_areas = Column(JSON, nullable=True)  # List of skill names
    plan_data = Column(JSON, nullable=False)  # Full plan structure
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="study_plans")
    daily_tasks = relationship("DailyTask", back_populates="study_plan", cascade="all, delete-orphan")
    weeks_data = relationship("Week", back_populates="study_plan", cascade="all, delete-orphan")
    calendar_events = relationship("CalendarEvent", back_populates="study_plan", cascade="all, delete-orphan")


class Week(Base):
    """Week model - represents a week in a study plan."""
    __tablename__ = "weeks"
    
    id = Column(Integer, primary_key=True, index=True)
    study_plan_id = Column(Integer, ForeignKey("study_plans.id"), nullable=False)
    week_number = Column(Integer, nullable=False)
    theme = Column(String(200), nullable=False)
    focus_skills = Column(JSON, nullable=True)  # List of skill names
    estimated_hours = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    study_plan = relationship("StudyPlan", back_populates="weeks_data")
    days = relationship("Day", back_populates="week", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_plan_week", "study_plan_id", "week_number"),
    )


class Day(Base):
    """Day model - represents a day in a week."""
    __tablename__ = "days"
    
    id = Column(Integer, primary_key=True, index=True)
    week_id = Column(Integer, ForeignKey("weeks.id"), nullable=False)
    day_number = Column(Integer, nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)
    theme = Column(String(200), nullable=True)
    estimated_hours = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    week = relationship("Week", back_populates="days")
    tasks = relationship("DailyTask", back_populates="day", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_week_day", "week_id", "day_number"),
    )


class DailyTask(Base):
    """Daily task model."""
    __tablename__ = "daily_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    study_plan_id = Column(Integer, ForeignKey("study_plans.id"), nullable=False)
    day_id = Column(Integer, ForeignKey("days.id"), nullable=True)
    task_date = Column(DateTime(timezone=True), nullable=False)
    task_type = Column(SQLEnum(TaskTypeEnum), nullable=False)
    status = Column(SQLEnum(TaskStatusEnum), nullable=False, default=TaskStatusEnum.PENDING)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    skill_names = Column(JSON, nullable=True)  # List of skill names
    estimated_minutes = Column(Integer, nullable=False)
    actual_minutes = Column(Integer, nullable=True)
    dependencies = Column(JSON, nullable=True)  # List of task IDs
    content = Column(JSON, nullable=False)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    study_plan = relationship("StudyPlan", back_populates="daily_tasks")
    day = relationship("Day", back_populates="tasks")
    practice_attempts = relationship("PracticeAttempt", back_populates="task")
    practice_items = relationship("PracticeItem", back_populates="task")
    calendar_events = relationship("CalendarEvent", back_populates="task")


class PracticeItem(Base):
    """Practice item model (quizzes, flashcards, prompts)."""
    __tablename__ = "practice_items"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("daily_tasks.id"), nullable=True)
    practice_type = Column(SQLEnum(PracticeTypeEnum), nullable=False)
    title = Column(String(200), nullable=False)
    question = Column(Text, nullable=False)
    skill_names = Column(JSON, nullable=True)  # List of skill names
    difficulty = Column(SQLEnum(DifficultyLevelEnum), nullable=False)
    content = Column(JSON, nullable=True)  # Flexible content (options, hints, etc.)
    expected_answer = Column(Text, nullable=True)
    rubric = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    task = relationship("DailyTask", back_populates="practice_items")
    practice_attempts = relationship("PracticeAttempt", back_populates="practice_item", cascade="all, delete-orphan")


class PracticeAttempt(Base):
    """Practice attempt model (quizzes, flashcards, prompts)."""
    __tablename__ = "practice_attempts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    practice_item_id = Column(Integer, ForeignKey("practice_items.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("daily_tasks.id"), nullable=True)
    answer = Column(Text, nullable=False)
    time_spent_seconds = Column(Integer, nullable=True)
    score = Column(Float, nullable=True)  # 0.0 to 1.0
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="practice_attempts")
    practice_item = relationship("PracticeItem", back_populates="practice_attempts")
    task = relationship("DailyTask", back_populates="practice_attempts")
    evaluation = relationship("Evaluation", back_populates="practice_attempt", uselist=False, cascade="all, delete-orphan")


class Evaluation(Base):
    """Evaluation model - stores LLM-based evaluations of practice attempts."""
    __tablename__ = "evaluations"
    
    id = Column(Integer, primary_key=True, index=True)
    practice_attempt_id = Column(Integer, ForeignKey("practice_attempts.id"), nullable=False, unique=True)
    rubric_id = Column(Integer, ForeignKey("rubrics.id"), nullable=True)
    overall_score = Column(Float, nullable=False)  # 0.0 to 1.0
    criterion_scores = Column(JSON, nullable=True)  # Dict of criterion_name -> score
    strengths = Column(JSON, nullable=True)  # List of strings
    weaknesses = Column(JSON, nullable=True)  # List of strings
    feedback = Column(Text, nullable=False)
    evaluator_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    practice_attempt = relationship("PracticeAttempt", back_populates="evaluation")
    rubric = relationship("Rubric", back_populates="evaluations")


class Rubric(Base):
    """Rubric model - defines evaluation criteria."""
    __tablename__ = "rubrics"
    
    id = Column(Integer, primary_key=True, index=True)
    practice_type = Column(SQLEnum(PracticeTypeEnum), nullable=False)
    criteria = Column(JSON, nullable=False)  # List of criterion objects
    total_max_score = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    evaluations = relationship("Evaluation", back_populates="rubric")


class SkillMastery(Base):
    """Skill mastery tracking model."""
    __tablename__ = "skill_mastery"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    skill_name = Column(String(200), nullable=False, index=True)
    mastery_score = Column(Float, default=0.0)  # 0.0 to 1.0
    last_practiced = Column(DateTime(timezone=True), nullable=True)
    practice_count = Column(Integer, default=0)
    improvement_trend = Column(String, nullable=True)  # "improving", "stable", "declining"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="skill_mastery")
    
    # Indexes
    __table_args__ = (
        Index("idx_user_skill_mastery", "user_id", "skill_name", unique=True),
    )


class CalendarEvent(Base):
    """Calendar event model for ICS export."""
    __tablename__ = "calendar_events"
    
    id = Column(Integer, primary_key=True, index=True)
    study_plan_id = Column(Integer, ForeignKey("study_plans.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("daily_tasks.id"), nullable=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    location = Column(String, nullable=True)
    recurrence_rule = Column(String, nullable=True)  # RRULE format
    ics_uid = Column(String, unique=True, nullable=True)  # Unique identifier for ICS
    synced = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    study_plan = relationship("StudyPlan", back_populates="calendar_events")
    task = relationship("DailyTask", back_populates="calendar_events")




