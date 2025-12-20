# Phase 7 Verification Guide

## Quick Verification Steps

### 1. Check Files Exist

Verify these files were created:
- ✅ `backend/app/services/practice_generator.py` - Practice generator service
- ✅ `backend/app/api/v1/endpoints/practice.py` - Updated with Phase 7 endpoints
- ✅ `backend/scripts/validate_phase7.py` - Full validation script
- ✅ `backend/scripts/test_phase7_simple.py` - Simple test script

### 2. Run Simple Test Script

```bash
cd backend
python scripts/test_phase7_simple.py
```

This will:
- Test PracticeGenerator initialization
- Find a task in your database
- Generate a flashcard
- Generate a quiz
- Show existing practice items
- Verify API routes

### 3. Test via API (Backend Server Running)

Start your backend server:
```bash
cd backend
python main.py
```

Then test the endpoints:

#### Generate Practice Items
```bash
# Generate flashcards for task ID 1
curl -X POST "http://localhost:8000/api/v1/practice/items/generate?task_id=1&practice_type=flashcard&count=2"

# Generate quizzes for task ID 1
curl -X POST "http://localhost:8000/api/v1/practice/items/generate?task_id=1&practice_type=quiz&count=1"

# Generate behavioral questions
curl -X POST "http://localhost:8000/api/v1/practice/items/generate?task_id=1&practice_type=behavioral&count=1"

# Generate system design prompts
curl -X POST "http://localhost:8000/api/v1/practice/items/generate?task_id=1&practice_type=system_design&count=1"
```

#### Get Practice Items
```bash
# Get all practice items for a task
curl "http://localhost:8000/api/v1/practice/items/task/1"

# Get specific practice item
curl "http://localhost:8000/api/v1/practice/items/1"
```

#### Submit Practice Attempt
```bash
curl -X POST "http://localhost:8000/api/v1/practice/attempts/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "practice_item_id": 1,
    "user_id": 1,
    "answer": "A",
    "time_spent_seconds": 30
  }'
```

### 4. Check Database

Verify practice items are being created:

```python
from app.db.database import SessionLocal
from app.db.models import PracticeItem

db = SessionLocal()
items = db.query(PracticeItem).all()
print(f"Total practice items: {len(items)}")
for item in items:
    print(f"- {item.practice_type.value}: {item.title}")
db.close()
```

### 5. Verify in Frontend

The practice items should be accessible through:
- Daily Coach page (when integrated)
- Task details (when practice items are linked to tasks)

## What Should Work

✅ **PracticeGenerator Service**
- Can generate quizzes (MCQ and short-answer)
- Can generate flashcards
- Can generate behavioral prompts
- Can generate system design prompts
- Automatically determines difficulty based on skill mastery

✅ **API Endpoints**
- POST `/api/v1/practice/items/generate` - Generate practice items
- GET `/api/v1/practice/items/task/{task_id}` - Get items for task
- GET `/api/v1/practice/items/{item_id}` - Get specific item
- POST `/api/v1/practice/attempts/submit` - Submit attempt
- GET `/api/v1/practice/attempts/{attempt_id}` - Get attempt

✅ **Database Integration**
- Practice items stored in `practice_items` table
- Linked to `daily_tasks` via `task_id`
- Attempts stored in `practice_attempts` table

## Troubleshooting

### "No tasks found"
- You need to upload a resume and job description first
- Generate a study plan
- Then tasks will be available for practice generation

### "LLM API Error"
- Check your `.env` file has correct API keys
- Verify LLM_PROVIDER is set (openai, anthropic, or ollama)
- Check API key is valid

### "Module not found"
- Make sure you're in the backend directory
- Activate your conda environment: `conda activate irc-coach`
- Install dependencies: `pip install -r requirements.txt`

### "Practice items not showing in frontend"
- Phase 7 is backend-only
- Frontend integration happens in later phases
- Use API endpoints or database queries to verify items exist

## Expected Output

When running the test script, you should see:
```
============================================================
Phase 7: Practice Generator - Simple Verification
============================================================

1. Testing PracticeGenerator import and initialization...
   ✓ PracticeGenerator initialized successfully

2. Looking for a task to generate practice items...
   ✓ Found task: [Task Title]
   → Task ID: 1
   → Skills: Python, Machine Learning
   → User ID: 1

3. Testing flashcard generation...
   ✓ Generated flashcard:
      - ID: 1
      - Title: Intermediate Flashcard: Python
      - Question: What is a list comprehension in Python?
      - Difficulty: intermediate
   ✓ Flashcard saved to database

4. Testing quiz generation...
   ✓ Generated 2 quiz item(s)
      - Intermediate Mcq Quiz
      - Intermediate Short Answer Quiz
   ✓ Quiz saved to database

5. Checking existing practice items in database...
   ✓ Found 3 practice item(s) for this task

6. Testing API endpoint structure...
   ✓ Practice API routes available:
      - /items/generate
      - /items/task/{task_id}
      - /items/{item_id}
      - /attempts/submit
      - /attempts/{attempt_id}

============================================================
✓ Phase 7 Verification Complete!
============================================================
```


