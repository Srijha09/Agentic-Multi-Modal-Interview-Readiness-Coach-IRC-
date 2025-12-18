"""
Gap analysis service that compares required skills vs demonstrated skills.

This service:
1. Compares required skills (from JD) vs demonstrated skills (from resume)
2. Determines coverage status (covered, partial, missing)
3. Assigns priority levels (critical, high, medium, low)
4. Generates gap reports with evidence
"""
from typing import List, Dict, Set, Tuple
from collections import defaultdict
import logging

from app.db.models import (
    Skill,
    SkillEvidence,
    Gap,
    Document as DocumentModel,
    User,
)
from app.schemas.skill import CoverageStatus, GapPriority, SkillCategory
from app.services.skill_extraction import SkillExtractor, ExtractedSkill
from app.core.llm import get_llm_with_temperature
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)


class GapAnalyzer:
    """Service for analyzing skill gaps between resume and job requirements."""
    
    def __init__(self):
        try:
            self.skill_extractor = SkillExtractor()
            self.llm = get_llm_with_temperature(temperature=0.3)  # Slight creativity for reasoning
            self._setup_prompts()
        except ValueError as e:
            # Re-raise with more context
            raise ValueError(f"Failed to initialize GapAnalyzer: {str(e)}. Please check LLM configuration.")
        except Exception as e:
            raise ValueError(f"Failed to initialize GapAnalyzer: {str(e)}")
    
    def _setup_prompts(self):
        """Setup prompt for gap analysis reasoning."""
        self.gap_reasoning_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at analyzing skill gaps between a candidate's resume and job requirements.

Given a required skill and evidence from both the resume and job description, determine:
1. Coverage status: COVERED (skill clearly demonstrated), PARTIAL (some evidence but not strong), or MISSING (no evidence)
2. Priority: CRITICAL (essential for role), HIGH (important), MEDIUM (useful), LOW (nice to have)
3. Gap reason: Clear explanation of why this is a gap
4. Estimated learning hours: Rough estimate of hours needed to learn/improve this skill

Be precise and evidence-based."""),
            ("human", """Required skill: {skill_name}
Category: {category}

Job description evidence:
{jd_evidence}

Resume evidence (if any):
{resume_evidence}

Analyze this gap and return JSON:
{{
  "coverage_status": "covered|partial|missing",
  "priority": "critical|high|medium|low",
  "gap_reason": "Detailed explanation",
  "estimated_learning_hours": 0.0
}}""")
        ])
    
    def analyze_gaps(
        self,
        user_id: int,
        resume_document: DocumentModel,
        jd_document: DocumentModel,
        db_session
    ) -> List[Gap]:
        """
        Perform gap analysis between resume and job description.
        
        Args:
            user_id: User ID
            resume_document: Resume document model
            jd_document: Job description document model
            db_session: Database session
        
        Returns:
            List of Gap model instances (not yet committed)
        """
        logger.info(f"Starting gap analysis for user {user_id}")
        
        # Extract skills from both documents
        resume_skills = self.skill_extractor.extract_skills_from_document(
            resume_document,
            resume_document.content or ""
        )
        
        jd_skills = self.skill_extractor.extract_skills_from_document(
            jd_document,
            jd_document.content or ""
        )
        
        logger.info(f"Extracted {len(resume_skills.skills)} skills from resume")
        logger.info(f"Extracted {len(jd_skills.skills)} requirements from job description")
        
        # Normalize skill names (case-insensitive matching)
        resume_skill_map: Dict[str, List[ExtractedSkill]] = defaultdict(list)
        for skill in resume_skills.skills:
            normalized = skill.name.lower().strip()
            resume_skill_map[normalized].append(skill)
        
        jd_skill_map: Dict[str, List[ExtractedSkill]] = defaultdict(list)
        for skill in jd_skills.skills:
            normalized = skill.name.lower().strip()
            jd_skill_map[normalized].append(skill)
        
        # Find all unique required skills
        all_required_skills = set(jd_skill_map.keys())
        
        gaps = []
        
        # Analyze each required skill
        for skill_name_normalized in all_required_skills:
            jd_skill_instances = jd_skill_map[skill_name_normalized]
            resume_skill_instances = resume_skill_map.get(skill_name_normalized, [])
            
            # Get the primary JD skill (highest confidence)
            primary_jd_skill = max(jd_skill_instances, key=lambda s: s.confidence)
            
            # Determine coverage and priority
            coverage, priority, gap_reason, learning_hours = self._analyze_single_gap(
                primary_jd_skill,
                resume_skill_instances,
                jd_skill_instances
            )
            
            # Get or create Skill in database
            skill = self._get_or_create_skill(
                name=primary_jd_skill.name,
                category=primary_jd_skill.category,
                db_session=db_session
            )
            
            # Create evidence for resume skills (if any)
            evidence_summary_parts = []
            if resume_skill_instances:
                for resume_skill in resume_skill_instances:
                    evidence_summary_parts.append(f"Resume: {resume_skill.evidence}")
            else:
                evidence_summary_parts.append("No evidence found in resume")
            
            for jd_skill in jd_skill_instances:
                evidence_summary_parts.append(f"JD: {jd_skill.evidence}")
            
            evidence_summary = " | ".join(evidence_summary_parts)
            
            # Create Gap
            gap = Gap(
                skill_id=skill.id,
                user_id=user_id,
                required_skill_name=primary_jd_skill.name,
                coverage_status=coverage,
                priority=priority,
                gap_reason=gap_reason,
                evidence_summary=evidence_summary,
                estimated_learning_hours=learning_hours,
            )
            
            gaps.append(gap)
        
        logger.info(f"Generated {len(gaps)} gaps for user {user_id}")
        return gaps
    
    def _analyze_single_gap(
        self,
        jd_skill: ExtractedSkill,
        resume_skills: List[ExtractedSkill],
        all_jd_skills: List[ExtractedSkill]
    ) -> Tuple[CoverageStatus, GapPriority, str, float]:
        """
        Analyze a single skill gap using heuristic rules (fast and deterministic).
        
        For more sophisticated analysis, this could use LLM reasoning, but heuristics
        are faster and more cost-effective for initial implementation.
        
        Returns:
            Tuple of (coverage_status, priority, gap_reason, estimated_learning_hours)
        """
        # Prepare evidence
        resume_evidence = "\n".join([f"- {s.evidence} (confidence: {s.confidence:.2f})" for s in resume_skills]) if resume_skills else "None"
        jd_evidence = "\n".join([f"- {s.evidence}" for s in all_jd_skills])
        
        # Determine coverage status
        if not resume_skills:
            # No evidence in resume
            coverage = CoverageStatus.MISSING
        elif len(resume_skills) == 1 and resume_skills[0].confidence < 0.6:
            # Weak or ambiguous evidence
            coverage = CoverageStatus.PARTIAL
        elif any(s.confidence >= 0.7 for s in resume_skills):
            # Strong evidence exists
            coverage = CoverageStatus.COVERED
        else:
            # Multiple weak pieces of evidence
            coverage = CoverageStatus.PARTIAL
        
        # Determine priority based on JD confidence and coverage
        if coverage == CoverageStatus.MISSING:
            # Missing skills: priority based on how required they are
            if jd_skill.confidence >= 0.9:
                priority = GapPriority.CRITICAL
            elif jd_skill.confidence >= 0.7:
                priority = GapPriority.HIGH
            elif jd_skill.confidence >= 0.5:
                priority = GapPriority.MEDIUM
            else:
                priority = GapPriority.LOW
        elif coverage == CoverageStatus.PARTIAL:
            # Partial coverage: medium priority to strengthen
            if jd_skill.confidence >= 0.8:
                priority = GapPriority.HIGH
            elif jd_skill.confidence >= 0.6:
                priority = GapPriority.MEDIUM
            else:
                priority = GapPriority.LOW
        else:
            # Covered: low priority (not really a gap, but track for completeness)
            priority = GapPriority.LOW
        
        # Generate gap reason
        if coverage == CoverageStatus.MISSING:
            gap_reason = (
                f"Required skill '{jd_skill.name}' not found in resume. "
                f"Job description requires: {jd_skill.evidence}"
            )
        elif coverage == CoverageStatus.PARTIAL:
            gap_reason = (
                f"Skill '{jd_skill.name}' mentioned in resume but evidence is weak or incomplete. "
                f"Resume shows: {resume_skills[0].evidence if resume_skills else 'N/A'}. "
                f"Job description requires: {jd_skill.evidence}"
            )
        else:
            gap_reason = (
                f"Skill '{jd_skill.name}' is demonstrated in resume: "
                f"{resume_skills[0].evidence if resume_skills else 'N/A'}"
            )
        
        # Estimate learning hours
        learning_hours = self._estimate_learning_hours(jd_skill.category, coverage)
        
        return coverage, priority, gap_reason, learning_hours
    
    def _estimate_learning_hours(self, category: str, coverage: CoverageStatus) -> float:
        """
        Estimate learning hours based on skill category and coverage status.
        
        This is a heuristic - can be improved with LLM reasoning.
        """
        base_hours = {
            "programming": 40.0,
            "framework": 20.0,
            "database": 15.0,
            "cloud": 30.0,
            "tool": 10.0,
            "soft_skill": 20.0,
            "domain": 40.0,
            "other": 15.0,
        }
        
        base = base_hours.get(category.lower(), 20.0)
        
        if coverage == CoverageStatus.PARTIAL:
            return base * 0.5  # Half the time if partially covered
        else:
            return base
    
    def _get_or_create_skill(
        self,
        name: str,
        category: str,
        db_session
    ) -> Skill:
        """
        Get existing skill or create new one.
        
        Args:
            name: Skill name
            category: Skill category
            db_session: Database session
        
        Returns:
            Skill model instance
        """
        # Try to find existing skill (case-insensitive)
        skill = db_session.query(Skill).filter(
            Skill.name.ilike(name)
        ).first()
        
        if not skill:
            # Create new skill
            try:
                skill_category = SkillCategory(category.lower())
            except ValueError:
                skill_category = SkillCategory.OTHER
            
            skill = Skill(
                name=name,
                category=skill_category,
                description=None
            )
            db_session.add(skill)
            db_session.flush()  # Get ID without committing
        
        return skill

