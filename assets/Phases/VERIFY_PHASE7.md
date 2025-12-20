# How to Verify Phase 7 is Complete

## ✅ Quick Checklist

### Step 1: Verify Files Exist

Check these files are in your project:

1. **Practice Generator Service**
   - File: `backend/app/services/practice_generator.py`
   - Should be ~520 lines
   - Contains `class PracticeGenerator` with methods:
     - `generate_quiz()`
     - `generate_flashcard()`
     - `generate_behavioral_prompt()`
     - `generate_system_design_prompt()`
     - `generate_for_task()`

2. **Updated Practice Endpoints**
   - File: `backend/app/api/v1/endpoints/practice.py`
   - Should have 5 endpoints:
     - `POST /items/generate`
     - `GET /items/task/{task_id}`
     - `GET /items/{item_id}`
     - `POST /attempts/submit`
     - `GET /attempts/{attempt_id}`

3. **Services Init**
   - File: `backend/app/services/__init__.py`
   - Should import `PracticeGenerator`

### Step 2: Manual Code Verification

Open `backend/app/services/practice_generator.py` and verify:

```python
# Line ~24: Class definition
class PracticeGenerator:
    """Service for generating practice materials..."""
    
# Line ~203: Quiz generator
def generate_quiz(self, ...):
    
# Line ~258: Flashcard generator  
def generate_flashcard(self, ...):
    
# Line ~308: Behavioral prompt generator
def generate_behavioral_prompt(self, ...):
    
# Line ~359: System design generator
def generate_system_design_prompt(self, ...):
    
# Line ~410: Task-based generator
def generate_for_task(self, ...):
```

### Step 3: Test with Python (Activate Environment First)

**Important:** Activate your conda environment first:
```bash
conda activate irc-coach
```

Then run:
```bash
python backend/scripts/test_phase7_simple.py
```

### Step 4: Test via API (If Backend is Running)

If your backend server is running on `http://localhost:8000`:

1. **Find a task ID** (from your database or study plan)
2. **Generate practice items:**
   ```
   POST http://localhost:8000/api/v1/practice/items/generate?task_id=1&practice_type=quiz&count=1
   ```
3. **Check generated items:**
   ```
   GET http://localhost:8000/api/v1/practice/items/task/1
   ```

### Step 5: Check API Documentation

Visit: `http://localhost:8000/docs`

Look for the `/api/v1/practice` section. You should see:
- `POST /api/v1/practice/items/generate`
- `GET /api/v1/practice/items/task/{task_id}`
- `GET /api/v1/practice/items/{item_id}`
- `POST /api/v1/practice/attempts/submit`
- `GET /api/v1/practice/attempts/{attempt_id}`

## What Phase 7 Does

Phase 7 creates a **Practice Generator** that:

1. **Generates Quizzes**
   - Multiple choice questions (MCQ) with 4 options
   - Short-answer questions with rubrics
   - Automatically adjusts difficulty

2. **Generates Flashcards**
   - Front (question) and back (answer)
   - For spaced repetition learning
   - Tagged with concepts

3. **Generates Behavioral Questions**
   - STAR-method interview questions
   - Competency-focused (leadership, teamwork, etc.)
   - Includes evaluation rubrics

4. **Generates System Design Prompts**
   - Architecture challenges
   - Requirements and constraints
   - Evaluation frameworks

## Visual Verification

### In Code Editor:
- Open `backend/app/services/practice_generator.py`
- You should see ~520 lines of code
- Search for "def generate" - should find 5 methods

### In API Docs:
- Start backend: `python backend/main.py`
- Visit: `http://localhost:8000/docs`
- Expand `/api/v1/practice` section
- Should see 5 endpoints listed

### In Database (if you have tasks):
```python
from app.db.database import SessionLocal
from app.db.models import PracticeItem

db = SessionLocal()
count = db.query(PracticeItem).count()
print(f"Practice items in database: {count}")
db.close()
```

## Common Issues

### "File not found"
- Make sure you're in the project root directory
- Check file paths are correct

### "Module not found" when running test
- Activate conda environment: `conda activate irc-coach`
- Make sure you're in the backend directory

### "No tasks found"
- Phase 7 needs tasks to generate practice for
- First: Upload resume + job description
- Second: Generate study plan (creates tasks)
- Then: Phase 7 can generate practice items for those tasks

### "API endpoint not found"
- Make sure backend server is running
- Check router includes practice endpoints (should be in `backend/app/api/v1/router.py`)

## Summary

**Phase 7 is complete if:**
- ✅ `practice_generator.py` file exists (~520 lines)
- ✅ `practice.py` endpoints file is updated
- ✅ `__init__.py` exports PracticeGenerator
- ✅ API endpoints are accessible at `/api/v1/practice/*`
- ✅ Can generate practice items for tasks (when tasks exist)

**Note:** Phase 7 is a **backend service**. You won't see it in the frontend UI yet - that integration happens in later phases. The practice generator creates items that can be used by:
- Phase 8: Evaluation Agent (to evaluate attempts)
- Phase 9: Progress Tracking (to track mastery)
- Frontend: When practice UI is added


