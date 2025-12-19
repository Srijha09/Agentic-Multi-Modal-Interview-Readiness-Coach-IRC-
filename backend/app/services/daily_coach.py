"""
Daily Coach Agent Service (Phase 6).

Orchestrates daily execution and accountability:
- Daily task briefing
- Missed-task rescheduling
- Carry-over logic
"""
import logging
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.db.models import (
    StudyPlan,
    DailyTask,
    Day,
    Week,
    TaskStatusEnum,
    TaskTypeEnum,
)
from app.schemas.coach import (
    DailyBriefingResponse,
    DailyBriefingTask,
    TaskRescheduleResponse,
    CarryOverSummary,
)
from app.core.llm import get_llm_with_temperature
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)


class DailyCoach:
    """
    Daily Coach Agent for orchestrating daily execution and accountability.
    """
    
    def __init__(self):
        self.llm = get_llm_with_temperature(temperature=0.7)  # Creative for motivational messages
        self._setup_prompts()
    
    def _setup_prompts(self):
        """Setup prompts for motivational messages."""
        self.motivational_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a supportive and encouraging study coach. Generate brief, motivating messages (1-2 sentences) based on the user's progress.

Be positive, specific, and actionable. Focus on:
- Celebrating completed tasks
- Encouraging progress on pending tasks
- Acknowledging effort and consistency
- Providing gentle motivation for overdue tasks

Keep messages concise and inspiring."""),
            ("human", """Generate a motivational message for today's study session.

Completed tasks: {completed_count}
Pending tasks: {pending_count}
Overdue tasks: {overdue_count}
Completion percentage: {completion_pct}%

Today's focus skills: {focus_skills}

Generate a brief, encouraging message."""),
        ])
    
    def get_daily_briefing(
        self,
        user_id: int,
        target_date: Optional[date] = None,
        study_plan_id: Optional[int] = None,
        *,
        db_session: Session
    ) -> DailyBriefingResponse:
        """
        Get daily briefing for a specific date.
        
        Args:
            user_id: User ID
            target_date: Date to get briefing for (defaults to today)
            study_plan_id: Specific study plan ID (uses latest if not provided)
            db_session: Database session
            
        Returns:
            DailyBriefingResponse with tasks and progress
        """
        if target_date is None:
            target_date = date.today()
        
        # Get study plan
        if study_plan_id:
            study_plan = db_session.query(StudyPlan).filter(
                StudyPlan.id == study_plan_id,
                StudyPlan.user_id == user_id
            ).first()
        else:
            study_plan = db_session.query(StudyPlan).filter(
                StudyPlan.user_id == user_id
            ).order_by(StudyPlan.created_at.desc()).first()
        
        if not study_plan:
            raise ValueError(f"No study plan found for user {user_id}")
        
        # Get tasks for the target date
        target_datetime = datetime.combine(target_date, datetime.min.time())
        tasks = db_session.query(DailyTask).filter(
            DailyTask.study_plan_id == study_plan.id,
            DailyTask.task_date >= target_datetime,
            DailyTask.task_date < target_datetime + timedelta(days=1)
        ).all()
        
        # Also get overdue tasks (tasks from previous dates that are not completed)
        overdue_cutoff = datetime.combine(target_date, datetime.min.time())
        overdue_tasks = db_session.query(DailyTask).filter(
            DailyTask.study_plan_id == study_plan.id,
            DailyTask.task_date < overdue_cutoff,
            DailyTask.status != TaskStatusEnum.COMPLETED,
            DailyTask.status != TaskStatusEnum.SKIPPED
        ).all()
        
        # Combine tasks
        all_tasks = list(tasks) + list(overdue_tasks)
        
        # Build briefing tasks
        briefing_tasks: List[DailyBriefingTask] = []
        completed_count = 0
        pending_count = 0
        overdue_count = 0
        total_estimated_minutes = 0
        total_actual_minutes = 0
        
        for task in all_tasks:
            task_date = task.task_date.date()
            is_overdue = task_date < target_date and task.status != TaskStatusEnum.COMPLETED
            days_overdue = (target_date - task_date).days if is_overdue else 0
            
            if is_overdue:
                overdue_count += 1
            elif task.status == TaskStatusEnum.COMPLETED:
                completed_count += 1
            else:
                pending_count += 1
            
            total_estimated_minutes += task.estimated_minutes
            if task.actual_minutes:
                total_actual_minutes += task.actual_minutes
            
            briefing_tasks.append(
                DailyBriefingTask(
                    id=task.id,
                    title=task.title,
                    description=task.description,
                    task_type=task.task_type.value,
                    estimated_minutes=task.estimated_minutes,
                    skill_names=task.skill_names if task.skill_names else [],
                    status=task.status.value,
                    dependencies=task.dependencies if task.dependencies else [],
                    is_overdue=is_overdue,
                    days_overdue=days_overdue,
                    content=task.content if task.content else {},
                    task_date=task.task_date.date() if task.task_date else None,
                )
            )
        
        total_tasks = len(all_tasks)
        completion_pct = (completed_count / total_tasks * 100) if total_tasks > 0 else 0.0
        
        # Get focus skills from today's tasks
        focus_skills = set()
        for task in tasks:
            if task.skill_names:
                focus_skills.update(task.skill_names)
        
        # Get upcoming tasks (next 7 days) to show what's coming
        upcoming_start = target_date + timedelta(days=1)
        upcoming_end = target_date + timedelta(days=7)
        upcoming_tasks_query = db_session.query(DailyTask).filter(
            DailyTask.study_plan_id == study_plan.id,
            DailyTask.task_date >= datetime.combine(upcoming_start, datetime.min.time()),
            DailyTask.task_date < datetime.combine(upcoming_end, datetime.min.time()),
            DailyTask.status != TaskStatusEnum.COMPLETED,
            DailyTask.status != TaskStatusEnum.SKIPPED
        ).order_by(DailyTask.task_date.asc()).limit(10).all()  # Limit to 10 upcoming tasks
        
        upcoming_tasks = []
        for task in upcoming_tasks_query:
            upcoming_tasks.append(
                DailyBriefingTask(
                    id=task.id,
                    title=task.title,
                    description=task.description,
                    task_type=task.task_type.value,
                    estimated_minutes=task.estimated_minutes,
                    skill_names=task.skill_names if task.skill_names else [],
                    status=task.status.value,
                    dependencies=task.dependencies if task.dependencies else [],
                    is_overdue=False,
                    days_overdue=0,
                    content=task.content if task.content else {},
                    task_date=task.task_date.date() if task.task_date else None,
                )
            )
        
        # Calculate current week and week progress
        current_week = None
        total_weeks = study_plan.weeks
        week_progress = None
        
        # OPTIMIZATION: Calculate current week and progress more efficiently
        if study_plan.weeks_data:
            plan_start_date = None
            # Find the earliest task date to determine plan start (cache this if called frequently)
            earliest_task = db_session.query(DailyTask).filter(
                DailyTask.study_plan_id == study_plan.id
            ).order_by(DailyTask.task_date.asc()).first()
            
            if earliest_task:
                plan_start_date = earliest_task.task_date.date()
            
            if plan_start_date:
                # Calculate which week we're in (assuming 7 days per week)
                days_since_start = (target_date - plan_start_date).days
                current_week = min((days_since_start // 7) + 1, total_weeks)
                
                # Calculate week progress - OPTIMIZATION: Use aggregate query instead of loading all tasks
                week_start_date = plan_start_date + timedelta(days=(current_week - 1) * 7)
                week_end_date = week_start_date + timedelta(days=7)
                week_start_datetime = datetime.combine(week_start_date, datetime.min.time())
                week_end_datetime = datetime.combine(week_end_date, datetime.min.time())
                
                # Use COUNT query instead of loading all tasks (OPTIMIZATION)
                total_week_tasks = db_session.query(func.count(DailyTask.id)).filter(
                    DailyTask.study_plan_id == study_plan.id,
                    DailyTask.task_date >= week_start_datetime,
                    DailyTask.task_date < week_end_datetime
                ).scalar() or 0
                
                completed_week_tasks = db_session.query(func.count(DailyTask.id)).filter(
                    DailyTask.study_plan_id == study_plan.id,
                    DailyTask.task_date >= week_start_datetime,
                    DailyTask.task_date < week_end_datetime,
                    DailyTask.status == TaskStatusEnum.COMPLETED
                ).scalar() or 0
                
                week_progress = (completed_week_tasks / total_week_tasks * 100) if total_week_tasks > 0 else 0.0
        
        # Generate motivational message
        motivational_message = self._generate_motivational_message(
            completed_count=completed_count,
            pending_count=pending_count,
            overdue_count=overdue_count,
            completion_pct=completion_pct,
            focus_skills=list(focus_skills)
        )
        
        return DailyBriefingResponse(
            date=target_date,
            study_plan_id=study_plan.id,
            total_tasks=total_tasks,
            completed_tasks=completed_count,
            pending_tasks=pending_count,
            overdue_tasks=overdue_count,
            estimated_minutes=total_estimated_minutes,
            actual_minutes=total_actual_minutes if total_actual_minutes > 0 else None,
            completion_percentage=completion_pct,
            tasks=briefing_tasks,
            motivational_message=motivational_message,
            focus_skills=list(focus_skills),
            upcoming_tasks=upcoming_tasks,
            current_week=current_week,
            total_weeks=total_weeks,
            week_progress=week_progress,
        )
    
    def _generate_motivational_message(
        self,
        completed_count: int,
        pending_count: int,
        overdue_count: int,
        completion_pct: float,
        focus_skills: List[str]
    ) -> str:
        """Generate a motivational message using LLM."""
        try:
            response = self.llm.invoke(
                self.motivational_prompt.format_messages(
                    completed_count=completed_count,
                    pending_count=pending_count,
                    overdue_count=overdue_count,
                    completion_pct=round(completion_pct, 1),
                    focus_skills=", ".join(focus_skills[:5]) if focus_skills else "General skills"
                )
            )
            return response.content.strip()
        except Exception as e:
            logger.warning(f"Failed to generate motivational message: {e}")
            # Fallback message
            if completed_count > 0:
                return f"Great progress! You've completed {completed_count} task(s) today. Keep up the momentum!"
            elif pending_count > 0:
                return f"You have {pending_count} task(s) ahead. Take it one step at a time - you've got this!"
            else:
                return "Every journey begins with a single step. Let's make today count!"
    
    def update_task_status(
        self,
        task_id: int,
        status: str,
        actual_minutes: Optional[int] = None,
        *,
        db_session: Session
    ) -> DailyTask:
        """
        Update task status (e.g., mark as completed).
        
        Args:
            task_id: Task ID
            status: New status (pending, in_progress, completed, skipped)
            actual_minutes: Actual time spent (optional)
            db_session: Database session
            
        Returns:
            Updated DailyTask
        """
        task = db_session.query(DailyTask).filter(DailyTask.id == task_id).first()
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        # Update status
        task.status = TaskStatusEnum(status.lower())
        
        # Update completion fields
        if status.lower() == "completed":
            task.completed = True
            task.completed_at = datetime.now()
        else:
            task.completed = False
            task.completed_at = None
        
        # Update actual minutes if provided
        if actual_minutes is not None:
            task.actual_minutes = actual_minutes
        
        db_session.commit()
        db_session.refresh(task)
        
        logger.info(f"Updated task {task_id} to status {status}")
        return task
    
    def reschedule_task(
        self,
        task_id: int,
        new_date: date,
        reason: Optional[str] = None,
        *,
        db_session: Session
    ) -> TaskRescheduleResponse:
        """
        Reschedule a task to a new date.
        
        Args:
            task_id: Task ID
            new_date: New date for the task
            reason: Optional reason for rescheduling
            db_session: Database session
            
        Returns:
            TaskRescheduleResponse
        """
        task = db_session.query(DailyTask).filter(DailyTask.id == task_id).first()
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        old_date = task.task_date.date()
        task.task_date = datetime.combine(new_date, datetime.min.time())
        
        # If task was overdue, update status to pending
        if task.status == TaskStatusEnum.PENDING and old_date < date.today():
            task.status = TaskStatusEnum.PENDING  # Keep as pending
        
        db_session.commit()
        db_session.refresh(task)
        
        logger.info(f"Rescheduled task {task_id} from {old_date} to {new_date}")
        
        return TaskRescheduleResponse(
            task_id=task_id,
            old_date=old_date,
            new_date=new_date,
            status=task.status.value,
            message=f"Task rescheduled from {old_date} to {new_date}" + (f". Reason: {reason}" if reason else ""),
        )
    
    def process_carry_over(
        self,
        user_id: int,
        from_date: date,
        to_date: date,
        study_plan_id: Optional[int] = None,
        *,
        db_session: Session
    ) -> CarryOverSummary:
        """
        Process carry-over logic: move incomplete tasks from one date to another.
        
        Args:
            user_id: User ID
            from_date: Date to carry tasks from
            to_date: Date to carry tasks to
            study_plan_id: Specific study plan ID (uses latest if not provided)
            db_session: Database session
            
        Returns:
            CarryOverSummary with rescheduled tasks
        """
        # Get study plan
        if study_plan_id:
            study_plan = db_session.query(StudyPlan).filter(
                StudyPlan.id == study_plan_id,
                StudyPlan.user_id == user_id
            ).first()
        else:
            study_plan = db_session.query(StudyPlan).filter(
                StudyPlan.user_id == user_id
            ).order_by(StudyPlan.created_at.desc()).first()
        
        if not study_plan:
            raise ValueError(f"No study plan found for user {user_id}")
        
        # Get incomplete tasks from from_date
        from_datetime = datetime.combine(from_date, datetime.min.time())
        to_from_datetime = datetime.combine(from_date + timedelta(days=1), datetime.min.time())
        
        incomplete_tasks = db_session.query(DailyTask).filter(
            DailyTask.study_plan_id == study_plan.id,
            DailyTask.task_date >= from_datetime,
            DailyTask.task_date < to_from_datetime,
            DailyTask.status != TaskStatusEnum.COMPLETED,
            DailyTask.status != TaskStatusEnum.SKIPPED
        ).all()
        
        # Reschedule tasks
        rescheduled_tasks: List[TaskRescheduleResponse] = []
        briefing_tasks: List[DailyBriefingTask] = []
        
        for task in incomplete_tasks:
            reschedule_response = self.reschedule_task(
                task_id=task.id,
                new_date=to_date,
                reason="Carried over from previous day",
                db_session=db_session
            )
            rescheduled_tasks.append(reschedule_response)
            
            briefing_tasks.append(
                DailyBriefingTask(
                    id=task.id,
                    title=task.title,
                    description=task.description,
                    task_type=task.task_type.value,
                    estimated_minutes=task.estimated_minutes,
                    skill_names=task.skill_names if task.skill_names else [],
                    status=task.status.value,
                    dependencies=task.dependencies if task.dependencies else [],
                    is_overdue=False,
                    days_overdue=0,
                )
            )
        
        return CarryOverSummary(
            date=to_date,
            carried_over_tasks=briefing_tasks,
            total_carried_over=len(incomplete_tasks),
            rescheduled_tasks=rescheduled_tasks,
        )
    
    def auto_reschedule_overdue_tasks(
        self,
        user_id: int,
        target_date: Optional[date] = None,
        study_plan_id: Optional[int] = None,
        *,
        db_session: Session
    ) -> List[TaskRescheduleResponse]:
        """
        Automatically reschedule overdue tasks to today or next available day.
        
        Args:
            user_id: User ID
            target_date: Target date to reschedule to (defaults to today)
            study_plan_id: Specific study plan ID (uses latest if not provided)
            db_session: Database session
            
        Returns:
            List of TaskRescheduleResponse
        """
        if target_date is None:
            target_date = date.today()
        
        # Get study plan
        if study_plan_id:
            study_plan = db_session.query(StudyPlan).filter(
                StudyPlan.id == study_plan_id,
                StudyPlan.user_id == user_id
            ).first()
        else:
            study_plan = db_session.query(StudyPlan).filter(
                StudyPlan.user_id == user_id
            ).order_by(StudyPlan.created_at.desc()).first()
        
        if not study_plan:
            raise ValueError(f"No study plan found for user {user_id}")
        
        # Get overdue tasks
        overdue_cutoff = datetime.combine(target_date, datetime.min.time())
        overdue_tasks = db_session.query(DailyTask).filter(
            DailyTask.study_plan_id == study_plan.id,
            DailyTask.task_date < overdue_cutoff,
            DailyTask.status != TaskStatusEnum.COMPLETED,
            DailyTask.status != TaskStatusEnum.SKIPPED
        ).all()
        
        # Reschedule each overdue task
        rescheduled: List[TaskRescheduleResponse] = []
        for task in overdue_tasks:
            # Distribute tasks across next few days to avoid overload
            days_ahead = len(rescheduled) % 3  # Spread across 3 days
            new_date = target_date + timedelta(days=days_ahead)
            
            reschedule_response = self.reschedule_task(
                task_id=task.id,
                new_date=new_date,
                reason="Auto-rescheduled overdue task",
                db_session=db_session
            )
            rescheduled.append(reschedule_response)
        
        logger.info(f"Auto-rescheduled {len(rescheduled)} overdue tasks for user {user_id}")
        return rescheduled

