"""Skill, SkillEvidence, and Gap schemas."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class SkillCategory(str, Enum):
    """Skill categories."""
    PROGRAMMING = "programming"
    FRAMEWORK = "framework"
    DATABASE = "database"
    CLOUD = "cloud"
    TOOL = "tool"
    SOFT_SKILL = "soft_skill"
    DOMAIN = "domain"
    OTHER = "other"


class CoverageStatus(str, Enum):
    """Coverage status for skills."""
    COVERED = "covered"
    PARTIAL = "partial"
    MISSING = "missing"


class GapPriority(str, Enum):
    """Gap priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SkillBase(BaseModel):
    """Base skill schema."""
    name: str = Field(..., min_length=1, max_length=200)
    category: SkillCategory
    description: Optional[str] = None
    parent_skill_id: Optional[int] = None  # For skill hierarchy


class SkillCreate(SkillBase):
    """Schema for creating a skill."""
    pass


class SkillResponse(SkillBase):
    """Schema for skill response."""
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class SkillEvidenceBase(BaseModel):
    """Base skill evidence schema."""
    skill_id: int
    document_id: int
    evidence_text: str = Field(..., min_length=1)  # Allow shorter evidence (skill names are valid)
    section_name: Optional[str] = None  # e.g., "Experience", "Projects"
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    start_char: Optional[int] = None  # Character position in document
    end_char: Optional[int] = None


class SkillEvidenceCreate(SkillEvidenceBase):
    """Schema for creating skill evidence."""
    pass


class SkillEvidenceResponse(SkillEvidenceBase):
    """Schema for skill evidence response."""
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class GapBase(BaseModel):
    """Base gap schema."""
    skill_id: int
    user_id: int
    required_skill_name: str
    coverage_status: CoverageStatus
    priority: GapPriority
    gap_reason: str  # Explanation of why this is a gap
    evidence_summary: Optional[str] = None  # Summary of evidence
    estimated_learning_hours: Optional[float] = None


class GapCreate(GapBase):
    """Schema for creating a gap."""
    pass


class GapResponse(GapBase):
    """Schema for gap response."""
    id: int
    created_at: datetime
    skill: Optional[SkillResponse] = None
    evidence: List[SkillEvidenceResponse] = []

    model_config = {"from_attributes": True}


class GapReportResponse(BaseModel):
    """Schema for gap report response."""
    user_id: int
    total_gaps: int
    critical_gaps: int
    high_priority_gaps: int
    gaps: List[GapResponse]
    generated_at: datetime

    model_config = {"from_attributes": True}

