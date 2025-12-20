"""
Mastery Tracking Service - Phase 9
Updates skill mastery based on practice attempt evaluations.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.models import (
    SkillMastery, PracticeAttempt, Evaluation, PracticeItem, User
)

logger = logging.getLogger(__name__)


class MasteryTracker:
    """Service for tracking and updating skill mastery."""
    
    # Configuration constants
    RECENT_ATTEMPTS_WEIGHT = 0.7  # Weight for recent attempts (last 10)
    OLDER_ATTEMPTS_WEIGHT = 0.3   # Weight for older attempts
    TREND_WINDOW = 5              # Number of recent attempts to analyze for trend
    MIN_ATTEMPTS_FOR_TREND = 3    # Minimum attempts needed to calculate trend
    
    def update_mastery_from_evaluation(
        self,
        evaluation: Evaluation,
        db: Session
    ) -> SkillMastery:
        """Update mastery scores for skills associated with the evaluated attempt."""
        # Get the practice attempt
        attempt = db.query(PracticeAttempt).filter(
            PracticeAttempt.id == evaluation.practice_attempt_id
        ).first()
        
        if not attempt:
            logger.error(f"Practice attempt {evaluation.practice_attempt_id} not found")
            return None
        
        # Get the practice item to find associated skills
        practice_item = db.query(PracticeItem).filter(
            PracticeItem.id == attempt.practice_item_id
        ).first()
        
        if not practice_item:
            logger.error(f"Practice item {attempt.practice_item_id} not found")
            return None
        
        # Get user_id from attempt
        user_id = attempt.user_id
        
        # Update mastery for each skill associated with the practice item
        skill_names = practice_item.skill_names or []
        if not skill_names:
            # If no skills, use a default or skip
            logger.warning(f"Practice item {practice_item.id} has no associated skills")
            return None
        
        updated_masteries = []
        for skill_name in skill_names:
            mastery = self._update_skill_mastery(
                user_id=user_id,
                skill_name=skill_name,
                evaluation_score=evaluation.overall_score,
                db=db
            )
            if mastery:
                updated_masteries.append(mastery)
        
        # Return the first updated mastery (or None)
        return updated_masteries[0] if updated_masteries else None
    
    def _update_skill_mastery(
        self,
        user_id: int,
        skill_name: str,
        evaluation_score: float,
        db: Session
    ) -> Optional[SkillMastery]:
        """Update mastery for a specific skill based on evaluation score."""
        # Get or create mastery record
        mastery = db.query(SkillMastery).filter(
            SkillMastery.user_id == user_id,
            SkillMastery.skill_name == skill_name
        ).first()
        
        if not mastery:
            # Create new mastery record
            mastery = SkillMastery(
                user_id=user_id,
                skill_name=skill_name,
                mastery_score=0.0,
                practice_count=0,
                last_practiced=None
            )
            db.add(mastery)
            db.flush()  # Flush to get the ID
        
        # Get recent evaluation scores for this skill
        recent_scores = self._get_recent_evaluation_scores(
            user_id=user_id,
            skill_name=skill_name,
            db=db
        )
        
        # Calculate new mastery score (weighted average)
        new_mastery_score = self._calculate_mastery_score(
            current_score=mastery.mastery_score,
            recent_scores=recent_scores,
            new_score=evaluation_score
        )
        
        # Clamp to [0.0, 1.0]
        new_mastery_score = max(0.0, min(1.0, new_mastery_score))
        
        # Calculate improvement trend
        trend = self._calculate_trend(recent_scores + [evaluation_score])
        
        # Update mastery record
        mastery.mastery_score = new_mastery_score
        mastery.practice_count += 1
        mastery.last_practiced = datetime.utcnow()
        mastery.improvement_trend = trend
        mastery.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(mastery)
        
        return mastery
    
    def _get_recent_evaluation_scores(
        self,
        user_id: int,
        skill_name: str,
        db: Session,
        limit: int = 20
    ) -> List[float]:
        """Get recent evaluation scores for a skill."""
        # Query recent evaluations for this skill
        # Get all recent evaluations for the user with skill names
        recent_evaluations = db.query(
            Evaluation.overall_score,
            PracticeItem.skill_names
        ).join(
            PracticeAttempt, Evaluation.practice_attempt_id == PracticeAttempt.id
        ).join(
            PracticeItem, PracticeAttempt.practice_item_id == PracticeItem.id
        ).filter(
            PracticeAttempt.user_id == user_id
        ).order_by(
            Evaluation.created_at.desc()
        ).limit(limit * 3).all()  # Get more to filter by skill
        
        # Filter by skill_name (since JSON contains doesn't work well in SQLite)
        scores = []
        for score, skill_names in recent_evaluations:
            # Check if skill_name is in the skill_names list
            if skill_names and skill_name in skill_names:
                scores.append(score)
                if len(scores) >= limit:
                    break
        
        return scores
    
    def _calculate_mastery_score(
        self,
        current_score: float,
        recent_scores: List[float],
        new_score: float
    ) -> float:
        """Calculate new mastery score using weighted average."""
        if not recent_scores:
            # First attempt - use the new score directly
            return new_score
        
        # Add new score to recent scores
        all_scores = [new_score] + recent_scores[:9]  # Last 10 scores including new one
        
        if len(all_scores) == 1:
            # Only one score
            return all_scores[0]
        
        # Calculate weighted average
        # Recent scores (last 5) get higher weight
        recent_window = min(5, len(all_scores))
        recent = all_scores[:recent_window]
        older = all_scores[recent_window:]
        
        recent_avg = sum(recent) / len(recent) if recent else current_score
        older_avg = sum(older) / len(older) if older else current_score
        
        # Weighted combination
        new_score = (
            self.RECENT_ATTEMPTS_WEIGHT * recent_avg +
            self.OLDER_ATTEMPTS_WEIGHT * older_avg
        )
        
        return new_score
    
    def _calculate_trend(self, scores: List[float]) -> Optional[str]:
        """Calculate improvement trend from recent scores."""
        if len(scores) < self.MIN_ATTEMPTS_FOR_TREND:
            return None
        
        # Use last TREND_WINDOW scores
        trend_scores = scores[:self.TREND_WINDOW]
        
        if len(trend_scores) < 2:
            return None
        
        # Split into two halves
        mid = len(trend_scores) // 2
        first_half = trend_scores[mid:]
        second_half = trend_scores[:mid]
        
        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)
        
        diff = second_avg - first_avg
        
        # Threshold for trend determination
        threshold = 0.05  # 5% change
        
        if diff > threshold:
            return "improving"
        elif diff < -threshold:
            return "declining"
        else:
            return "stable"
    
    def get_user_mastery_stats(
        self,
        user_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """Get comprehensive mastery statistics for a user."""
        # Get all mastery records
        masteries = db.query(SkillMastery).filter(
            SkillMastery.user_id == user_id
        ).all()
        
        if not masteries:
            return {
                "total_skills": 0,
                "average_mastery": 0.0,
                "skills_by_level": {},
                "improving_skills": 0,
                "stable_skills": 0,
                "declining_skills": 0,
                "total_practice_count": 0,
                "recent_practice_count": 0
            }
        
        # Calculate statistics
        total_skills = len(masteries)
        average_mastery = sum(m.mastery_score for m in masteries) / total_skills if total_skills > 0 else 0.0
        
        # Skills by mastery level
        skills_by_level = {
            "beginner": 0,      # 0.0 - 0.3
            "intermediate": 0,  # 0.3 - 0.6
            "advanced": 0,      # 0.6 - 0.8
            "expert": 0         # 0.8 - 1.0
        }
        
        improving = 0
        stable = 0
        declining = 0
        total_practice = 0
        
        for mastery in masteries:
            score = mastery.mastery_score
            if score < 0.3:
                skills_by_level["beginner"] += 1
            elif score < 0.6:
                skills_by_level["intermediate"] += 1
            elif score < 0.8:
                skills_by_level["advanced"] += 1
            else:
                skills_by_level["expert"] += 1
            
            if mastery.improvement_trend == "improving":
                improving += 1
            elif mastery.improvement_trend == "stable":
                stable += 1
            elif mastery.improvement_trend == "declining":
                declining += 1
            
            total_practice += mastery.practice_count
        
        # Recent practice count (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_practice = db.query(func.count(PracticeAttempt.id)).join(
            PracticeItem, PracticeAttempt.practice_item_id == PracticeItem.id
        ).filter(
            PracticeAttempt.user_id == user_id,
            PracticeAttempt.created_at >= seven_days_ago
        ).scalar() or 0
        
        return {
            "total_skills": total_skills,
            "average_mastery": round(average_mastery, 3),
            "skills_by_level": skills_by_level,
            "improving_skills": improving,
            "stable_skills": stable,
            "declining_skills": declining,
            "total_practice_count": total_practice,
            "recent_practice_count": recent_practice
        }
    
    def get_skill_mastery(
        self,
        user_id: int,
        skill_name: str,
        db: Session
    ) -> Optional[SkillMastery]:
        """Get mastery record for a specific skill."""
        return db.query(SkillMastery).filter(
            SkillMastery.user_id == user_id,
            SkillMastery.skill_name == skill_name
        ).first()
    
    def get_all_user_masteries(
        self,
        user_id: int,
        db: Session
    ) -> List[SkillMastery]:
        """Get all mastery records for a user."""
        return db.query(SkillMastery).filter(
            SkillMastery.user_id == user_id
        ).order_by(SkillMastery.mastery_score.desc()).all()

