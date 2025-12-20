"""
Evaluation Agent - Phase 8
Evaluates practice attempts using LLM and rubrics.
"""
import json
import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.core.llm import get_llm
from app.db.models import (
    PracticeAttempt, PracticeItem, Rubric, Evaluation,
    PracticeTypeEnum
)

logger = logging.getLogger(__name__)


class EvaluationAgent:
    """Agent for evaluating practice attempts."""
    
    def __init__(self):
        self.llm = get_llm()
    
    def get_or_create_rubric(
        self, 
        practice_type: PracticeTypeEnum, 
        db: Session
    ) -> Rubric:
        """Get existing rubric or create default one for practice type."""
        # Check if rubric exists
        rubric = db.query(Rubric).filter(
            Rubric.practice_type == practice_type
        ).first()
        
        if rubric:
            return rubric
        
        # Create default rubric based on practice type
        default_rubrics = self._get_default_rubrics()
        rubric_data = default_rubrics.get(practice_type.value)
        
        if not rubric_data:
            raise ValueError(f"No default rubric for practice type: {practice_type}")
        
        rubric = Rubric(
            practice_type=practice_type,
            criteria=rubric_data["criteria"],
            total_max_score=rubric_data["total_max_score"]
        )
        db.add(rubric)
        db.commit()
        db.refresh(rubric)
        
        return rubric
    
    def _get_default_rubrics(self) -> Dict[str, Dict[str, Any]]:
        """Get default rubrics for each practice type."""
        return {
            "quiz": {
                "criteria": [
                    {
                        "name": "Correctness",
                        "description": "Whether the answer is correct",
                        "weight": 0.7,
                        "max_score": 1.0
                    },
                    {
                        "name": "Understanding",
                        "description": "Demonstrates understanding of the concept",
                        "weight": 0.3,
                        "max_score": 1.0
                    }
                ],
                "total_max_score": 1.0
            },
            "flashcard": {
                "criteria": [
                    {
                        "name": "Recall Accuracy",
                        "description": "Ability to recall the correct information",
                        "weight": 1.0,
                        "max_score": 1.0
                    }
                ],
                "total_max_score": 1.0
            },
            "behavioral": {
                "criteria": [
                    {
                        "name": "STAR Structure",
                        "description": "Proper use of Situation, Task, Action, Result framework",
                        "weight": 0.3,
                        "max_score": 1.0
                    },
                    {
                        "name": "Relevance",
                        "description": "Relevance to the question asked",
                        "weight": 0.2,
                        "max_score": 1.0
                    },
                    {
                        "name": "Specificity",
                        "description": "Use of specific examples and details",
                        "weight": 0.2,
                        "max_score": 1.0
                    },
                    {
                        "name": "Impact",
                        "description": "Clear demonstration of impact and results",
                        "weight": 0.3,
                        "max_score": 1.0
                    }
                ],
                "total_max_score": 1.0
            },
            "system_design": {
                "criteria": [
                    {
                        "name": "Requirements Analysis",
                        "description": "Clear identification of functional and non-functional requirements",
                        "weight": 0.2,
                        "max_score": 1.0
                    },
                    {
                        "name": "Architecture Design",
                        "description": "Well-structured system architecture with components",
                        "weight": 0.3,
                        "max_score": 1.0
                    },
                    {
                        "name": "Scalability",
                        "description": "Consideration of scalability and performance",
                        "weight": 0.2,
                        "max_score": 1.0
                    },
                    {
                        "name": "Trade-offs",
                        "description": "Discussion of trade-offs and alternatives",
                        "weight": 0.2,
                        "max_score": 1.0
                    },
                    {
                        "name": "Completeness",
                        "description": "Coverage of all important aspects (data flow, APIs, etc.)",
                        "weight": 0.1,
                        "max_score": 1.0
                    }
                ],
                "total_max_score": 1.0
            }
        }
    
    def evaluate_attempt(
        self, 
        attempt: PracticeAttempt, 
        db: Session
    ) -> Evaluation:
        """Evaluate a practice attempt using LLM and rubric."""
        # Get practice item
        practice_item = db.query(PracticeItem).filter(
            PracticeItem.id == attempt.practice_item_id
        ).first()
        
        if not practice_item:
            raise ValueError(f"Practice item {attempt.practice_item_id} not found")
        
        # Get or create rubric
        rubric = self.get_or_create_rubric(practice_item.practice_type, db)
        
        # Check if evaluation already exists
        existing_eval = db.query(Evaluation).filter(
            Evaluation.practice_attempt_id == attempt.id
        ).first()
        
        if existing_eval:
            return existing_eval
        
        # Generate evaluation using LLM
        evaluation_result = self._llm_evaluate(
            practice_item=practice_item,
            attempt=attempt,
            rubric=rubric
        )
        
        # Create evaluation record
        evaluation = Evaluation(
            practice_attempt_id=attempt.id,
            rubric_id=rubric.id,
            overall_score=evaluation_result["overall_score"],
            criterion_scores=evaluation_result["criterion_scores"],
            strengths=evaluation_result["strengths"],
            weaknesses=evaluation_result["weaknesses"],
            feedback=evaluation_result["feedback"],
            evaluator_notes=evaluation_result.get("evaluator_notes")
        )
        
        db.add(evaluation)
        db.commit()
        db.refresh(evaluation)
        
        return evaluation
    
    def _llm_evaluate(
        self,
        practice_item: PracticeItem,
        attempt: PracticeAttempt,
        rubric: Rubric
    ) -> Dict[str, Any]:
        """Use LLM to evaluate the attempt against the rubric."""
        # Build evaluation prompt
        prompt = self._build_evaluation_prompt(
            practice_item=practice_item,
            attempt=attempt,
            rubric=rubric
        )
        
        try:
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Parse JSON response
            evaluation_data = self._parse_evaluation_response(content)
            
            # Normalize scores
            evaluation_data = self._normalize_scores(evaluation_data, rubric)
            
            return evaluation_data
        except Exception as e:
            logger.error(f"Error in LLM evaluation: {e}")
            # Return default evaluation on error
            return self._default_evaluation(rubric)
    
    def _build_evaluation_prompt(
        self,
        practice_item: PracticeItem,
        attempt: PracticeAttempt,
        rubric: Rubric
    ) -> str:
        """Build the evaluation prompt for the LLM."""
        criteria_text = "\n".join([
            f"- {c['name']}: {c['description']} (weight: {c['weight']}, max: {c['max_score']})"
            for c in rubric.criteria
        ])
        
        prompt = f"""You are an expert evaluator for interview preparation. Evaluate the following practice attempt against the provided rubric.

PRACTICE ITEM:
Type: {practice_item.practice_type.value}
Title: {practice_item.title}
Question: {practice_item.question}
Expected Answer/Key Points: {practice_item.expected_answer or 'N/A'}

USER'S ANSWER:
{attempt.answer}

RUBRIC CRITERIA:
{criteria_text}

EVALUATION INSTRUCTIONS:
1. Score each criterion on a scale of 0.0 to 1.0 (where 1.0 is perfect)
2. Calculate overall score as weighted average: sum(criterion_score * weight) for all criteria
3. Identify 2-3 specific strengths in the answer
4. Identify 2-3 specific weaknesses or areas for improvement
5. Provide constructive, actionable feedback (2-3 sentences)

Return your evaluation as JSON in this exact format:
{{
    "criterion_scores": {{
        "Criterion Name": 0.0-1.0,
        ...
    }},
    "overall_score": 0.0-1.0,
    "strengths": ["strength 1", "strength 2", ...],
    "weaknesses": ["weakness 1", "weakness 2", ...],
    "feedback": "Your detailed feedback here...",
    "evaluator_notes": "Optional internal notes"
}}

Be fair but thorough. Focus on helping the user improve."""
        
        return prompt
    
    def _parse_evaluation_response(self, content: str) -> Dict[str, Any]:
        """Parse LLM response into evaluation data."""
        # Try to extract JSON from markdown code blocks
        if "```json" in content:
            json_start = content.find("```json") + 7
            json_end = content.find("```", json_start)
            content = content[json_start:json_end].strip()
        elif "```" in content:
            json_start = content.find("```") + 3
            json_end = content.find("```", json_start)
            content = content[json_start:json_end].strip()
        
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse JSON, attempting extraction: {content[:200]}")
            # Fallback: try to extract key values
            return self._extract_evaluation_from_text(content)
    
    def _extract_evaluation_from_text(self, text: str) -> Dict[str, Any]:
        """Fallback: extract evaluation data from unstructured text."""
        # This is a simple fallback - in production, you'd want more robust parsing
        return {
            "criterion_scores": {},
            "overall_score": 0.5,
            "strengths": ["Answer provided"],
            "weaknesses": ["Could be improved"],
            "feedback": text[:500] if len(text) > 500 else text,
            "evaluator_notes": "Parsed from unstructured response"
        }
    
    def _normalize_scores(
        self, 
        evaluation_data: Dict[str, Any], 
        rubric: Rubric
    ) -> Dict[str, Any]:
        """Normalize scores to ensure they're within valid ranges."""
        # Normalize criterion scores
        criterion_scores = {}
        for criterion in rubric.criteria:
            criterion_name = criterion["name"]
            score = evaluation_data.get("criterion_scores", {}).get(criterion_name, 0.5)
            # Clamp to [0.0, 1.0]
            score = max(0.0, min(1.0, float(score)))
            criterion_scores[criterion_name] = score
        
        # Calculate overall score from criterion scores if not provided
        if "overall_score" not in evaluation_data or evaluation_data["overall_score"] is None:
            overall_score = sum(
                criterion_scores.get(c["name"], 0.0) * c["weight"]
                for c in rubric.criteria
            )
        else:
            overall_score = max(0.0, min(1.0, float(evaluation_data["overall_score"])))
        
        evaluation_data["criterion_scores"] = criterion_scores
        evaluation_data["overall_score"] = overall_score
        
        # Ensure strengths and weaknesses are lists
        if not isinstance(evaluation_data.get("strengths"), list):
            evaluation_data["strengths"] = []
        if not isinstance(evaluation_data.get("weaknesses"), list):
            evaluation_data["weaknesses"] = []
        
        # Ensure feedback is a string
        if not isinstance(evaluation_data.get("feedback"), str):
            evaluation_data["feedback"] = "Evaluation completed."
        
        return evaluation_data
    
    def _default_evaluation(self, rubric: Rubric) -> Dict[str, Any]:
        """Return a default evaluation when LLM fails."""
        criterion_scores = {
            c["name"]: 0.5 for c in rubric.criteria
        }
        
        return {
            "criterion_scores": criterion_scores,
            "overall_score": 0.5,
            "strengths": ["Answer was submitted"],
            "weaknesses": ["Evaluation pending - please try again"],
            "feedback": "Evaluation could not be completed automatically. Please review your answer.",
            "evaluator_notes": "Default evaluation due to LLM error"
        }

