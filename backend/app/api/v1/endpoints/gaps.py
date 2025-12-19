"""
Gap analysis endpoints.
"""
from typing import List, Optional
from datetime import datetime
import logging

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db

logger = logging.getLogger(__name__)
from app.db.models import (
    Document as DocumentModel,
    User,
    Gap,
    SkillEvidence,
)
from app.schemas.skill import GapResponse, GapReportResponse, SkillEvidenceResponse
from app.services.gap_analysis import GapAnalyzer
from app.services.skill_extraction import SkillExtractor
from app.core.serializers import skill_evidence_to_response

router = APIRouter()


@router.post("/analyze", response_model=GapReportResponse)
async def analyze_gaps(
    user_id: int,
    resume_document_id: int,
    jd_document_id: int,
    db: Session = Depends(get_db),
):
    """
    Analyze skill gaps between resume and job description.
    
    - **user_id**: User ID
    - **resume_document_id**: ID of uploaded resume document
    - **jd_document_id**: ID of uploaded job description document
    
    Returns a gap report with prioritized skill gaps.
    """
    # Validate user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get documents
    resume_doc = db.query(DocumentModel).filter(
        DocumentModel.id == resume_document_id,
        DocumentModel.user_id == user_id,
        DocumentModel.document_type == "resume"
    ).first()
    
    if not resume_doc:
        raise HTTPException(
            status_code=404,
            detail=f"Resume document {resume_document_id} not found for user {user_id}"
        )
    
    jd_doc = db.query(DocumentModel).filter(
        DocumentModel.id == jd_document_id,
        DocumentModel.user_id == user_id,
        DocumentModel.document_type == "job_description"
    ).first()
    
    if not jd_doc:
        raise HTTPException(
            status_code=404,
            detail=f"Job description document {jd_document_id} not found for user {user_id}"
        )
    
    # Check if gaps already exist for this user
    existing_gaps = db.query(Gap).filter(
        Gap.user_id == user_id
    ).all()
    
    # Delete existing gaps if any (fresh analysis)
    if existing_gaps:
        for gap in existing_gaps:
            db.delete(gap)
        db.commit()
    
    # Perform gap analysis
    try:
        analyzer = GapAnalyzer()
        gaps = analyzer.analyze_gaps(
            user_id=user_id,
            resume_document=resume_doc,
            jd_document=jd_doc,
            db_session=db
        )
    except ValueError as e:
        # LLM configuration error
        if "API_KEY" in str(e) or "not set" in str(e):
            raise HTTPException(
                status_code=500,
                detail=f"LLM configuration error: {str(e)}. Please set OPENAI_API_KEY in your .env file."
            )
        raise HTTPException(status_code=500, detail=f"Configuration error: {str(e)}")
    except Exception as e:
        # Log the full error for debugging
        import traceback
        logger.error(f"Gap analysis error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Error during gap analysis: {str(e)}. Check backend logs for details."
        )
    
    # Store gaps in database
    for gap in gaps:
        db.add(gap)
    
    # Also extract and store skill evidence
    skill_extractor = SkillExtractor()
    
    # Extract skills from resume and store evidence
    resume_skills = skill_extractor.extract_skills_from_document(
        resume_doc,
        resume_doc.content or ""
    )
    
    for extracted_skill in resume_skills.skills:
        # Get or create skill
        from app.db.models import Skill
        from app.schemas.skill import SkillCategory
        
        try:
            skill_category = SkillCategory(extracted_skill.category.lower())
        except ValueError:
            skill_category = SkillCategory.OTHER
        
        skill = db.query(Skill).filter(
            Skill.name.ilike(extracted_skill.name)
        ).first()
        
        if not skill:
            skill = Skill(
                name=extracted_skill.name,
                category=skill_category,
                description=None
            )
            db.add(skill)
            db.flush()
        
        # Create evidence
        evidence = SkillEvidence(
            skill_id=skill.id,
            document_id=resume_doc.id,
            evidence_text=extracted_skill.evidence,
            section_name=extracted_skill.section_name,
            confidence_score=extracted_skill.confidence,
        )
        db.add(evidence)
    
    db.commit()
    
    # Refresh gaps to get IDs
    for gap in gaps:
        db.refresh(gap)
    
    # Get all gaps with relationships
    all_gaps = db.query(Gap).filter(
        Gap.user_id == user_id
    ).all()
    
    # Build response
    # OPTIMIZATION: Batch load all evidence in one query instead of N+1 queries
    gap_responses = []
    if resume_doc and all_gaps:
        # Load all evidence for all gaps in a single query
        skill_ids = [gap.skill_id for gap in all_gaps]
        all_evidence = db.query(SkillEvidence).filter(
            SkillEvidence.document_id == resume_doc.id,
            SkillEvidence.skill_id.in_(skill_ids)
        ).all()
        
        # Group evidence by skill_id for O(1) lookup
        evidence_by_skill = {}
        for ev in all_evidence:
            if ev.skill_id not in evidence_by_skill:
                evidence_by_skill[ev.skill_id] = []
            evidence_by_skill[ev.skill_id].append(ev)
    else:
        evidence_by_skill = {}
    
    # Build gap responses with pre-loaded evidence
    for gap in all_gaps:
        gap_response = GapResponse.model_validate(gap)
        
        # Get evidence from pre-loaded dictionary
        evidence_list = evidence_by_skill.get(gap.skill_id, [])
        
        # Filter and validate evidence before converting
        valid_evidence = []
        for ev in evidence_list:
            try:
                # Ensure evidence_text meets minimum requirements
                if ev.evidence_text and len(ev.evidence_text.strip()) >= 1:
                    valid_evidence.append(skill_evidence_to_response(ev))
            except Exception as e:
                logger.warning(f"Failed to serialize evidence {ev.id}: {e}")
                continue
        gap_response.evidence = valid_evidence
        gap_responses.append(gap_response)
    
    # Count by priority
    critical_count = sum(1 for g in all_gaps if g.priority.value == "critical")
    high_count = sum(1 for g in all_gaps if g.priority.value == "high")
    
    return GapReportResponse(
        user_id=user_id,
        total_gaps=len(all_gaps),
        critical_gaps=critical_count,
        high_priority_gaps=high_count,
        gaps=gap_responses,
        generated_at=datetime.utcnow(),
    )


@router.get("/report/{user_id}", response_model=GapReportResponse)
async def get_gap_report(
    user_id: int,
    db: Session = Depends(get_db),
):
    """
    Get existing gap report for a user.
    
    - **user_id**: User ID
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    gaps = db.query(Gap).filter(Gap.user_id == user_id).all()
    
    if not gaps:
        raise HTTPException(
            status_code=404,
            detail=f"No gap report found for user {user_id}. Run /analyze first."
        )
    
    # Get resume document for evidence
    resume_doc = db.query(DocumentModel).filter(
        DocumentModel.user_id == user_id,
        DocumentModel.document_type == "resume"
    ).first()
    
    # OPTIMIZATION: Batch load all evidence in one query instead of N+1 queries
    gap_responses = []
    if resume_doc and gaps:
        # Load all evidence for all gaps in a single query
        skill_ids = [gap.skill_id for gap in gaps]
        all_evidence = db.query(SkillEvidence).filter(
            SkillEvidence.document_id == resume_doc.id,
            SkillEvidence.skill_id.in_(skill_ids)
        ).all()
        
        # Group evidence by skill_id for O(1) lookup
        evidence_by_skill = {}
        for ev in all_evidence:
            if ev.skill_id not in evidence_by_skill:
                evidence_by_skill[ev.skill_id] = []
            evidence_by_skill[ev.skill_id].append(ev)
    else:
        evidence_by_skill = {}
    
    # Build gap responses with pre-loaded evidence
    for gap in gaps:
        gap_response = GapResponse.model_validate(gap)
        
        # Get evidence from pre-loaded dictionary
        evidence_list = evidence_by_skill.get(gap.skill_id, [])
        
        # Filter and validate evidence before converting
        valid_evidence = []
        for ev in evidence_list:
            try:
                if ev.evidence_text and len(ev.evidence_text.strip()) >= 1:
                    valid_evidence.append(skill_evidence_to_response(ev))
            except Exception as e:
                logger.warning(f"Failed to serialize evidence {ev.id}: {e}")
                continue
        gap_response.evidence = valid_evidence
        gap_responses.append(gap_response)
    
    critical_count = sum(1 for g in gaps if g.priority.value == "critical")
    high_count = sum(1 for g in gaps if g.priority.value == "high")
    
    return GapReportResponse(
        user_id=user_id,
        total_gaps=len(gaps),
        critical_gaps=critical_count,
        high_priority_gaps=high_count,
        gaps=gap_responses,
        generated_at=gaps[0].created_at if gaps else datetime.utcnow(),
    )

