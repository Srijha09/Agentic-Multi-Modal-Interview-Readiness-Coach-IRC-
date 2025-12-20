"""
Calendar Service - Phase 11
Generates ICS calendar files from study plans.

This service:
1. Creates calendar events from study plan tasks
2. Generates ICS (iCalendar) format files
3. Regenerates calendar on plan updates
4. Manages calendar event synchronization
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.models import (
    StudyPlan, DailyTask, CalendarEvent, TaskStatusEnum
)

logger = logging.getLogger(__name__)


class CalendarService:
    """Service for generating calendar events and ICS exports."""
    
    # Default event duration (in minutes)
    DEFAULT_EVENT_DURATION = 60  # 1 hour
    
    def generate_calendar_events_from_plan(
        self,
        study_plan_id: int,
        user_id: int,
        db: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        regenerate: bool = False
    ) -> List[CalendarEvent]:
        """
        Generate calendar events from all tasks in a study plan.
        
        Args:
            study_plan_id: Study plan ID
            user_id: User ID
            db: Database session
            start_date: Only include tasks after this date (defaults to today)
            end_date: Only include tasks before this date (defaults to plan end)
            regenerate: If True, delete existing events and regenerate
        
        Returns:
            List of created CalendarEvent objects
        """
        # Get study plan
        study_plan = db.query(StudyPlan).filter(
            StudyPlan.id == study_plan_id,
            StudyPlan.user_id == user_id
        ).first()
        
        if not study_plan:
            raise ValueError(f"Study plan {study_plan_id} not found for user {user_id}")
        
        # Delete existing events if regenerating
        if regenerate:
            existing_events = db.query(CalendarEvent).filter(
                CalendarEvent.study_plan_id == study_plan_id
            ).all()
            for event in existing_events:
                db.delete(event)
            db.flush()
            logger.info(f"Deleted {len(existing_events)} existing calendar events for plan {study_plan_id}")
        
        # Get all tasks for this plan
        query = db.query(DailyTask).filter(
            DailyTask.study_plan_id == study_plan_id
        )
        
        # Apply date filters
        if start_date:
            query = query.filter(DailyTask.task_date >= start_date)
        if end_date:
            query = query.filter(DailyTask.task_date <= end_date)
        
        tasks = query.order_by(DailyTask.task_date).all()
        
        if not tasks:
            logger.warning(f"No tasks found for study plan {study_plan_id}")
            return []
        
        # Generate calendar events
        events = []
        for task in tasks:
            # Skip completed tasks (optional - you might want to include them)
            # if task.status == TaskStatusEnum.COMPLETED:
            #     continue
            
            event = self._create_event_from_task(task, study_plan_id, db)
            if event:
                events.append(event)
        
        db.flush()
        logger.info(f"Generated {len(events)} calendar events for plan {study_plan_id}")
        
        return events
    
    def _create_event_from_task(
        self,
        task: DailyTask,
        study_plan_id: int,
        db: Session
    ) -> Optional[CalendarEvent]:
        """Create a calendar event from a daily task."""
        # Calculate start and end times
        task_date = task.task_date
        if isinstance(task_date, datetime):
            start_time = task_date
        else:
            # If task_date is date, convert to datetime (default to 9 AM)
            start_time = datetime.combine(task_date, datetime.min.time().replace(hour=9))
        
        # Calculate duration from estimated_minutes or use default
        duration_minutes = task.estimated_minutes or self.DEFAULT_EVENT_DURATION
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        # Generate unique ICS UID
        ics_uid = f"{uuid4()}@irc-coach.local"
        
        # Build description from task content
        description_parts = [task.description]
        
        if task.content:
            if task.content.get("study_materials"):
                description_parts.append("\n\nStudy Materials:")
                for material in task.content.get("study_materials", []):
                    description_parts.append(f"- {material}")
            
            if task.content.get("key_concepts"):
                description_parts.append("\n\nKey Concepts:")
                for concept in task.content.get("key_concepts", []):
                    description_parts.append(f"- {concept}")
            
            if task.content.get("resources"):
                description_parts.append("\n\nResources:")
                for resource in task.content.get("resources", [])[:5]:  # Limit to 5
                    description_parts.append(f"- {resource}")
        
        description = "\n".join(description_parts)
        
        # Build location (optional)
        location = None
        if task.skill_names:
            location = f"Skills: {', '.join(task.skill_names)}"
        
        # Check if event already exists
        existing_event = db.query(CalendarEvent).filter(
            CalendarEvent.task_id == task.id
        ).first()
        
        if existing_event:
            # Update existing event
            existing_event.title = task.title
            existing_event.description = description
            existing_event.start_time = start_time
            existing_event.end_time = end_time
            existing_event.location = location
            existing_event.updated_at = datetime.now()
            return existing_event
        
        # Create new event
        event = CalendarEvent(
            study_plan_id=study_plan_id,
            task_id=task.id,
            title=task.title,
            description=description,
            start_time=start_time,
            end_time=end_time,
            location=location,
            ics_uid=ics_uid,
            synced=False
        )
        
        db.add(event)
        return event
    
    def generate_ics_file(
        self,
        study_plan_id: int,
        user_id: int,
        db: Session,
        calendar_name: Optional[str] = None
    ) -> str:
        """
        Generate ICS (iCalendar) file content from study plan.
        
        Args:
            study_plan_id: Study plan ID
            user_id: User ID
            db: Database session
            calendar_name: Name for the calendar (defaults to "Study Plan")
        
        Returns:
            ICS file content as string
        """
        # Get study plan
        study_plan = db.query(StudyPlan).filter(
            StudyPlan.id == study_plan_id,
            StudyPlan.user_id == user_id
        ).first()
        
        if not study_plan:
            raise ValueError(f"Study plan {study_plan_id} not found")
        
        # Ensure calendar events exist
        events = db.query(CalendarEvent).filter(
            CalendarEvent.study_plan_id == study_plan_id
        ).all()
        
        if not events:
            # Generate events if they don't exist
            logger.info(f"No calendar events found, generating from tasks...")
            events = self.generate_calendar_events_from_plan(
                study_plan_id, user_id, db, regenerate=False
            )
        
        # Generate ICS content
        calendar_name = calendar_name or f"Study Plan - {study_plan_id}"
        ics_lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Interview Readiness Coach//Study Plan//EN",
            f"X-WR-CALNAME:{calendar_name}",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH"
        ]
        
        # Add timezone (UTC)
        ics_lines.extend([
            "BEGIN:VTIMEZONE",
            "TZID:UTC",
            "BEGIN:STANDARD",
            "DTSTART:19700101T000000Z",
            "TZOFFSETFROM:+0000",
            "TZOFFSETTO:+0000",
            "TZNAME:UTC",
            "END:STANDARD",
            "END:VTIMEZONE"
        ])
        
        # Add events
        for event in events:
            event_lines = self._event_to_ics(event)
            ics_lines.extend(event_lines)
        
        ics_lines.append("END:VCALENDAR")
        
        return "\r\n".join(ics_lines)
    
    def _event_to_ics(self, event: CalendarEvent) -> List[str]:
        """Convert a CalendarEvent to ICS format."""
        # Format datetime to ICS format (UTC)
        def format_datetime(dt: datetime) -> str:
            if dt.tzinfo is None:
                # Assume UTC if no timezone
                dt = dt.replace(tzinfo=None)
            return dt.strftime("%Y%m%dT%H%M%SZ")
        
        def escape_text(text: str) -> str:
            """Escape text for ICS format."""
            if not text:
                return ""
            # Replace special characters
            text = text.replace("\\", "\\\\")
            text = text.replace(",", "\\,")
            text = text.replace(";", "\\;")
            text = text.replace("\n", "\\n")
            return text
        
        lines = [
            "BEGIN:VEVENT",
            f"UID:{event.ics_uid or uuid4()}@irc-coach.local",
            f"DTSTART:{format_datetime(event.start_time)}",
            f"DTEND:{format_datetime(event.end_time)}",
            f"SUMMARY:{escape_text(event.title)}",
            f"DTSTAMP:{format_datetime(datetime.now())}",
            f"CREATED:{format_datetime(event.created_at)}"
        ]
        
        if event.description:
            # ICS has 75 character line limit, so we need to fold long lines
            desc = escape_text(event.description)
            if len(desc) > 75:
                # Fold the description
                folded_desc = ""
                for i in range(0, len(desc), 75):
                    if i > 0:
                        folded_desc += "\r\n "
                    folded_desc += desc[i:i+75]
                lines.append(f"DESCRIPTION:{folded_desc}")
            else:
                lines.append(f"DESCRIPTION:{desc}")
        
        if event.location:
            lines.append(f"LOCATION:{escape_text(event.location)}")
        
        if event.task_id:
            lines.append(f"URL:http://irc-coach.local/tasks/{event.task_id}")
        
        lines.append("END:VEVENT")
        
        return lines
    
    def regenerate_calendar(
        self,
        study_plan_id: int,
        user_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """
        Regenerate calendar events for a study plan.
        Useful when plan is updated.
        
        Returns:
            Summary of regeneration
        """
        events = self.generate_calendar_events_from_plan(
            study_plan_id, user_id, db, regenerate=True
        )
        
        return {
            "study_plan_id": study_plan_id,
            "events_generated": len(events),
            "regenerated_at": datetime.now().isoformat()
        }

