# Phase 6: Daily Coach Agent - Summary

## ✅ Completed Deliverables

### 1. Daily Coach Service (`app/services/daily_coach.py`)

The `DailyCoach` class provides comprehensive daily execution and accountability features:

#### Core Features:
- **Daily Task Briefing**: Get a comprehensive overview of tasks for a specific date
  - Lists all tasks (pending, completed, overdue)
  - Calculates completion percentage
  - Identifies overdue tasks with days overdue
  - Generates motivational messages using LLM
  - Extracts focus skills for the day

- **Task Status Updates**: Update task status (pending, in_progress, completed, skipped)
  - Tracks actual time spent vs. estimated time
  - Automatically sets completion timestamps
  - Updates task completion flags

- **Task Rescheduling**: Move tasks to different dates
  - Manual rescheduling with optional reason
  - Updates task dates while preserving relationships
  - Handles status updates for overdue tasks

- **Carry-Over Logic**: Automatically move incomplete tasks forward
  - Processes tasks from one date to another
  - Maintains task relationships and dependencies
  - Provides summary of carried-over tasks

- **Auto-Reschedule Overdue Tasks**: Automatically reschedule overdue tasks
  - Distributes tasks across multiple days to avoid overload
  - Spreads tasks across next 3 days by default
  - Handles bulk rescheduling efficiently

### 2. API Endpoints (`app/api/v1/endpoints/coach.py`)

#### Endpoints Created:
1. **GET `/api/v1/coach/briefing`**
   - Get daily briefing for a user
   - Parameters: `user_id`, `target_date` (optional), `study_plan_id` (optional)
   - Returns: `DailyBriefingResponse` with tasks, progress, and motivational message

2. **POST `/api/v1/coach/tasks/{task_id}/complete`**
   - Mark a task as completed
   - Parameters: `task_id`, `actual_minutes` (optional)
   - Returns: Task completion confirmation

3. **POST `/api/v1/coach/tasks/{task_id}/update`**
   - Update task status (pending, in_progress, completed, skipped)
   - Body: `TaskUpdateRequest` with status and optional actual_minutes
   - Returns: Updated task information

4. **POST `/api/v1/coach/tasks/{task_id}/reschedule`**
   - Reschedule a task to a new date
   - Body: `TaskRescheduleRequest` with new_date and optional reason
   - Returns: `TaskRescheduleResponse` with old/new dates

5. **POST `/api/v1/coach/carry-over`**
   - Carry over incomplete tasks from one date to another
   - Parameters: `user_id`, `from_date`, `to_date`, `study_plan_id` (optional)
   - Returns: `CarryOverSummary` with rescheduled tasks

6. **POST `/api/v1/coach/auto-reschedule`**
   - Automatically reschedule overdue tasks
   - Parameters: `user_id`, `target_date` (optional), `study_plan_id` (optional)
   - Returns: Summary of rescheduled tasks

### 3. Pydantic Schemas (`app/schemas/coach.py`)

#### Schemas Created:
- **`DailyBriefingTask`**: Task information for daily briefing
  - Includes overdue status and days overdue
  - Contains all task metadata needed for display

- **`DailyBriefingResponse`**: Complete daily briefing
  - Task counts (total, completed, pending, overdue)
  - Time tracking (estimated vs. actual)
  - Completion percentage
  - List of tasks with details
  - Motivational message
  - Focus skills for the day

- **`TaskUpdateRequest`**: Request to update task status
  - Task ID, new status, optional actual minutes

- **`TaskRescheduleRequest`**: Request to reschedule a task
  - Task ID, new date, optional reason

- **`TaskRescheduleResponse`**: Response after rescheduling
  - Old and new dates, status, confirmation message

- **`CarryOverSummary`**: Summary of carry-over operation
  - List of carried-over tasks
  - Rescheduled tasks information

### 4. Integration

- ✅ Added coach router to main API router (`app/api/v1/router.py`)
- ✅ Exported coach schemas in `app/schemas/__init__.py`
- ✅ Integrated with existing StudyPlan and DailyTask models

## 🎯 Key Features

### 1. **Daily Briefing**
- Comprehensive overview of daily tasks
- Progress tracking with completion percentage
- Overdue task identification
- LLM-generated motivational messages
- Focus skills extraction

### 2. **Task Management**
- Status updates (pending → in_progress → completed)
- Time tracking (estimated vs. actual)
- Completion timestamps
- Task skipping capability

### 3. **Rescheduling**
- Manual task rescheduling with reasons
- Automatic overdue task rescheduling
- Smart distribution across multiple days
- Preserves task relationships

### 4. **Carry-Over Logic**
- Automatic carry-over of incomplete tasks
- Batch processing from one date to another
- Maintains task integrity
- Provides detailed summaries

## 📊 Validation

### Test Script: `backend/scripts/validate_phase6.py`

The validation script tests:
1. ✅ Daily briefing retrieval
2. ✅ Task completion
3. ✅ Task rescheduling
4. ✅ Carry-over functionality
5. ✅ Auto-reschedule overdue tasks

### How to Validate:

```bash
# Ensure backend server is running
cd backend
uvicorn main:app --reload --port 8000

# In another terminal, run validation
python scripts/validate_phase6.py
```

## 🔄 Workflow Example

1. **User starts their day**:
   ```
   GET /api/v1/coach/briefing?user_id=1
   ```
   - Returns daily briefing with tasks, progress, and motivational message

2. **User completes a task**:
   ```
   POST /api/v1/coach/tasks/123/complete?actual_minutes=45
   ```
   - Marks task as completed, records actual time

3. **User needs to reschedule a task**:
   ```
   POST /api/v1/coach/tasks/124/reschedule
   {
     "new_date": "2024-01-15",
     "reason": "Unexpected meeting"
   }
   ```
   - Moves task to new date

4. **End of day - carry over incomplete tasks**:
   ```
   POST /api/v1/coach/carry-over?user_id=1&from_date=2024-01-10&to_date=2024-01-11
   ```
   - Automatically moves incomplete tasks to next day

5. **Auto-reschedule overdue tasks**:
   ```
   POST /api/v1/coach/auto-reschedule?user_id=1
   ```
   - Automatically reschedules all overdue tasks

## 🎨 Motivational Messages

The Daily Coach uses LLM to generate personalized motivational messages based on:
- Number of completed tasks
- Number of pending tasks
- Number of overdue tasks
- Completion percentage
- Focus skills for the day

Messages are:
- Brief (1-2 sentences)
- Positive and encouraging
- Specific to user's progress
- Actionable

## 📝 Next Steps (Phase 7)

Phase 6 provides the foundation for Phase 7: **Practice Generator**, which will:
- Generate quizzes aligned to study plan tasks
- Create flashcards for skill reinforcement
- Generate behavioral interview questions
- Create system design prompts

## 🎯 Key Achievements

1. **Accountability**: Users can track their daily progress
2. **Flexibility**: Tasks can be rescheduled as needed
3. **Automation**: Carry-over and auto-reschedule reduce manual work
4. **Motivation**: LLM-generated messages keep users engaged
5. **Visibility**: Daily briefings provide clear overview of progress

## 🔧 Technical Details

- **Service Layer**: `DailyCoach` class handles all business logic
- **Database**: Uses existing `DailyTask` and `StudyPlan` models
- **LLM Integration**: Uses `get_llm_with_temperature` for motivational messages
- **Date Handling**: Proper timezone-aware datetime handling
- **Error Handling**: Comprehensive error handling with user-friendly messages

---

**Phase 6 Status**: ✅ **COMPLETE**

All deliverables have been implemented and integrated. The Daily Coach Agent is ready for use and provides comprehensive daily execution and accountability features.

