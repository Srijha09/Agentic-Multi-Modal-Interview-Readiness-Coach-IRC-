"""
Skill extraction service using LLM to extract skills from documents.

This service extracts:
- Skills from resume (demonstrated skills)
- Requirements from job description (required skills)
- Evidence snippets linking skills to document sections
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import logging

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

from app.core.llm import get_llm
from app.db.models import Document as DocumentModel
from app.schemas.skill import SkillCategory


logger = logging.getLogger(__name__)


class ExtractedSkill(BaseModel):
    """Represents a skill extracted from a document."""
    name: str = Field(..., description="Skill name (e.g., 'Python', 'Machine Learning')")
    category: str = Field(..., description="Skill category")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    evidence: str = Field(..., description="Evidence text from document")
    section_name: Optional[str] = Field(None, description="Document section where found")


class SkillExtractionResult(BaseModel):
    """Result of skill extraction from a document."""
    skills: List[ExtractedSkill]
    document_type: str  # "resume" or "job_description"


class SkillExtractor:
    """Service for extracting skills from documents using LLM."""
    
    def __init__(self):
        try:
            self.llm = get_llm()
            self._setup_prompts()
        except ValueError as e:
            # Re-raise with more context
            raise ValueError(f"Failed to initialize SkillExtractor: {str(e)}. Please check LLM configuration in .env file.")
        except Exception as e:
            raise ValueError(f"Failed to initialize SkillExtractor: {str(e)}")
    
    def _setup_prompts(self):
        """Setup prompt templates for skill extraction."""
        
        # Resume skill extraction prompt
        self.resume_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at analyzing resumes and extracting technical and professional skills.

Your task is to extract ALL skills demonstrated in the resume, including:
- Programming languages (Python, Java, JavaScript, etc.)
- Frameworks and libraries (React, Django, TensorFlow, etc.)
- Tools and platforms (AWS, Docker, Kubernetes, etc.)
- Databases (PostgreSQL, MongoDB, etc.)
- Soft skills (Leadership, Communication, etc.)
- Domain expertise (Machine Learning, Web Development, etc.)

For each skill, provide:
1. The skill name (standardized, e.g., "Python" not "python programming")
2. Category (programming, framework, database, cloud, tool, soft_skill, domain, other)
3. Confidence score (0.0 to 1.0) based on how clearly the skill is demonstrated
4. Evidence text (exact quote or paraphrase from the resume)
5. Section name (Experience, Education, Projects, Skills, etc.)

Return a JSON array of skills. Be thorough but accurate."""),
            ("human", """Extract all skills from this resume:

{document_text}

Return a JSON array with this structure:
[
  {{
    "name": "Python",
    "category": "programming",
    "confidence": 0.95,
    "evidence": "Developed machine learning models using Python and scikit-learn",
    "section_name": "Experience"
  }},
  ...
]

Only include skills that are clearly demonstrated. Return an empty array if no skills found.""")
        ])
        
        # Job description requirement extraction prompt
        self.jd_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at analyzing job descriptions and extracting required skills and qualifications.

Your task is to extract ALL skills and requirements mentioned in the job description, including:
- Required programming languages
- Required frameworks and technologies
- Required tools and platforms
- Required databases
- Required soft skills
- Required domain knowledge
- Preferred/optional skills (mark with lower confidence)

For each requirement, provide:
1. The skill name (standardized)
2. Category (programming, framework, database, cloud, tool, soft_skill, domain, other)
3. Confidence score (0.0 to 1.0) - higher for required, lower for preferred
4. Evidence text (exact quote from job description)
5. Section name (Requirements, Qualifications, Nice to Have, etc.)

Return a JSON array of required skills."""),
            ("human", """Extract all required and preferred skills from this job description:

{document_text}

Return a JSON array with this structure:
[
  {{
    "name": "Python",
    "category": "programming",
    "confidence": 1.0,
    "evidence": "5+ years of Python development experience required",
    "section_name": "Requirements"
  }},
  ...
]

Include both required and preferred skills. Mark preferred skills with lower confidence (0.6-0.8).""")
        ])
        
        # JSON parser
        self.json_parser = JsonOutputParser(pydantic_object=None)  # We'll parse manually
    
    def extract_skills_from_document(
        self,
        document: DocumentModel,
        document_text: str
    ) -> SkillExtractionResult:
        """
        Extract skills from a document using LLM.
        
        Args:
            document: Document model instance
            document_text: Full text content of the document
        
        Returns:
            SkillExtractionResult with extracted skills
        """
        try:
            # Select appropriate prompt based on document type
            if document.document_type == "resume":
                prompt = self.resume_prompt
            elif document.document_type == "job_description":
                prompt = self.jd_prompt
            else:
                raise ValueError(f"Unknown document type: {document.document_type}")
            
            # Format prompt with document text
            formatted_prompt = prompt.format_messages(document_text=document_text)
            
            # Call LLM
            logger.info(f"Extracting skills from {document.document_type} document {document.id}")
            response = self.llm.invoke(formatted_prompt)
            
            # Parse JSON response
            content = response.content
            # Remove markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            skills_data = json.loads(content)
            
            # Convert to ExtractedSkill objects
            extracted_skills = []
            for skill_data in skills_data:
                try:
                    # Ensure evidence is meaningful - if it's too short, use skill name with context
                    evidence = skill_data.get("evidence", "")
                    if len(evidence) < 10:
                        # If evidence is just the skill name, create a better evidence string
                        evidence = f"Skill '{skill_data['name']}' mentioned in document"
                    
                    skill = ExtractedSkill(
                        name=skill_data["name"],
                        category=skill_data.get("category", "other"),
                        confidence=float(skill_data.get("confidence", 0.5)),
                        evidence=evidence,
                        section_name=skill_data.get("section_name"),
                    )
                    extracted_skills.append(skill)
                except Exception as e:
                    logger.warning(f"Failed to parse skill: {skill_data}, error: {e}")
                    continue
            
            logger.info(f"Extracted {len(extracted_skills)} skills from document {document.id}")
            
            return SkillExtractionResult(
                skills=extracted_skills,
                document_type=document.document_type
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.error(f"Response content: {response.content if 'response' in locals() else 'N/A'}")
            return SkillExtractionResult(skills=[], document_type=document.document_type)
        except Exception as e:
            logger.error(f"Error extracting skills from document {document.id}: {e}", exc_info=True)
            return SkillExtractionResult(skills=[], document_type=document.document_type)

