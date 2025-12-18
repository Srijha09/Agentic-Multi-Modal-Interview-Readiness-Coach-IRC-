"""
Document management endpoints.
"""
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.db.models import Document as DocumentModel
from app.schemas.document import DocumentResponse, ParsedDocument
from app.services.document_parser import get_upload_path, parse_document


router = APIRouter()


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form("resume"),
    user_id: int = Form(...),
    db: Session = Depends(get_db),
):
    """
    Upload a document (resume or job description).

    - **file**: PDF or DOCX file
    - **document_type**: "resume" or "job_description"
    - **user_id**: User ID (required for persistence)
    """

    if document_type not in {"resume", "job_description"}:
        raise HTTPException(status_code=400, detail="Invalid document_type")

    contents = await file.read()
    if len(contents) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="File too large")

    upload_path = get_upload_path(user_id=user_id, file_name=file.filename)
    upload_path.write_bytes(contents)

    # Parse the document
    import logging
    try:
        parsed: ParsedDocument = parse_document(upload_path, document_type=document_type)
        logging.info(f"Successfully parsed {file.filename}: {parsed.section_count} sections, {parsed.chunk_count} chunks, {parsed.char_count} chars")
    except Exception as e:
        # Log the error with full traceback
        import traceback
        error_msg = f"Error parsing document {file.filename}: {str(e)}\n{traceback.format_exc()}"
        logging.error(error_msg)
        print(error_msg)  # Also print to console for immediate visibility
        
        # Try to extract at least the raw text as fallback
        try:
            from app.services.document_parser import extract_text, normalize_whitespace
            raw_text = extract_text(upload_path)
            normalized_text = normalize_whitespace(raw_text)
            logging.info(f"Fallback: Extracted {len(normalized_text)} characters from {file.filename}")
            parsed = ParsedDocument(
                document_type=document_type,
                file_name=file.filename,
                text=normalized_text,
                sections=[],
                chunks=[],
                char_count=len(normalized_text),
                section_count=0,
                chunk_count=0,
            )
        except Exception as e2:
            logging.error(f"Failed to extract text from {file.filename}: {str(e2)}")
            # Last resort: empty document
            parsed = ParsedDocument(
                document_type=document_type,
                file_name=file.filename,
                text="",
                sections=[],
                chunks=[],
                char_count=0,
                section_count=0,
                chunk_count=0,
            )

    db_doc = DocumentModel(
        user_id=user_id,
        document_type=document_type,
        file_path=str(upload_path),
        file_name=file.filename,
        content=parsed.text,
        doc_metadata={
            "sections": [s.model_dump() for s in parsed.sections],
            "chunks": [c.model_dump() for c in parsed.chunks],
            "char_count": parsed.char_count,
            "section_count": parsed.section_count,
            "chunk_count": parsed.chunk_count,
        },
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)

    # Ensure doc_metadata is properly set
    response = DocumentResponse.model_validate(db_doc)
    # Explicitly set doc_metadata if it's None (shouldn't happen, but safety check)
    if response.doc_metadata is None:
        response.doc_metadata = {
            "sections": [s.model_dump() for s in parsed.sections],
            "chunks": [c.model_dump() for c in parsed.chunks],
            "char_count": parsed.char_count,
            "section_count": parsed.section_count,
            "chunk_count": parsed.chunk_count,
        }
    
    return response


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: int, db: Session = Depends(get_db)):
    """Get document by ID, including parsed metadata."""
    doc = db.query(DocumentModel).filter(DocumentModel.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentResponse.model_validate(doc)




