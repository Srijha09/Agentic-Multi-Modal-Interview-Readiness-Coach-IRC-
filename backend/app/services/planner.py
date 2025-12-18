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

For each task, provide:
- Type: "learn" (reading, watching videos), "practice" (coding, exercises), or "review" (recap)
- Title: Clear, actionable task name
- Description: What to do
- Skill names: Which skills this addresses
- Estimated minutes: Realistic time estimate
- Dependencies: Any prerequisite tasks (by task index)

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
1. Prioritizes critical and high-priority gaps in early weeks
2. Distributes learning evenly across weeks
3. Includes a mix of learn → practice → review cycles
4. Respects the hours_per_week constraint
5. Ensures all critical gaps are covered

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
              "dependencies": []
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
            
            logger.info(f"Generated plan with {len(plan_data.get('weeks', []))} weeks")
            
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
                        tasks.append({
                            "task_type": "learn",
                            "title": f"Learn {gap.required_skill_name}",
                            "description": gap.gap_reason,
                            "skill_names": [gap.required_skill_name],
                            "estimated_minutes": int(task_hours * 60),
                            "dependencies": []
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
                        content=task_data.get("content", {}) or {},
                    )
                    db_session.add(task)

