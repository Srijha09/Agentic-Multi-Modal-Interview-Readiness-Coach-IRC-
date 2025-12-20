# Phase 7: Practice Generator - Summary

## ✅ Completed Deliverables

### 1. Practice Generator Service (`app/services/practice_generator.py`)

The `PracticeGenerator` class provides comprehensive practice material generation:

#### Core Features:
- **Quiz Generator**: Generates MCQ and short-answer quizzes
  - MCQ quizzes with 4 options and explanations
  - Short-answer quizzes with key points and rubrics
  - Difficulty-aligned questions
  
- **Flashcard Generator**: Creates flashcards for spaced repetition
  - Front (question/prompt) and back (answer/explanation)
  - Tagged with concepts for organization
  - Appropriate for memorization

- **Behavioral Prompt Generator**: Generates STAR-method behavioral questions
  - Role-relevant questions
  - Competency-focused (leadership, problem-solving, teamwork, etc.)
  - Includes STAR guidance (Situation, Task, Action, Result)
  - Evaluation criteria and rubrics

- **System Design Prompt Generator**: Creates system design challenges
  - Requirements and constraints
  - Evaluation framework (functional, non-functional, architecture, trade-offs)
  - Difficulty-appropriate challenges
  - Comprehensive rubrics

#### Key Methods:
- `generate_quiz()`: Generate quiz questions (MCQ or short-answer)
- `generate_flashcard()`: Generate flashcards
- `generate_behavioral_prompt()`: Generate behavioral interview questions
- `generate_system_design_prompt()`: Generate system design challenges
- `generate_for_task()`: Generate practice items for a specific task
- `_determine_difficulty()`: Automatically determine difficulty based on skill mastery

### 2. API Endpoints (`app/api/v1/endpoints/practice.py`)

#### Endpoints Created:
1. **POST `/api/v1/practice/items/generate`**
   - Generate practice items for a task
   - Parameters: `task_id`, `practice_type`, `count`
   - Returns: List of generated practice items

2. **GET `/api/v1/practice/items/task/{task_id}`**
   - Get all practice items for a task
   - Optional filter by `practice_type`
   - Returns: List of practice items

3. **GET `/api/v1/practice/items/{item_id}`**
   - Get a specific practice item by ID
   - Returns: Practice item details

4. **POST `/api/v1/practice/attempts/submit`**
   - Submit a practice attempt (answer to quiz/flashcard/prompt)
   - Parameters: `practice_item_id`, `user_id`, `answer`, `time_spent_seconds`
   - Returns: Practice attempt with ID
   - Note: Evaluation happens in Phase 8

5. **GET `/api/v1/practice/attempts/{attempt_id}`**
   - Get practice attempt by ID
   - Returns: Attempt details including answer and score

### 3. Integration with Existing Systems

- **Task Integration**: Practice items are linked to `DailyTask` records
- **Skill Alignment**: Practice items are tagged with relevant skill names
- **Difficulty Adaptation**: Automatically adjusts difficulty based on `SkillMastery` scores
- **Database Storage**: All practice items stored in `PracticeItem` table
- **Attempt Tracking**: User attempts stored in `PracticeAttempt` table

### 4. Difficulty Determination

The generator automatically determines appropriate difficulty levels:
- **BEGINNER**: Mastery < 0.3
- **INTERMEDIATE**: Mastery 0.3 - 0.6
- **ADVANCED**: Mastery 0.6 - 0.8
- **EXPERT**: Mastery > 0.8

If no mastery data exists, defaults to BEGINNER level.

---

## Technical Implementation

### LLM Prompts

Each practice type has specialized prompts:
- **Quiz Prompt**: Focuses on technical understanding, clear questions, explanations
- **Flashcard Prompt**: Emphasizes conciseness, memorability, spaced repetition
- **Behavioral Prompt**: STAR method guidance, competency testing, evaluation criteria
- **System Design Prompt**: Architectural thinking, scalability, trade-offs

### Error Handling

- JSON parsing with fallback extraction from markdown code blocks
- Graceful degradation if LLM fails
- Logging for debugging
- Database transaction management

### Content Structure

Each practice item includes:
- `practice_type`: Type of practice (quiz, flashcard, behavioral, system_design)
- `title`: Descriptive title
- `question`: The question/prompt
- `skill_names`: Related skills
- `difficulty`: Difficulty level
- `content`: Type-specific content (options, hints, guidance, etc.)
- `expected_answer`: Correct answer (if applicable)
- `rubric`: Evaluation rubric (for Phase 8 evaluation)

---

## Validation

Run validation tests:

```bash
cd backend
python scripts/validate_phase7.py
```

The validation script tests:
- ✅ Module imports
- ✅ PracticeGenerator initialization
- ✅ Quiz generation (MCQ and short-answer)
- ✅ Flashcard generation
- ✅ Behavioral prompt generation
- ✅ System design prompt generation
- ✅ Difficulty determination
- ✅ Task-based generation

---

## Usage Examples

### Generate Quiz for a Task

```python
from app.services.practice_generator import PracticeGenerator
from app.db.models import DailyTask, PracticeTypeEnum

generator = PracticeGenerator()
task = db.query(DailyTask).filter(DailyTask.id == task_id).first()

# Generate 2 flashcards for the task
practice_items = generator.generate_for_task(
    task=task,
    practice_type=PracticeTypeEnum.FLASHCARD,
    user_id=user_id,
    db=db,
    count=2
)
```

### Generate Specific Practice Type

```python
# Generate a behavioral question
behavioral_data = generator.generate_behavioral_prompt(
    skill_names=["Leadership", "Teamwork"],
    difficulty=DifficultyLevelEnum.INTERMEDIATE,
    context="Software engineering role"
)

# Generate a system design challenge
design_data = generator.generate_system_design_prompt(
    skill_names=["System Design", "Scalability"],
    difficulty=DifficultyLevelEnum.ADVANCED,
    context="Backend engineering"
)
```

### API Usage

```bash
# Generate practice items for a task
curl -X POST "http://localhost:8000/api/v1/practice/items/generate?task_id=1&practice_type=quiz&count=2"

# Get practice items for a task
curl "http://localhost:8000/api/v1/practice/items/task/1?practice_type=flashcard"

# Submit an attempt
curl -X POST "http://localhost:8000/api/v1/practice/attempts/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "practice_item_id": 1,
    "user_id": 1,
    "answer": "A",
    "time_spent_seconds": 30
  }'
```

---

## 📝 Next Steps (Phase 8)

Phase 7 provides the foundation for Phase 8: **Evaluation Agent & Rubrics**, which will:
- Evaluate practice attempts using LLM
- Score answers against rubrics
- Generate feedback for users
- Update mastery scores based on performance
- Identify areas needing improvement

---

## Files Created/Modified

### Created Files:
- `backend/app/services/practice_generator.py` - Practice generator service
- `backend/scripts/validate_phase7.py` - Validation script
- `PHASE7_SUMMARY.md` - This summary document

### Modified Files:
- `backend/app/api/v1/endpoints/practice.py` - Updated endpoints
- `backend/app/services/__init__.py` - Added PracticeGenerator export

---

## Notes

- Practice items are generated on-demand when requested
- Difficulty is automatically determined based on user's skill mastery
- All practice types include comprehensive rubrics for evaluation (Phase 8)
- Practice attempts are stored but not evaluated until Phase 8
- The generator uses temperature=0.8 for creative question generation
- JSON responses are parsed with fallback for markdown code blocks

---

**Phase 7 Status**: ✅ **COMPLETE**


