"""
Practice Generator Service (Phase 7).

Generates quizzes, flashcards, behavioral prompts, and system design prompts
aligned with skill gaps and difficulty levels.
"""
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from langchain_core.prompts import ChatPromptTemplate
from sqlalchemy.orm import Session

from app.core.llm import get_llm_with_temperature
from app.db.models import (
    PracticeItem, PracticeTypeEnum, DifficultyLevelEnum,
    DailyTask, SkillMastery
)

logger = logging.getLogger(__name__)


class PracticeGenerator:
    """Service for generating practice materials aligned with skills and difficulty."""
    
    def __init__(self):
        self.llm = get_llm_with_temperature(temperature=0.8)  # Creative for question generation
        self._setup_prompts()
    
    def _setup_prompts(self):
        """Setup prompt templates for practice generation."""
        
        # Quiz generation prompt
        self.quiz_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at creating interview preparation quizzes.

Generate quiz questions that:
1. Test understanding of specific technical skills
2. Are appropriate for the given difficulty level
3. Include clear, unambiguous questions
4. Have correct answers with explanations

For MCQ quizzes:
- Provide 4 options (A, B, C, D)
- Only one correct answer
- Include explanations for why each option is correct/incorrect

For short-answer quizzes:
- Provide a clear question
- Include expected answer points/key concepts
- Provide a rubric for evaluation

Return JSON with the question structure."""),
            ("human", """Generate a {difficulty} level {quiz_type} quiz question about: {skills}

Context: {context}

Return JSON:
{{
  "question": "Question text",
  "question_type": "{quiz_type}",
  "options": ["Option A", "Option B", "Option C", "Option D"],  // Only for MCQ
  "correct_answer": "A" or "Answer text",  // Index for MCQ, text for short-answer
  "explanation": "Why this is correct",
  "key_points": ["Key concept 1", "Key concept 2"],  // For short-answer
  "rubric": {{"points": ["Point 1", "Point 2"]}}  // For short-answer evaluation
}}"""),
        ])
        
        # Flashcard generation prompt
        self.flashcard_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at creating educational flashcards for interview preparation.

Create flashcards that:
1. Focus on key concepts, definitions, or facts
2. Are concise and memorable
3. Include clear front (question/prompt) and back (answer)
4. Are appropriate for spaced repetition learning

Return JSON with front and back content."""),
            ("human", """Create a {difficulty} level flashcard about: {skills}

Context: {context}

Return JSON:
{{
  "front": "Question or prompt (concise)",
  "back": "Answer or explanation (clear and complete)",
  "tags": ["concept1", "concept2"]
}}"""),
        ])
        
        # Behavioral prompt generation
        self.behavioral_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at creating behavioral interview questions.

Generate STAR-method behavioral questions that:
1. Are relevant to the target role and skills
2. Test specific competencies (leadership, problem-solving, teamwork, etc.)
3. Are appropriate for the role level
4. Include evaluation criteria

Return JSON with question and evaluation rubric."""),
            ("human", """Generate a behavioral interview question for a role requiring: {skills}

Role Level: {difficulty}
Context: {context}

Return JSON:
{{
  "question": "Tell me about a time when...",
  "competency": "leadership" | "problem-solving" | "teamwork" | "communication" | etc.,
  "star_guidance": {{
    "situation": "What context to describe",
    "task": "What challenge to focus on",
    "action": "What actions to detail",
    "result": "What outcomes to highlight"
  }},
  "evaluation_criteria": [
    "Criterion 1",
    "Criterion 2",
    "Criterion 3"
  ],
  "rubric": {{
    "excellent": "What excellent answer includes",
    "good": "What good answer includes",
    "needs_improvement": "What needs improvement"
  }}
}}"""),
        ])
        
        # System design prompt generation
        self.system_design_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at creating system design interview questions.

Generate system design prompts that:
1. Are appropriate for the difficulty level
2. Test architectural thinking and scalability
3. Include clear requirements and constraints
4. Have evaluation criteria for different aspects

Return JSON with prompt and evaluation framework."""),
            ("human", """Generate a {difficulty} level system design question for skills: {skills}

Context: {context}

Return JSON:
{{
  "question": "Design a system to...",
  "requirements": [
    "Requirement 1",
    "Requirement 2"
  ],
  "constraints": [
    "Constraint 1",
    "Constraint 2"
  ],
  "evaluation_framework": {{
    "functional_requirements": ["What to evaluate"],
    "non_functional_requirements": ["Scalability", "Reliability", "Performance"],
    "architecture": ["Components", "Data flow", "Technology choices"],
    "trade_offs": ["What trade-offs to discuss"]
  }},
  "rubric": {{
    "excellent": "What excellent design includes",
    "good": "What good design includes",
    "needs_improvement": "What needs improvement"
  }}
}}"""),
        ])
    
    def _determine_difficulty(
        self,
        skill_names: List[str],
        user_id: int,
        db: Session
    ) -> DifficultyLevelEnum:
        """Determine appropriate difficulty based on skill mastery."""
        if not skill_names:
            return DifficultyLevelEnum.INTERMEDIATE
        
        # Check average mastery for these skills
        mastery_scores = db.query(SkillMastery.mastery_score).filter(
            SkillMastery.user_id == user_id,
            SkillMastery.skill_name.in_(skill_names)
        ).all()
        
        if not mastery_scores:
            return DifficultyLevelEnum.BEGINNER
        
        avg_mastery = sum(m[0] for m in mastery_scores if m[0] is not None) / len(mastery_scores)
        
        if avg_mastery < 0.3:
            return DifficultyLevelEnum.BEGINNER
        elif avg_mastery < 0.6:
            return DifficultyLevelEnum.INTERMEDIATE
        elif avg_mastery < 0.8:
            return DifficultyLevelEnum.ADVANCED
        else:
            return DifficultyLevelEnum.EXPERT
    
    def generate_quiz(
        self,
        skill_names: List[str],
        quiz_type: str = "mcq",  # "mcq" or "short_answer"
        difficulty: Optional[DifficultyLevelEnum] = None,
        context: str = "",
        user_id: Optional[int] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """Generate a quiz question."""
        try:
            # Determine difficulty if not provided
            if difficulty is None and user_id and db:
                difficulty = self._determine_difficulty(skill_names, user_id, db)
            elif difficulty is None:
                difficulty = DifficultyLevelEnum.INTERMEDIATE
            
            skills_str = ", ".join(skill_names) if skill_names else "general technical skills"
            
            response = self.llm.invoke(
                self.quiz_prompt.format_messages(
                    difficulty=difficulty.value,
                    quiz_type=quiz_type,
                    skills=skills_str,
                    context=context or f"Interview preparation for {skills_str}"
                )
            )
            
            content_text = response.content
            if "```json" in content_text:
                content_text = content_text.split("```json")[1].split("```")[0].strip()
            elif "```" in content_text:
                content_text = content_text.split("```")[1].split("```")[0].strip()
            
            quiz_data = json.loads(content_text)
            
            return {
                "practice_type": PracticeTypeEnum.QUIZ,
                "title": f"{difficulty.value.title()} {quiz_type.replace('_', ' ').title()} Quiz",
                "question": quiz_data.get("question", ""),
                "skill_names": skill_names,
                "difficulty": difficulty,
                "content": {
                    "question_type": quiz_type,
                    "options": quiz_data.get("options", []),
                    "explanation": quiz_data.get("explanation", ""),
                    "key_points": quiz_data.get("key_points", []),
                },
                "expected_answer": quiz_data.get("correct_answer", ""),
                "rubric": quiz_data.get("rubric", {})
            }
        except Exception as e:
            logger.error(f"Error generating quiz: {e}")
            raise
    
    def generate_flashcard(
        self,
        skill_names: List[str],
        difficulty: Optional[DifficultyLevelEnum] = None,
        context: str = "",
        user_id: Optional[int] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """Generate a flashcard."""
        try:
            if difficulty is None and user_id and db:
                difficulty = self._determine_difficulty(skill_names, user_id, db)
            elif difficulty is None:
                difficulty = DifficultyLevelEnum.INTERMEDIATE
            
            skills_str = ", ".join(skill_names) if skill_names else "general concepts"
            
            response = self.llm.invoke(
                self.flashcard_prompt.format_messages(
                    difficulty=difficulty.value,
                    skills=skills_str,
                    context=context or f"Learning {skills_str}"
                )
            )
            
            content_text = response.content
            if "```json" in content_text:
                content_text = content_text.split("```json")[1].split("```")[0].strip()
            elif "```" in content_text:
                content_text = content_text.split("```")[1].split("```")[0].strip()
            
            flashcard_data = json.loads(content_text)
            
            return {
                "practice_type": PracticeTypeEnum.FLASHCARD,
                "title": f"{difficulty.value.title()} Flashcard: {skill_names[0] if skill_names else 'General'}",
                "question": flashcard_data.get("front", ""),
                "skill_names": skill_names,
                "difficulty": difficulty,
                "content": {
                    "back": flashcard_data.get("back", ""),
                    "tags": flashcard_data.get("tags", [])
                },
                "expected_answer": flashcard_data.get("back", ""),
                "rubric": None
            }
        except Exception as e:
            logger.error(f"Error generating flashcard: {e}")
            raise
    
    def generate_behavioral_prompt(
        self,
        skill_names: List[str],
        difficulty: Optional[DifficultyLevelEnum] = None,
        context: str = "",
        user_id: Optional[int] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """Generate a behavioral interview prompt."""
        try:
            if difficulty is None and user_id and db:
                difficulty = self._determine_difficulty(skill_names, user_id, db)
            elif difficulty is None:
                difficulty = DifficultyLevelEnum.INTERMEDIATE
            
            skills_str = ", ".join(skill_names) if skill_names else "general professional skills"
            
            response = self.llm.invoke(
                self.behavioral_prompt.format_messages(
                    skills=skills_str,
                    difficulty=difficulty.value,
                    context=context or f"Behavioral interview for role requiring {skills_str}"
                )
            )
            
            content_text = response.content
            if "```json" in content_text:
                content_text = content_text.split("```json")[1].split("```")[0].strip()
            elif "```" in content_text:
                content_text = content_text.split("```")[1].split("```")[0].strip()
            
            behavioral_data = json.loads(content_text)
            
            return {
                "practice_type": PracticeTypeEnum.BEHAVIORAL,
                "title": f"Behavioral Question: {behavioral_data.get('competency', 'General')}",
                "question": behavioral_data.get("question", ""),
                "skill_names": skill_names,
                "difficulty": difficulty,
                "content": {
                    "competency": behavioral_data.get("competency", ""),
                    "star_guidance": behavioral_data.get("star_guidance", {}),
                    "evaluation_criteria": behavioral_data.get("evaluation_criteria", [])
                },
                "expected_answer": None,  # Behavioral questions don't have single correct answer
                "rubric": behavioral_data.get("rubric", {})
            }
        except Exception as e:
            logger.error(f"Error generating behavioral prompt: {e}")
            raise
    
    def generate_system_design_prompt(
        self,
        skill_names: List[str],
        difficulty: Optional[DifficultyLevelEnum] = None,
        context: str = "",
        user_id: Optional[int] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """Generate a system design prompt."""
        try:
            if difficulty is None and user_id and db:
                difficulty = self._determine_difficulty(skill_names, user_id, db)
            elif difficulty is None:
                difficulty = DifficultyLevelEnum.INTERMEDIATE
            
            skills_str = ", ".join(skill_names) if skill_names else "system design"
            
            response = self.llm.invoke(
                self.system_design_prompt.format_messages(
                    difficulty=difficulty.value,
                    skills=skills_str,
                    context=context or f"System design interview for {skills_str}"
                )
            )
            
            content_text = response.content
            if "```json" in content_text:
                content_text = content_text.split("```json")[1].split("```")[0].strip()
            elif "```" in content_text:
                content_text = content_text.split("```")[1].split("```")[0].strip()
            
            design_data = json.loads(content_text)
            
            return {
                "practice_type": PracticeTypeEnum.SYSTEM_DESIGN,
                "title": f"{difficulty.value.title()} System Design Challenge",
                "question": design_data.get("question", ""),
                "skill_names": skill_names,
                "difficulty": difficulty,
                "content": {
                    "requirements": design_data.get("requirements", []),
                    "constraints": design_data.get("constraints", []),
                    "evaluation_framework": design_data.get("evaluation_framework", {})
                },
                "expected_answer": None,  # System design has no single answer
                "rubric": design_data.get("rubric", {})
            }
        except Exception as e:
            logger.error(f"Error generating system design prompt: {e}")
            raise
    
    def generate_for_task(
        self,
        task: DailyTask,
        practice_type: PracticeTypeEnum,
        user_id: int,
        db: Session,
        count: int = 1
    ) -> List[PracticeItem]:
        """Generate practice items for a specific task."""
        practice_items = []
        
        skill_names = task.skill_names or []
        context = f"Task: {task.title}. {task.description}"
        
        for _ in range(count):
            try:
                if practice_type == PracticeTypeEnum.QUIZ:
                    # Generate both MCQ and short-answer quizzes
                    quiz_types = ["mcq", "short_answer"]
                    for qt in quiz_types:
                        data = self.generate_quiz(
                            skill_names=skill_names,
                            quiz_type=qt,
                            context=context,
                            user_id=user_id,
                            db=db
                        )
                        practice_item = PracticeItem(
                            task_id=task.id,
                            practice_type=data["practice_type"],
                            title=data["title"],
                            question=data["question"],
                            skill_names=data["skill_names"],
                            difficulty=data["difficulty"],
                            content=data["content"],
                            expected_answer=data["expected_answer"],
                            rubric=data["rubric"]
                        )
                        db.add(practice_item)
                        practice_items.append(practice_item)
                
                elif practice_type == PracticeTypeEnum.FLASHCARD:
                    data = self.generate_flashcard(
                        skill_names=skill_names,
                        context=context,
                        user_id=user_id,
                        db=db
                    )
                    practice_item = PracticeItem(
                        task_id=task.id,
                        practice_type=data["practice_type"],
                        title=data["title"],
                        question=data["question"],
                        skill_names=data["skill_names"],
                        difficulty=data["difficulty"],
                        content=data["content"],
                        expected_answer=data["expected_answer"],
                        rubric=data["rubric"]
                    )
                    db.add(practice_item)
                    practice_items.append(practice_item)
                
                elif practice_type == PracticeTypeEnum.BEHAVIORAL:
                    data = self.generate_behavioral_prompt(
                        skill_names=skill_names,
                        context=context,
                        user_id=user_id,
                        db=db
                    )
                    practice_item = PracticeItem(
                        task_id=task.id,
                        practice_type=data["practice_type"],
                        title=data["title"],
                        question=data["question"],
                        skill_names=data["skill_names"],
                        difficulty=data["difficulty"],
                        content=data["content"],
                        expected_answer=data["expected_answer"],
                        rubric=data["rubric"]
                    )
                    db.add(practice_item)
                    practice_items.append(practice_item)
                
                elif practice_type == PracticeTypeEnum.SYSTEM_DESIGN:
                    data = self.generate_system_design_prompt(
                        skill_names=skill_names,
                        context=context,
                        user_id=user_id,
                        db=db
                    )
                    practice_item = PracticeItem(
                        task_id=task.id,
                        practice_type=data["practice_type"],
                        title=data["title"],
                        question=data["question"],
                        skill_names=data["skill_names"],
                        difficulty=data["difficulty"],
                        content=data["content"],
                        expected_answer=data["expected_answer"],
                        rubric=data["rubric"]
                    )
                    db.add(practice_item)
                    practice_items.append(practice_item)
            
            except Exception as e:
                logger.error(f"Error generating practice item: {e}")
                continue
        
        db.flush()
        return practice_items


