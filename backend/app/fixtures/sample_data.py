"""
Sample data fixtures for testing and development.
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List


def get_sample_user() -> Dict[str, Any]:
    """Get sample user data."""
    return {
        "email": "test@example.com",
        "name": "Test User"
    }


def get_sample_skill() -> Dict[str, Any]:
    """Get sample skill data."""
    return {
        "name": "Python",
        "category": "programming",
        "description": "Python programming language",
        "parent_skill_id": None
    }


def get_sample_skill_evidence() -> Dict[str, Any]:
    """Get sample skill evidence data."""
    return {
        "skill_id": 1,
        "document_id": 1,
        "evidence_text": "Developed REST APIs using Python and Flask framework",
        "section_name": "Experience",
        "confidence_score": 0.9,
        "start_char": 100,
        "end_char": 150
    }


def get_sample_gap() -> Dict[str, Any]:
    """Get sample gap data."""
    return {
        "skill_id": 1,
        "user_id": 1,
        "required_skill_name": "Docker",
        "coverage_status": "missing",
        "priority": "high",
        "gap_reason": "Docker is required for containerization but not found in resume",
        "evidence_summary": "No mention of Docker or containerization in experience",
        "estimated_learning_hours": 8.0
    }


def get_sample_study_plan() -> Dict[str, Any]:
    """Get sample study plan data."""
    interview_date = datetime.now() + timedelta(weeks=4)
    
    return {
        "user_id": 1,
        "interview_date": interview_date.isoformat(),
        "weeks": 4,
        "hours_per_week": 10.0,
        "focus_areas": ["Docker", "Kubernetes", "System Design"],
        "plan_data": get_sample_plan_structure()
    }


def get_sample_plan_structure() -> Dict[str, Any]:
    """Get sample plan structure (weeks/days/tasks)."""
    weeks = []
    start_date = datetime.now().date()
    
    for week_num in range(1, 5):
        week = {
            "week_number": week_num,
            "theme": f"Week {week_num} Theme",
            "focus_skills": ["Skill1", "Skill2"],
            "estimated_hours": 10.0,
            "days": []
        }
        
        # Add 5 days per week (Mon-Fri)
        for day_num in range(1, 6):
            day_date = start_date + timedelta(weeks=week_num-1, days=day_num-1)
            day = {
                "day_number": (week_num - 1) * 5 + day_num,
                "date": day_date.isoformat(),
                "theme": f"Day {day_num}",
                "estimated_hours": 2.0,
                "tasks": [
                    {
                        "task_type": "learn",
                        "title": f"Learn Topic {day_num}",
                        "description": f"Study materials for topic {day_num}",
                        "skill_names": ["Skill1"],
                        "estimated_minutes": 60,
                        "dependencies": [],
                        "content": {}
                    },
                    {
                        "task_type": "practice",
                        "title": f"Practice Topic {day_num}",
                        "description": f"Practice exercises for topic {day_num}",
                        "skill_names": ["Skill1"],
                        "estimated_minutes": 30,
                        "dependencies": [],
                        "content": {}
                    }
                ]
            }
            week["days"].append(day)
        
        weeks.append(week)
    
    return {"weeks": weeks}


def get_sample_task() -> Dict[str, Any]:
    """Get sample task data."""
    return {
        "study_plan_id": 1,
        "task_type": "learn",
        "title": "Learn Docker Basics",
        "description": "Study Docker fundamentals and containerization concepts",
        "skill_names": ["Docker"],
        "estimated_minutes": 60,
        "dependencies": [],
        "content": {
            "resources": ["https://docs.docker.com/get-started/"],
            "topics": ["Containers", "Images", "Dockerfile"]
        }
    }


def get_sample_practice_item() -> Dict[str, Any]:
    """Get sample practice item data."""
    return {
        "task_id": 1,
        "practice_type": "quiz",
        "title": "Docker Fundamentals Quiz",
        "question": "What is the difference between a Docker image and a container?",
        "skill_names": ["Docker"],
        "difficulty": "intermediate",
        "content": {
            "options": [
                "Image is a template, container is a running instance",
                "Container is a template, image is a running instance",
                "They are the same thing",
                "Image is for development, container is for production"
            ],
            "correct_answer": 0
        },
        "expected_answer": "A Docker image is a read-only template used to create containers. A container is a running instance of an image.",
        "rubric": {
            "criteria": [
                {"name": "Accuracy", "weight": 0.5, "max_score": 1.0},
                {"name": "Completeness", "weight": 0.3, "max_score": 1.0},
                {"name": "Clarity", "weight": 0.2, "max_score": 1.0}
            ]
        }
    }


def get_sample_practice_attempt() -> Dict[str, Any]:
    """Get sample practice attempt data."""
    return {
        "user_id": 1,
        "practice_item_id": 1,
        "task_id": 1,
        "answer": "A Docker image is a template used to create containers, which are running instances.",
        "time_spent_seconds": 120
    }


def get_sample_evaluation() -> Dict[str, Any]:
    """Get sample evaluation data."""
    return {
        "practice_attempt_id": 1,
        "rubric_id": 1,
        "overall_score": 0.85,
        "criterion_scores": {
            "Accuracy": 0.9,
            "Completeness": 0.8,
            "Clarity": 0.85
        },
        "strengths": [
            "Correct understanding of Docker concepts",
            "Clear explanation"
        ],
        "weaknesses": [
            "Could provide more detail on container lifecycle"
        ],
        "feedback": "Good understanding of Docker basics. Consider learning more about container lifecycle management.",
        "evaluator_notes": "User demonstrates solid grasp of fundamentals"
    }


def get_sample_rubric() -> Dict[str, Any]:
    """Get sample rubric data."""
    return {
        "practice_type": "quiz",
        "criteria": [
            {
                "name": "Accuracy",
                "description": "Correctness of the answer",
                "weight": 0.5,
                "max_score": 1.0
            },
            {
                "name": "Completeness",
                "description": "Thoroughness of the response",
                "weight": 0.3,
                "max_score": 1.0
            },
            {
                "name": "Clarity",
                "description": "Clarity and organization of the answer",
                "weight": 0.2,
                "max_score": 1.0
            }
        ],
        "total_max_score": 1.0
    }


def get_sample_mastery() -> Dict[str, Any]:
    """Get sample mastery data."""
    return {
        "user_id": 1,
        "skill_name": "Docker",
        "mastery_score": 0.75,
        "last_practiced": datetime.now().isoformat(),
        "practice_count": 5,
        "improvement_trend": "improving"
    }


def get_sample_calendar_event() -> Dict[str, Any]:
    """Get sample calendar event data."""
    start_time = datetime.now() + timedelta(days=1)
    end_time = start_time + timedelta(hours=2)
    
    return {
        "study_plan_id": 1,
        "task_id": 1,
        "title": "Study Session: Docker Basics",
        "description": "Learn Docker fundamentals",
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "location": "Home",
        "recurrence_rule": None
    }


def get_sample_gap_report() -> Dict[str, Any]:
    """Get sample gap report data."""
    return {
        "user_id": 1,
        "total_gaps": 5,
        "critical_gaps": 2,
        "high_priority_gaps": 2,
        "gaps": [
            get_sample_gap(),
            {
                **get_sample_gap(),
                "required_skill_name": "Kubernetes",
                "priority": "critical"
            }
        ],
        "generated_at": datetime.now().isoformat()
    }

