"""Document schemas."""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict


class DocumentType(str):
    """Document types."""

    RESUME = "resume"
    JOB_DESCRIPTION = "job_description"


class DocumentChunk(BaseModel):
    """
    A small chunk of document text suitable for vectorization.
    """

    text: str
    section_name: Optional[str] = None
    start_char: Optional[int] = None
    end_char: Optional[int] = None


class DocumentSection(BaseModel):
    """
    High‑level logical section of a document, e.g. Experience, Education, Requirements.
    """

    name: str
    text: str
    start_char: Optional[int] = None
    end_char: Optional[int] = None


class ParsedDocument(BaseModel):
    """
    Parsed representation shared across agents:
    - raw text
    - sections
    - chunks
    """

    document_type: str = Field(..., pattern="^(resume|job_description)$")
    file_name: str
    text: str
    sections: List[DocumentSection]
    chunks: List[DocumentChunk]
    char_count: int
    section_count: int
    chunk_count: int
    metadata: Optional[Dict[str, Any]] = None


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


class DocumentResponse(BaseModel):
    """Schema for document response."""

    id: int
    user_id: int
    document_type: str
    file_name: str
    file_path: str
    content: str

    doc_metadata: Optional[Dict[str, Any]] = None

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

