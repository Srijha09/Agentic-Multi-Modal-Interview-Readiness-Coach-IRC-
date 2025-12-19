"""
Planner service that generates personalized multi-week study plans from skill gaps.

This service:
1. Takes skill gaps and user constraints (interview date, hours per week)
2. Uses LLM to generate a structured study plan
3. Creates weekly themes and daily task breakdowns
4. Ensures tasks map directly to skill gaps
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, date
import json
import logging

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from app.core.llm import get_llm_with_temperature
from app.db.models import (
    StudyPlan,
    Week,
    Day,
    DailyTask,
    Gap,
    User,
    Skill,
    TaskTypeEnum,
    TaskStatusEnum,
)
from app.schemas.skill import GapPriority

logger = logging.getLogger(__name__)


class StudyPlanner:
    """Service for generating personalized study plans from skill gaps."""
    
    def __init__(self):
        self.llm = get_llm_with_temperature(temperature=0.7)  # Some creativity for planning
        self._setup_prompts()
    
    def _setup_prompts(self):
        """Setup prompt templates for plan generation."""
        
        self.plan_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at creating personalized study plans for interview preparation.

Your task is to create a structured, multi-week study plan that:
1. Addresses skill gaps identified between a candidate's resume and job requirements
2. Respects time constraints (interview date, hours per week)
3. Organizes learning into weekly themes
4. Breaks down each week into daily tasks with time estimates
5. Ensures tasks map directly to skill gaps

For each week, provide:
- A theme (e.g., "Deep Learning Fundamentals", "System Design Patterns")
- Focus skills (which gaps this week addresses)
- Daily breakdown with tasks

For each task, you MUST provide:
- Type: "learn" (reading, watching videos), "practice" (coding, exercises), or "review" (recap)
- Title: Clear, actionable task name
- Description: What to do
- Skill names: Which skills this addresses
- Estimated minutes: Realistic time estimate
- Dependencies: Any prerequisite tasks (by task index)
- Content: A REQUIRED JSON object with study materials. This is CRITICAL - always include:
  - "study_materials": List of 2-4 specific items to study (e.g., ["Read Chapter 3 on Neural Networks", "Watch video on backpropagation", "Complete exercises on gradient descent"])
  - "resources": List of 2-5 real URLs or resource links (e.g., ["https://docs.python.org/3/", "https://realpython.com/python-basics/", "https://www.coursera.org/learn/machine-learning"])
  - "key_concepts": List of 3-5 key concepts to focus on (e.g., ["Neural Networks", "Backpropagation", "Gradient Descent"])
  - "practice_exercises": List of practice exercises (only for "practice" type tasks, otherwise empty array)

CRITICAL: For the "resources" field, provide REAL, VERIFIED URLs that are DIRECTLY related to the skill. 
- Each URL MUST be specifically about the skill mentioned in the task
- Do NOT include generic programming tutorials, unrelated videos, or off-topic links
- Verify relevance: if the task is about "CUDA", every URL must be about CUDA/GPU computing
- Examples of CORRECT resources:
  * For "CUDA": ["https://docs.nvidia.com/cuda/", "https://developer.nvidia.com/cuda-toolkit", "https://developer.nvidia.com/cuda-zone"]
  * For "Python": ["https://docs.python.org/3/", "https://realpython.com/", "https://www.python.org/about/gettingstarted/"]
  * For "Machine Learning": ["https://scikit-learn.org/stable/", "https://www.coursera.org/learn/machine-learning", "https://www.kaggle.com/learn/machine-learning"]
- Examples of INCORRECT (do NOT do this):
  * For "CUDA" task: including Python tutorials, general programming videos, or unrelated Medium articles
  * For "Python" task: including JavaScript tutorials or C++ documentation
- Quality over quantity: Include 3-5 highly relevant resources, not 10+ generic ones

ALWAYS include the "content" field for EVERY task. Do not skip it.

Return a JSON structure with weeks, days, and tasks."""),
            ("human", """Create a {weeks}-week study plan for interview preparation.

**Constraints:**
- Interview date: {interview_date}
- Hours per week: {hours_per_week}
- Total available hours: {total_hours}

**Skill Gaps to Address (Prioritized):**
{gaps_summary}

**Critical Gaps (Must Address):**
{critical_gaps}

**High Priority Gaps:**
{high_gaps}

**Medium Priority Gaps:**
{medium_gaps}

Create a plan that:
1. Creates EXACTLY {weeks} weeks (you MUST generate all {weeks} weeks, not fewer)
2. Prioritizes critical and high-priority gaps in early weeks
3. Distributes learning evenly across weeks
4. Includes a mix of learn → practice → review cycles
5. Respects the hours_per_week constraint
6. Ensures all critical gaps are covered

CRITICAL: You must return a JSON structure with EXACTLY {weeks} weeks in the "weeks" array. Do not generate fewer weeks than requested.

Return JSON with this structure:
{{
  "weeks": [
    {{
      "week_number": 1,
      "theme": "Week 1 Theme",
      "focus_skills": ["Skill1", "Skill2"],
      "estimated_hours": 10.0,
      "days": [
        {{
          "day_number": 1,
          "date": "2024-01-15",
          "theme": "Day 1 Theme",
          "estimated_hours": 2.0,
          "tasks": [
            {{
              "task_type": "learn",
              "title": "Task Title",
              "description": "Task description",
              "skill_names": ["Skill1"],
              "estimated_minutes": 60,
              "dependencies": [],
              "content": {{
                "study_materials": ["Read Chapter 3 on Neural Networks", "Watch video on backpropagation"],
                "resources": ["https://example.com/tutorial", "https://docs.example.com"],
                "key_concepts": ["Neural Networks", "Backpropagation"],
                "practice_exercises": []
              }}
            }}
          ]
        }}
      ]
    }}
  ]
}}""")
        ])
    
    def generate_plan(
        self,
        user_id: int,
        gaps: List[Gap],
        interview_date: Optional[datetime],
        weeks: int,
        hours_per_week: float,
        db_session
    ) -> StudyPlan:
        """
        Generate a personalized study plan from skill gaps.
        
        Args:
            user_id: User ID
            gaps: List of Gap model instances
            interview_date: Target interview date (optional)
            weeks: Number of weeks for the plan
            hours_per_week: Hours available per week
            db_session: Database session
        
        Returns:
            StudyPlan model instance (not yet committed)
        """
        logger.info(f"Generating {weeks}-week study plan for user {user_id}")
        
        # Prepare gaps summary for LLM
        gaps_summary = self._prepare_gaps_summary(gaps)
        critical_gaps = [g for g in gaps if g.priority == GapPriority.CRITICAL]
        high_gaps = [g for g in gaps if g.priority == GapPriority.HIGH]
        medium_gaps = [g for g in gaps if g.priority == GapPriority.MEDIUM]
        
        # Calculate total hours
        total_hours = weeks * hours_per_week
        
        # Format interview date
        interview_date_str = interview_date.strftime("%Y-%m-%d") if interview_date else "Not specified"
        
        # Generate plan using LLM
        try:
            formatted_prompt = self.plan_prompt.format_messages(
                weeks=weeks,
                interview_date=interview_date_str,
                hours_per_week=hours_per_week,
                total_hours=total_hours,
                gaps_summary=gaps_summary,
                critical_gaps=self._format_gaps_list(critical_gaps),
                high_gaps=self._format_gaps_list(high_gaps),
                medium_gaps=self._format_gaps_list(medium_gaps),
            )
            
            logger.info("Calling LLM to generate study plan...")
            response = self.llm.invoke(formatted_prompt)
            
            # Parse JSON response
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            plan_data = json.loads(content)
            
            generated_weeks = len(plan_data.get('weeks', []))
            logger.info(f"Generated plan with {generated_weeks} weeks (requested: {weeks})")
            
            # Validate that we got the requested number of weeks
            if generated_weeks < weeks:
                logger.warning(f"LLM only generated {generated_weeks} weeks instead of {weeks}. Using fallback to ensure all weeks are created.")
                plan_data = self._create_fallback_plan(gaps, weeks, hours_per_week, interview_date)
            elif generated_weeks > weeks:
                logger.warning(f"LLM generated {generated_weeks} weeks instead of {weeks}. Truncating to {weeks} weeks.")
                plan_data["weeks"] = plan_data["weeks"][:weeks]
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.error(f"Response content: {response.content if 'response' in locals() else 'N/A'}")
            # Fallback to a simple plan structure
            plan_data = self._create_fallback_plan(gaps, weeks, hours_per_week, interview_date)
        except Exception as e:
            logger.error(f"Error generating plan: {e}", exc_info=True)
            plan_data = self._create_fallback_plan(gaps, weeks, hours_per_week, interview_date)
        
        # Create StudyPlan in database
        focus_areas = [g.required_skill_name for g in critical_gaps[:5]]  # Top 5 critical skills
        
        study_plan = StudyPlan(
            user_id=user_id,
            interview_date=interview_date,
            weeks=weeks,
            hours_per_week=hours_per_week,
            focus_areas=focus_areas,
            plan_data=plan_data,
        )
        db_session.add(study_plan)
        db_session.flush()  # Get ID
        
        # Create Week, Day, and Task records
        self._create_plan_structure(study_plan, plan_data, interview_date, db_session)
        
        logger.info(f"Created study plan {study_plan.id} with {len(study_plan.weeks_data)} weeks")
        
        return study_plan
    
    def _prepare_gaps_summary(self, gaps: List[Gap]) -> str:
        """Prepare a summary of gaps for the LLM prompt."""
        if not gaps:
            return "No skill gaps identified."
        
        summary_parts = []
        for gap in gaps:
            summary_parts.append(
                f"- {gap.required_skill_name} ({gap.coverage_status.value}, {gap.priority.value} priority): "
                f"{gap.gap_reason}. Estimated learning: {gap.estimated_learning_hours or 0:.1f} hours"
            )
        
        return "\n".join(summary_parts)
    
    def _format_gaps_list(self, gaps: List[Gap]) -> str:
        """Format a list of gaps for the prompt."""
        if not gaps:
            return "None"
        
        return ", ".join([f"{g.required_skill_name} ({g.estimated_learning_hours or 0:.1f}h)" for g in gaps])
    
    def _generate_task_content(
        self,
        title: str,
        description: str,
        skill_names: List[str],
        task_type: str
    ) -> Dict[str, Any]:
        """
        Generate study materials and resources for a task using LLM.
        This is a fallback/enhancement function to ensure all tasks have content.
        """
        try:
            # Use LLM to generate specific study materials for this task
            content_prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert at creating study materials for interview preparation.

Given a task title, description, and skills, generate specific study materials including:
- What to study (specific chapters, videos, articles)
- Key concepts to focus on
- Helpful resources and links (REAL, VERIFIED URLs that are DIRECTLY related to the skill/topic)
- Practice exercises (if it's a practice task)

CRITICAL REQUIREMENTS:
1. ALL resource URLs MUST be directly related to the skill(s) mentioned in the task
2. Do NOT include generic or unrelated links
3. Verify that URLs are actually about the specific skill (e.g., for CUDA, only include CUDA-specific resources)
4. Prefer official documentation, well-known tutorials, and verified educational content
5. If you're unsure about a URL's relevance, omit it rather than including an unrelated link

Be specific and actionable. For technical skills, include relevant documentation, tutorials, and practice resources."""),
                ("human", """Generate study materials for this task:

Title: {title}
Description: {description}
Skills: {skills}
Task Type: {task_type}

Return a JSON object with:
{{
  "study_materials": ["Specific item 1", "Specific item 2", ...],
  "resources": ["https://real-verified-url-directly-related-to-skill.com", ...],
  "key_concepts": ["Concept 1", "Concept 2", ...],
  "practice_exercises": ["Exercise 1", "Exercise 2", ...] (only if task_type is "practice")
}}

IMPORTANT: 
- For "{skills}", ONLY include resources that are SPECIFICALLY about {skills}
- Do NOT include generic programming tutorials, unrelated YouTube videos, or off-topic links
- Each URL must be directly relevant to learning {skills}
- Examples:
  * For CUDA: NVIDIA CUDA docs, CUDA programming tutorials, GPU computing resources
  * For Python: Python.org docs, Python tutorials, Python-specific courses
  * For Machine Learning: ML courses, ML libraries docs, ML-specific resources

Be extremely selective - quality over quantity. Only include 3-5 highly relevant resources."""),
            ])
            
            skills_str = ", ".join(skill_names) if skill_names else "General skills"
            response = self.llm.invoke(
                content_prompt.format_messages(
                    title=title,
                    description=description,
                    skills=skills_str,
                    task_type=task_type
                )
            )
            
            content_text = response.content
            if "```json" in content_text:
                content_text = content_text.split("```json")[1].split("```")[0].strip()
            elif "```" in content_text:
                content_text = content_text.split("```")[1].split("```")[0].strip()
            
            generated_content = json.loads(content_text)
            
            # Validate and filter resources to ensure they're relevant
            resources = generated_content.get("resources", [])
            filtered_resources = self._filter_relevant_resources(resources, skill_names)
            
            # Ensure all required fields exist
            return {
                "study_materials": generated_content.get("study_materials", []),
                "resources": filtered_resources if filtered_resources else self._get_default_resources(skill_names),
                "key_concepts": generated_content.get("key_concepts", skill_names if skill_names else []),
                "practice_exercises": generated_content.get("practice_exercises", []) if task_type == "practice" else []
            }
        except Exception as e:
            logger.warning(f"Failed to generate content for task '{title}': {e}. Using fallback.")
            # Fallback: generate basic content from task info
            return {
                "study_materials": [
                    f"Study {title.lower()}",
                    description if description else f"Learn about {', '.join(skill_names) if skill_names else 'the topic'}"
                ],
                "resources": self._get_default_resources(skill_names),
                "key_concepts": skill_names if skill_names else [title],
                "practice_exercises": [] if task_type != "practice" else [f"Practice {title.lower()}"]
            }
    
    def _filter_relevant_resources(self, resources: List[str], skill_names: List[str]) -> List[str]:
        """
        Filter resources to ensure they're relevant to the skills.
        This is a basic validation - URLs should contain skill-related keywords.
        """
        if not resources or not skill_names:
            return resources
        
        filtered = []
        skill_keywords = []
        
        # Extract keywords from skill names
        for skill in skill_names:
            skill_lower = skill.lower()
            # Add the skill name and common variations
            skill_keywords.append(skill_lower)
            # Handle multi-word skills
            skill_keywords.extend(skill_lower.split())
            # Handle common abbreviations
            if "cuda" in skill_lower:
                skill_keywords.extend(["cuda", "nvidia", "gpu", "parallel"])
            elif "python" in skill_lower:
                skill_keywords.extend(["python", "py"])
            elif "machine learning" in skill_lower or "ml" in skill_lower:
                skill_keywords.extend(["machine-learning", "ml", "ai"])
            elif "deep learning" in skill_lower:
                skill_keywords.extend(["deep-learning", "neural", "pytorch", "tensorflow"])
        
        # Filter resources - keep if URL contains any skill keyword
        for resource in resources:
            if isinstance(resource, str) and resource.startswith("http"):
                resource_lower = resource.lower()
                # Check if URL contains any skill-related keyword
                if any(keyword in resource_lower for keyword in skill_keywords):
                    filtered.append(resource)
                # Also keep if it's from known educational/tech domains
                elif any(domain in resource_lower for domain in [
                    "docs.nvidia.com", "developer.nvidia.com", "nvidia.com",
                    "python.org", "docs.python.org",
                    "pytorch.org", "tensorflow.org",
                    "scikit-learn.org", "kaggle.com",
                    "coursera.org", "udacity.com", "edx.org"
                ]):
                    # Double-check it's not obviously wrong
                    # If skill is CUDA but URL is about Python, skip it
                    skill_lower_str = " ".join([s.lower() for s in skill_names])
                    if "cuda" in skill_lower_str and "python" in resource_lower and "cuda" not in resource_lower:
                        continue  # Skip Python-only resources for CUDA tasks
                    filtered.append(resource)
        
        return filtered if filtered else resources  # Return original if filtering removes everything
    
    def _get_default_resources(self, skill_names: List[str]) -> List[str]:
        """Get default resources based on skill names. Only includes verified, relevant resources."""
        resources = []
        for skill in skill_names:
            skill_lower = skill.lower()
            # Add common resource patterns - only verified, relevant resources
            if "cuda" in skill_lower:
                resources.extend([
                    "https://docs.nvidia.com/cuda/",
                    "https://developer.nvidia.com/cuda-toolkit",
                    "https://developer.nvidia.com/cuda-zone",
                    "https://www.nvidia.com/en-us/developer/learn/cuda-tutorial/"
                ])
            elif "python" in skill_lower:
                resources.extend([
                    "https://docs.python.org/3/",
                    "https://www.python.org/about/gettingstarted/",
                    "https://realpython.com/"
                ])
            elif "machine learning" in skill_lower or "ml" in skill_lower:
                resources.extend([
                    "https://scikit-learn.org/stable/",
                    "https://www.coursera.org/learn/machine-learning",
                    "https://www.kaggle.com/learn/machine-learning"
                ])
            elif "deep learning" in skill_lower:
                resources.extend([
                    "https://pytorch.org/tutorials/",
                    "https://www.tensorflow.org/tutorials",
                    "https://www.deeplearning.ai/"
                ])
            elif "tensorflow" in skill_lower:
                resources.extend([
                    "https://www.tensorflow.org/tutorials",
                    "https://www.tensorflow.org/api_docs",
                    "https://www.tensorflow.org/learn"
                ])
            elif "pytorch" in skill_lower:
                resources.extend([
                    "https://pytorch.org/tutorials/",
                    "https://pytorch.org/docs/stable/index.html",
                    "https://pytorch.org/tutorials/beginner/basics/intro.html"
                ])
            elif "system design" in skill_lower:
                resources.extend([
                    "https://github.com/donnemartin/system-design-primer",
                    "https://www.educative.io/courses/grokking-the-system-design-interview"
                ])
            elif "java" in skill_lower:
                resources.extend([
                    "https://docs.oracle.com/javase/tutorial/",
                    "https://www.oracle.com/java/technologies/"
                ])
            elif "c++" in skill_lower or "cpp" in skill_lower:
                resources.extend([
                    "https://www.cplusplus.com/doc/tutorial/",
                    "https://en.cppreference.com/w/cpp"
                ])
            elif "docker" in skill_lower:
                resources.extend([
                    "https://docs.docker.com/get-started/",
                    "https://docs.docker.com/"
                ])
            elif "kubernetes" in skill_lower or "k8s" in skill_lower:
                resources.extend([
                    "https://kubernetes.io/docs/home/",
                    "https://kubernetes.io/docs/tutorials/"
                ])
            elif "aws" in skill_lower:
                resources.extend([
                    "https://aws.amazon.com/getting-started/",
                    "https://docs.aws.amazon.com/"
                ])
        
        return list(set(resources))  # Remove duplicates
    
    def _create_fallback_plan(
        self,
        gaps: List[Gap],
        weeks: int,
        hours_per_week: float,
        interview_date: Optional[datetime]
    ) -> Dict[str, Any]:
        """Create a simple fallback plan if LLM generation fails."""
        logger.warning("Using fallback plan generation")
        
        # Sort gaps by priority
        sorted_gaps = sorted(gaps, key=lambda g: (
            0 if g.priority == GapPriority.CRITICAL else
            1 if g.priority == GapPriority.HIGH else
            2 if g.priority == GapPriority.MEDIUM else 3
        ))
        
        # Distribute gaps across weeks
        weeks_data = []
        start_date = datetime.now().date()
        
        for week_num in range(1, weeks + 1):
            # Get gaps for this week (distribute evenly)
            week_gaps = sorted_gaps[(week_num - 1)::weeks] if weeks > 0 else []
            
            theme = f"Week {week_num}: {', '.join([g.required_skill_name for g in week_gaps[:3]])}" if week_gaps else f"Week {week_num}"
            
            # Create days (5 study days per week)
            days = []
            for day_num in range(1, 6):  # Monday to Friday
                day_date = start_date + timedelta(days=(week_num - 1) * 7 + day_num - 1)
                
                # Simple task per day
                task_hours = hours_per_week / 5
                tasks = []
                if week_gaps:
                    gap = week_gaps[0] if week_gaps else None
                    if gap:
                        # Generate content for heuristic plan tasks
                        task_content = self._generate_task_content(
                            f"Learn {gap.required_skill_name}",
                            gap.gap_reason,
                            [gap.required_skill_name],
                            "learn"
                        )
                        
                        tasks.append({
                            "task_type": "learn",
                            "title": f"Learn {gap.required_skill_name}",
                            "description": gap.gap_reason,
                            "skill_names": [gap.required_skill_name],
                            "estimated_minutes": int(task_hours * 60),
                            "dependencies": [],
                            "content": task_content
                        })
                
                days.append({
                    "day_number": day_num,
                    "date": day_date.isoformat(),
                    "theme": f"Study {week_gaps[0].required_skill_name if week_gaps else 'General'}",
                    "estimated_hours": task_hours,
                    "tasks": tasks
                })
            
            weeks_data.append({
                "week_number": week_num,
                "theme": theme,
                "focus_skills": [g.required_skill_name for g in week_gaps],
                "estimated_hours": hours_per_week,
                "days": days
            })
        
        return {"weeks": weeks_data}
    
    def _create_plan_structure(
        self,
        study_plan: StudyPlan,
        plan_data: Dict[str, Any],
        interview_date: Optional[datetime],
        db_session
    ):
        """Create Week, Day, and Task records from plan data."""
        weeks_data = plan_data.get("weeks", [])
        
        for week_data in weeks_data:
            week = Week(
                study_plan_id=study_plan.id,
                week_number=week_data["week_number"],
                theme=week_data["theme"],
                focus_skills=week_data.get("focus_skills", []),
                estimated_hours=week_data.get("estimated_hours", 0.0),
            )
            db_session.add(week)
            db_session.flush()
            
            days_data = week_data.get("days", [])
            for day_data in days_data:
                # Parse date
                day_date_str = day_data.get("date")
                if isinstance(day_date_str, str):
                    try:
                        # Try parsing ISO format
                        if "T" in day_date_str:
                            day_date = datetime.fromisoformat(day_date_str.replace("Z", "+00:00"))
                        else:
                            # Just date string (YYYY-MM-DD)
                            parsed_date = datetime.strptime(day_date_str, "%Y-%m-%d")
                            day_date = datetime.combine(parsed_date.date(), datetime.min.time())
                    except (ValueError, AttributeError) as e:
                        logger.warning(f"Failed to parse date '{day_date_str}': {e}, using fallback")
                        # Fallback: calculate from week number
                        start_date = interview_date.date() if interview_date else datetime.now().date()
                        day_date = datetime.combine(
                            start_date + timedelta(days=(week_data["week_number"] - 1) * 7 + day_data["day_number"] - 1),
                            datetime.min.time()
                        )
                else:
                    # Fallback: calculate from week number
                    start_date = interview_date.date() if interview_date else datetime.now().date()
                    day_date = datetime.combine(
                        start_date + timedelta(days=(week_data["week_number"] - 1) * 7 + day_data["day_number"] - 1),
                        datetime.min.time()
                    )
                
                day = Day(
                    week_id=week.id,
                    day_number=day_data["day_number"],
                    date=day_date,
                    theme=day_data.get("theme"),
                    estimated_hours=day_data.get("estimated_hours", 0.0),
                )
                db_session.add(day)
                db_session.flush()
                
                tasks_data = day_data.get("tasks", [])
                for task_data in tasks_data:
                    # Map task_type string to enum
                    task_type_str = task_data.get("task_type", "learn").lower()
                    task_type_enum = TaskTypeEnum.LEARN
                    if task_type_str == "practice":
                        task_type_enum = TaskTypeEnum.PRACTICE
                    elif task_type_str == "review":
                        task_type_enum = TaskTypeEnum.REVIEW
                    
                    # Get content from Planner Agent's LLM response
                    # The Planner Agent should always generate content, but we have a fallback if it doesn't
                    task_content = task_data.get("content", {}) or {}
                    
                    # Filter resources to ensure they're relevant to the task skills
                    if task_content and task_content.get("resources"):
                        skill_names = task_data.get("skill_names", []) or []
                        filtered_resources = self._filter_relevant_resources(
                            task_content.get("resources", []),
                            skill_names
                        )
                        task_content["resources"] = filtered_resources
                        # If filtering removed all resources, use defaults
                        if not filtered_resources and skill_names:
                            task_content["resources"] = self._get_default_resources(skill_names)
                    
                    if not task_content or not task_content.get("study_materials"):
                        # Fallback: Generate content if Planner Agent didn't provide it
                        # This should rarely happen with the updated prompt
                        logger.warning(f"Planner Agent didn't generate content for task '{task_data.get('title')}', using fallback")
                        task_content = self._generate_task_content(
                            task_data.get("title", ""),
                            task_data.get("description", ""),
                            task_data.get("skill_names", []),
                            task_type_str
                        )
                    
                    task = DailyTask(
                        study_plan_id=study_plan.id,
                        day_id=day.id,
                        task_date=day_date,
                        task_type=task_type_enum,
                        title=task_data["title"],
                        description=task_data.get("description", ""),
                        skill_names=task_data.get("skill_names", []) or [],
                        estimated_minutes=task_data.get("estimated_minutes", 60),
                        status=TaskStatusEnum.PENDING,
                        dependencies=task_data.get("dependencies", []) or [],
                        content=task_content,
                    )
                    db_session.add(task)

