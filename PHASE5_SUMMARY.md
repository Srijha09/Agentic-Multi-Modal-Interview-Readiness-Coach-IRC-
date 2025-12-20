# Phase 5: Planner Agent (Multi-Week Study Plan) - Summary

## ✅ Completed Deliverables

### 1. Planner Service (`backend/app/services/planner.py`)
- **LLM-based study plan generation** from skill gaps
- Takes user constraints:
  - Interview date (optional)
  - Number of weeks
  - Hours per week
- Generates structured plans with:
  - **Weekly themes** (e.g., "Deep Learning Fundamentals", "System Design Patterns")
  - **Focus skills** per week (which gaps are addressed)
  - **Daily breakdown** with tasks
  - **Task types**: learn, practice, review
  - **Time estimates** for each task
  - **Dependencies** between tasks

### 2. Plan Generation Logic
- **Prioritization**: Critical and high-priority gaps addressed in early weeks
- **Time distribution**: Evenly distributes learning across weeks
- **Learn → Practice → Review cycles**: Structured learning approach
- **Constraint handling**: Respects hours_per_week and interview date
- **Fallback plan**: Simple plan generation if LLM fails

### 3. Database Integration
- **StudyPlan**: Stores plan metadata and full plan structure (JSON)
- **Week**: Weekly themes and focus skills
- **Day**: Daily themes and time estimates
- **DailyTask**: Individual tasks with types, descriptions, time estimates

### 4. API Endpoints (`backend/app/api/v1/endpoints/plans.py`)
- `POST /api/v1/plans/generate`: Generate a new study plan
  - Parameters: `user_id`, `interview_date` (optional), `weeks`, `hours_per_week`
  - Returns: `StudyPlanResponse` with full plan structure
- `GET /api/v1/plans/{plan_id}`: Get plan by ID
- `GET /api/v1/plans/user/{user_id}/latest`: Get latest plan for user

### 5. Validation Script (`backend/scripts/validate_phase5.py`)
- Validates all imports
- Checks router registration
- Validates schema enums

## 📊 Study Plan Structure

```json
{
  "id": 1,
  "user_id": 1,
  "interview_date": "2024-02-15T00:00:00Z",
  "weeks": 4,
  "hours_per_week": 10.0,
  "focus_areas": ["Python", "Machine Learning", "Deep Learning"],
  "total_estimated_hours": 40.0,
  "completion_percentage": 0.0,
  "weeks_data": [
    {
      "id": 1,
      "week_number": 1,
      "theme": "Week 1: Deep Learning Fundamentals",
      "focus_skills": ["PyTorch", "Neural Networks"],
      "estimated_hours": 10.0,
      "days": [
        {
          "id": 1,
          "day_number": 1,
          "date": "2024-01-15",
          "theme": "Introduction to Deep Learning",
          "estimated_hours": 2.0,
          "tasks": [
            {
              "id": 1,
              "task_type": "learn",
              "title": "Read Deep Learning Basics",
              "description": "Study neural network fundamentals",
              "skill_names": ["Deep Learning"],
              "estimated_minutes": 60,
              "status": "pending"
            }
          ]
        }
      ]
    }
  ]
}
```

## 🔧 Usage

### Generate Plan via API

```bash
# Generate a 4-week plan with 10 hours/week
curl -X POST "http://localhost:8000/api/v1/plans/generate?user_id=1&weeks=4&hours_per_week=10.0"

# With interview date
curl -X POST "http://localhost:8000/api/v1/plans/generate?user_id=1&weeks=4&hours_per_week=10.0&interview_date=2024-02-15T00:00:00Z"
```

### Get Latest Plan

```bash
curl "http://localhost:8000/api/v1/plans/user/1/latest"
```

## ✅ Validation Criteria Met

- ✅ **Plans respect time limits**: Hours per week constraint enforced
- ✅ **Tasks map directly to gaps**: Each task addresses specific skill gaps
- ✅ **Weekly themes**: Organized by learning focus
- ✅ **Daily breakdown**: Tasks scheduled with time estimates
- ✅ **Constraint-aware**: Interview date and time availability considered

## 📝 Next Steps (Phase 6)

Phase 5 provides the foundation for Phase 6: **Daily Coach Agent**, which will:
- Display daily tasks to the user
- Track task completion
- Reschedule missed tasks
- Provide daily briefings

## 🎯 Key Features

1. **Personalized**: Plans generated from user's specific skill gaps
2. **Structured**: Weekly themes and daily task breakdowns
3. **Time-aware**: Respects user's available time and interview deadline
4. **Prioritized**: Critical gaps addressed first
5. **Flexible**: Learn → Practice → Review cycles for effective learning


