"""
Database models for Interview Readiness Coach.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class User(Base):
    """User model."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    documents = relationship("Document", back_populates="user")
    study_plans = relationship("StudyPlan", back_populates="user")
    practice_attempts = relationship("PracticeAttempt", back_populates="user")


class Document(Base):
    """Document model for resumes and job descriptions."""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    document_type = Column(String, nullable=False)  # resume, job_description
    file_path = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    content = Column(Text, nullable=True)
    doc_metadata  = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="documents")


class StudyPlan(Base):
    """Study plan model."""
    __tablename__ = "study_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    interview_date = Column(DateTime(timezone=True), nullable=True)
    weeks = Column(Integer, nullable=False)
    plan_data = Column(JSON, nullable=False)  # Full plan structure
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="study_plans")
    daily_tasks = relationship("DailyTask", back_populates="study_plan")


class DailyTask(Base):
    """Daily task model."""
    __tablename__ = "daily_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    study_plan_id = Column(Integer, ForeignKey("study_plans.id"), nullable=False)
    task_date = Column(DateTime(timezone=True), nullable=False)
    task_type = Column(String, nullable=False)  # learn, practice, review
    content = Column(JSON, nullable=False)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    study_plan = relationship("StudyPlan", back_populates="daily_tasks")


class PracticeAttempt(Base):
    """Practice attempt model (quizzes, flashcards, prompts)."""
    __tablename__ = "practice_attempts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("daily_tasks.id"), nullable=True)
    practice_type = Column(String, nullable=False)  # quiz, flashcard, coding, behavioral
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=True)
    score = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="practice_attempts")


class SkillMastery(Base):
    """Skill mastery tracking model."""
    __tablename__ = "skill_mastery"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    skill_name = Column(String, nullable=False, index=True)
    mastery_score = Column(Float, default=0.0)  # 0.0 to 1.0
    last_practiced = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())



