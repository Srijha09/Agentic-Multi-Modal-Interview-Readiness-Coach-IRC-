"""Document schemas."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any


class DocumentType(str):
    """Document types."""
    RESUME = "resume"
    JOB_DESCRIPTION = "job_description"


class DocumentBase(BaseModel):
    """Base document schema."""
    document_type: str = Field(..., pattern="^(resume|job_description)$")
    file_name: str
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class DocumentCreate(DocumentBase):
    """Schema for creating a document."""
    user_id: int
    file_path: str


class DocumentResponse(DocumentBase):
    """Schema for document response."""
    id: int
    user_id: int
    file_path: str
    created_at: datetime

    model_config = {"from_attributes": True}

