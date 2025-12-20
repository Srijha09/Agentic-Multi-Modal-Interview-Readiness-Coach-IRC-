"""
Adaptive Planning Agent - Phase 10
Modifies study plans based on learning signals from mastery tracking.

This service:
1. Analyzes mastery data to identify weak/strong skills
2. Adds reinforcement tasks for weak skills
3. Reduces repetition for strong skills
4. Adjusts difficulty of practice items
5. Logs plan modifications
"""
import logging
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.models import (
    StudyPlan, DailyTask, Week, Day, SkillMastery, PracticeItem,
    TaskTypeEnum, TaskStatusEnum
)
from app.services.mastery_tracker import MasteryTracker
from app.services.planner import StudyPlanner

logger = logging.getLogger(__name__)


class AdaptivePlanner:
    """Service for adaptively modifying study plans based on mastery data."""
    
    # Configuration constants
    WEAK_MASTERY_THRESHOLD = 0.5  # Skills below this need reinforcement
    STRONG_MASTERY_THRESHOLD = 0.8  # Skills above this can reduce repetition
    REINFORCEMENT_TASK_COUNT = 2  # Number of reinforcement tasks to add per weak skill
    MIN_DAYS_BETWEEN_REINFORCEMENT = 2  # Minimum days between reinforcement tasks
    
    def __init__(self):
        self.mastery_tracker = MasteryTracker()
        self.planner = StudyPlanner()
    
    def analyze_plan_adaptation_needs(
        self,
        user_id: int,
        study_plan_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """
        Analyze the study plan and mastery data to determine what adaptations are needed.
        
        Returns:
            {
                "weak_skills": List of skills needing reinforcement,
                "strong_skills": List of skills that can reduce repetition,
                "recommendations": List of adaptation recommendations
            }
        """
        # Get study plan
        study_plan = db.query(StudyPlan).filter(
            StudyPlan.id == study_plan_id,
            StudyPlan.user_id == user_id
        ).first()
        
        if not study_plan:
            raise ValueError(f"Study plan {study_plan_id} not found for user {user_id}")
        
        # Get all mastery records for this user
        mastery_records = db.query(SkillMastery).filter(
            SkillMastery.user_id == user_id
        ).all()
        
        # Get upcoming tasks (not completed)
        upcoming_tasks = db.query(DailyTask).filter(
            DailyTask.study_plan_id == study_plan_id,
            DailyTask.status != TaskStatusEnum.COMPLETED,
            DailyTask.task_date >= datetime.now().date()
        ).order_by(DailyTask.task_date).all()
        
        # Analyze skills
        weak_skills = []
        strong_skills = []
        recommendations = []
        
        for mastery in mastery_records:
            skill_name = mastery.skill_name
            mastery_score = mastery.mastery_score
            trend = mastery.improvement_trend
            practice_count = mastery.practice_count
            
            # Check if skill is in upcoming tasks
            skill_in_upcoming = any(
                skill_name in (task.skill_names or [])
                for task in upcoming_tasks
            )
            
            # Weak skills: low mastery, declining, or not practiced enough
            if (mastery_score < self.WEAK_MASTERY_THRESHOLD or 
                trend == "declining" or
                (practice_count < 3 and skill_in_upcoming)):
                weak_skills.append({
                    "skill_name": skill_name,
                    "mastery_score": mastery_score,
                    "trend": trend,
                    "practice_count": practice_count,
                    "reason": self._get_weak_skill_reason(mastery_score, trend, practice_count)
                })
            
            # Strong skills: high mastery and improving
            elif (mastery_score >= self.STRONG_MASTERY_THRESHOLD and 
                  trend == "improving" and
                  practice_count >= 5):
                strong_skills.append({
                    "skill_name": skill_name,
                    "mastery_score": mastery_score,
                    "trend": trend,
                    "practice_count": practice_count
                })
        
        # Generate recommendations
        for weak_skill in weak_skills:
            recommendations.append({
                "type": "reinforcement",
                "skill": weak_skill["skill_name"],
                "action": f"Add {self.REINFORCEMENT_TASK_COUNT} reinforcement practice tasks",
                "priority": "high" if weak_skill["mastery_score"] < 0.3 else "medium",
                "reason": weak_skill["reason"]
            })
        
        for strong_skill in strong_skills:
            # Count how many tasks exist for this skill
            skill_task_count = sum(
                1 for task in upcoming_tasks
                if strong_skill["skill_name"] in (task.skill_names or [])
            )
            
            if skill_task_count > 2:
                recommendations.append({
                    "type": "reduce_repetition",
                    "skill": strong_skill["skill_name"],
                    "action": f"Reduce {skill_task_count - 1} redundant tasks",
                    "priority": "low",
                    "reason": f"High mastery ({strong_skill['mastery_score']:.0%}) with improving trend"
                })
        
        return {
            "weak_skills": weak_skills,
            "strong_skills": strong_skills,
            "recommendations": recommendations,
            "total_weak": len(weak_skills),
            "total_strong": len(strong_skills)
        }
    
    def _get_weak_skill_reason(
        self,
        mastery_score: float,
        trend: str,
        practice_count: int
    ) -> str:
        """Get human-readable reason why a skill is weak."""
        reasons = []
        if mastery_score < 0.3:
            reasons.append("very low mastery")
        elif mastery_score < 0.5:
            reasons.append("low mastery")
        
        if trend == "declining":
            reasons.append("declining performance")
        
        if practice_count < 3:
            reasons.append("insufficient practice")
        
        return ", ".join(reasons) if reasons else "needs improvement"
    
    def add_reinforcement_tasks(
        self,
        user_id: int,
        study_plan_id: int,
        skill_name: str,
        count: int = None,
        db: Session = None
    ) -> List[DailyTask]:
        """
        Add reinforcement practice tasks for a weak skill.
        
        Args:
            user_id: User ID
            study_plan_id: Study plan ID
            skill_name: Skill to reinforce
            count: Number of tasks to add (defaults to REINFORCEMENT_TASK_COUNT)
            db: Database session
        
        Returns:
            List of created DailyTask objects
        """
        if count is None:
            count = self.REINFORCEMENT_TASK_COUNT
        
        # Get study plan
        study_plan = db.query(StudyPlan).filter(
            StudyPlan.id == study_plan_id,
            StudyPlan.user_id == user_id
        ).first()
        
        if not study_plan:
            raise ValueError(f"Study plan {study_plan_id} not found")
        
        # Get upcoming tasks to find insertion points
        upcoming_tasks = db.query(DailyTask).filter(
            DailyTask.study_plan_id == study_plan_id,
            DailyTask.task_date >= datetime.now().date()
        ).order_by(DailyTask.task_date).all()
        
        # Get mastery to determine difficulty
        mastery = db.query(SkillMastery).filter(
            SkillMastery.user_id == user_id,
            SkillMastery.skill_name == skill_name
        ).first()
        
        difficulty = "beginner"
        if mastery:
            if mastery.mastery_score >= 0.6:
                difficulty = "advanced"
            elif mastery.mastery_score >= 0.3:
                difficulty = "intermediate"
        
        # Find suitable dates for reinforcement tasks
        created_tasks = []
        last_task_date = None
        
        # Group tasks by date
        tasks_by_date = {}
        for task in upcoming_tasks:
            task_date = task.task_date.date() if isinstance(task.task_date, datetime) else task.task_date
            if task_date not in tasks_by_date:
                tasks_by_date[task_date] = []
            tasks_by_date[task_date].append(task)
        
        # Find dates with fewer tasks (better for adding reinforcement)
        sorted_dates = sorted(tasks_by_date.keys())
        
        for i in range(count):
            # Find a date at least MIN_DAYS_BETWEEN_REINFORCEMENT days after last task
            target_date = None
            
            if last_task_date:
                min_date = last_task_date + timedelta(days=self.MIN_DAYS_BETWEEN_REINFORCEMENT)
            else:
                min_date = datetime.now().date()
            
            # Look for a date with fewer tasks
            for date in sorted_dates:
                if date >= min_date and len(tasks_by_date.get(date, [])) < 5:
                    target_date = date
                    break
            
            # If no suitable date found, use the last date + 1 day
            if not target_date:
                if sorted_dates:
                    target_date = sorted_dates[-1] + timedelta(days=1)
                else:
                    target_date = datetime.now().date() + timedelta(days=i + 1)
            
            # Get or create day for this date
            day = self._get_or_create_day(study_plan_id, target_date, db)
            
            # Create reinforcement task
            task = DailyTask(
                study_plan_id=study_plan_id,
                day_id=day.id,
                task_date=datetime.combine(target_date, datetime.min.time()),
                task_type=TaskTypeEnum.PRACTICE,
                status=TaskStatusEnum.PENDING,
                title=f"Reinforcement Practice: {skill_name}",
                description=f"Additional practice to strengthen {skill_name} skills",
                skill_names=[skill_name],
                estimated_minutes=30,
                content={
                    "study_materials": [
                        f"Practice {skill_name} concepts",
                        f"Review {skill_name} fundamentals"
                    ],
                    "resources": [],
                    "key_concepts": [skill_name],
                    "practice_exercises": [
                        f"Complete {difficulty} level exercises for {skill_name}"
                    ],
                    "adaptive_note": f"Added by adaptive planner due to weak mastery",
                    "difficulty": difficulty
                },
                completed=False
            )
            
            db.add(task)
            created_tasks.append(task)
            last_task_date = target_date
        
        db.flush()
        return created_tasks
    
    def _get_or_create_day(
        self,
        study_plan_id: int,
        target_date: date,
        db: Session
    ) -> Day:
        """Get or create a Day record for the given date."""
        # Find the week this date belongs to
        week = db.query(Week).filter(
            Week.study_plan_id == study_plan_id
        ).order_by(Week.week_number).first()
        
        if not week:
            # Create a default week if none exists
            week = Week(
                study_plan_id=study_plan_id,
                week_number=1,
                theme="Adaptive Reinforcement",
                estimated_hours=0
            )
            db.add(week)
            db.flush()
        
        # Find day for this date (Day.date is DateTime, so we need to compare dates)
        target_datetime = datetime.combine(target_date, datetime.min.time())
        day = db.query(Day).filter(
            Day.week_id == week.id,
            func.date(Day.date) == target_date
        ).first()
        
        if not day:
            # Create day
            day = Day(
                week_id=week.id,
                day_number=1,
                date=target_datetime,
                theme="Reinforcement Day",
                estimated_hours=0.5
            )
            db.add(day)
            db.flush()
        
        return day
    
    def reduce_redundant_tasks(
        self,
        user_id: int,
        study_plan_id: int,
        skill_name: str,
        max_tasks: int = 2,
        db: Session = None
    ) -> List[DailyTask]:
        """
        Remove or mark redundant tasks for a strong skill.
        
        Args:
            user_id: User ID
            study_plan_id: Study plan ID
            skill_name: Skill that's strong
            max_tasks: Maximum number of tasks to keep
            db: Database session
        
        Returns:
            List of tasks that were removed/marked
        """
        # Get upcoming tasks for this skill
        upcoming_tasks = db.query(DailyTask).filter(
            DailyTask.study_plan_id == study_plan_id,
            DailyTask.status != TaskStatusEnum.COMPLETED,
            DailyTask.task_date >= datetime.now().date()
        ).all()
        
        skill_tasks = [
            task for task in upcoming_tasks
            if skill_name in (task.skill_names or [])
        ]
        
        # Sort by date (keep earlier tasks, remove later ones)
        skill_tasks.sort(key=lambda t: t.task_date)
        
        # Mark excess tasks as optional or remove them
        removed_tasks = []
        if len(skill_tasks) > max_tasks:
            excess_tasks = skill_tasks[max_tasks:]
            for task in excess_tasks:
                # Mark as optional in content
                if not task.content:
                    task.content = {}
                task.content["adaptive_note"] = "Marked optional due to strong mastery"
                task.content["is_optional"] = True
                removed_tasks.append(task)
        
        db.flush()
        return removed_tasks
    
    def adapt_plan(
        self,
        user_id: int,
        study_plan_id: int,
        apply_recommendations: bool = True,
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Main method to adapt a study plan based on mastery data.
        
        Args:
            user_id: User ID
            study_plan_id: Study plan ID
            apply_recommendations: If True, automatically apply recommendations
            db: Database session
        
        Returns:
            {
                "analysis": Analysis results,
                "changes": List of changes made,
                "plan_diff": Plan diff log
            }
        """
        # Analyze adaptation needs
        analysis = self.analyze_plan_adaptation_needs(user_id, study_plan_id, db)
        
        changes = []
        plan_diff = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "study_plan_id": study_plan_id,
            "changes": []
        }
        
        if apply_recommendations:
            # Apply reinforcement for weak skills
            for weak_skill in analysis["weak_skills"]:
                skill_name = weak_skill["skill_name"]
                try:
                    new_tasks = self.add_reinforcement_tasks(
                        user_id, study_plan_id, skill_name, db=db
                    )
                    changes.append({
                        "type": "added_reinforcement",
                        "skill": skill_name,
                        "tasks_added": len(new_tasks),
                        "task_ids": [t.id for t in new_tasks]
                    })
                    plan_diff["changes"].append({
                        "action": "add",
                        "type": "task",
                        "skill": skill_name,
                        "count": len(new_tasks),
                        "reason": weak_skill["reason"]
                    })
                except Exception as e:
                    logger.error(f"Error adding reinforcement for {skill_name}: {e}")
                    changes.append({
                        "type": "error",
                        "skill": skill_name,
                        "error": str(e)
                    })
            
            # Reduce repetition for strong skills
            for strong_skill in analysis["strong_skills"]:
                skill_name = strong_skill["skill_name"]
                try:
                    removed_tasks = self.reduce_redundant_tasks(
                        user_id, study_plan_id, skill_name, max_tasks=2, db=db
                    )
                    if removed_tasks:
                        changes.append({
                            "type": "reduced_repetition",
                            "skill": skill_name,
                            "tasks_marked_optional": len(removed_tasks),
                            "task_ids": [t.id for t in removed_tasks]
                        })
                        plan_diff["changes"].append({
                            "action": "modify",
                            "type": "task",
                            "skill": skill_name,
                            "count": len(removed_tasks),
                            "reason": "Strong mastery, reducing repetition"
                        })
                except Exception as e:
                    logger.error(f"Error reducing repetition for {skill_name}: {e}")
        
        # Store plan diff in study plan metadata
        study_plan = db.query(StudyPlan).filter(
            StudyPlan.id == study_plan_id
        ).first()
        
        if study_plan:
            if not study_plan.plan_data:
                study_plan.plan_data = {}
            if "adaptation_history" not in study_plan.plan_data:
                study_plan.plan_data["adaptation_history"] = []
            study_plan.plan_data["adaptation_history"].append(plan_diff)
            study_plan.updated_at = datetime.now()
            db.flush()
        
        return {
            "analysis": analysis,
            "changes": changes,
            "plan_diff": plan_diff,
            "summary": {
                "reinforcement_tasks_added": sum(
                    c.get("tasks_added", 0) for c in changes
                    if c["type"] == "added_reinforcement"
                ),
                "tasks_marked_optional": sum(
                    c.get("tasks_marked_optional", 0) for c in changes
                    if c["type"] == "reduced_repetition"
                )
            }
        }

