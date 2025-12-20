# Demo Script - Interview Readiness Coach

## Quick Demo Flow (5-10 minutes)

### Step 1: Setup (1 minute)
1. **Start Backend:**
   ```bash
   make backend
   # Or: cd backend && uvicorn main:app --reload --port 8000
   ```

2. **Start Frontend:**
   ```bash
   make frontend
   # Or: cd frontend && npm run dev
   ```

3. **Verify:**
   - Backend: http://localhost:8000/docs (API docs should load)
   - Frontend: http://localhost:5173 (app should load)

### Step 2: Upload Resume & Job Description (2 minutes)

1. **Navigate to Upload Page:**
   - Click "Upload" in navigation
   - Or go to: http://localhost:5173/upload

2. **Upload Resume:**
   - Click "Choose File" for Resume
   - Select a PDF or DOCX resume file
   - Wait for upload confirmation

3. **Upload Job Description:**
   - Paste job description text OR upload a PDF
   - Click "Upload Documents"
   - Wait for processing

**Expected Result:** 
- Success message: "Documents uploaded successfully"
- Documents are processed and stored

### Step 3: View Gap Analysis (1 minute)

1. **Navigate to Dashboard:**
   - Click "Dashboard" in navigation
   - Or go to: http://localhost:5173/dashboard

2. **View Gap Report:**
   - Click "View Gap Analysis" or navigate to gap report
   - Review identified skill gaps
   - See prioritized gaps (Critical, High, Medium, Low)

**Expected Result:**
- Gap report shows skills from JD not in resume
- Gaps are prioritized and have evidence

### Step 4: Generate Study Plan (2 minutes)

1. **Generate Plan:**
   - From Dashboard or Gap Report page
   - Click "Generate Study Plan"
   - Enter:
     - Interview date (e.g., 6 weeks from now)
     - Hours per week (e.g., 10)
   - Click "Generate"

2. **View Plan:**
   - Plan appears on Dashboard
   - Shows weeks, days, and tasks
   - Tasks have study materials and resources

**Expected Result:**
- Multi-week study plan generated
- Tasks organized by week and day
- Each task has content, resources, and time estimates

### Step 5: Daily Coach & Practice (3 minutes)

1. **Navigate to Daily Coach:**
   - Click "Daily Coach" in navigation
   - Or go to: http://localhost:5173/coach

2. **View Today's Tasks:**
   - See tasks for today
   - Tasks organized by status (Overdue, Pending, In Progress, Completed)

3. **Generate Practice Items:**
   - Click "View Study Materials" on a task
   - Click "Generate Practice" → Select type (Quiz, Flashcard, etc.)
   - Wait for generation

4. **Take Practice:**
   - Click on generated practice item
   - For Quiz: Select answer and submit
   - For Flashcard: Review and mark Correct/Incorrect
   - View evaluation results

**Expected Result:**
- Practice items generated successfully
- Can submit answers
- Evaluation shows score, feedback, strengths, weaknesses
- Correct/incorrect answer displayed for quizzes

### Step 6: View Progress & Mastery (1 minute)

1. **Check Mastery Stats:**
   - Go to Dashboard
   - Scroll to "Skill Mastery Overview"
   - See average mastery, skill levels, trends

2. **Check Adaptive Recommendations:**
   - Scroll to "Adaptive Plan Recommendations"
   - See recommendations for weak/strong skills
   - Click "Apply Recommendations" (if available)

**Expected Result:**
- Mastery stats displayed
- Adaptive recommendations shown
- Can apply recommendations to update plan

### Step 7: Export Calendar (1 minute)

1. **Export Calendar:**
   - On Dashboard, click "📅 Export Calendar"
   - Wait for generation
   - ICS file downloads automatically

2. **Import to Calendar:**
   - Open downloaded .ics file
   - Import into Google Calendar, Outlook, or Apple Calendar
   - Verify events appear

**Expected Result:**
- ICS file downloads
- Can be imported into calendar apps
- Events show study tasks with times

---

## Extended Demo Flow (15-20 minutes)

### Additional Steps:

1. **Complete Multiple Tasks:**
   - Mark several tasks as completed
   - See progress update

2. **Submit Multiple Practice Attempts:**
   - Generate and submit 3-4 practice items
   - Watch mastery scores update
   - See adaptive recommendations change

3. **Apply Adaptive Planning:**
   - After submitting low-scoring attempts
   - Check adaptive recommendations
   - Apply recommendations
   - Verify new reinforcement tasks appear

4. **View System Metrics:**
   - Check "System Metrics" section on Dashboard
   - View performance over last 7 days
   - See LangSmith tracing status (if enabled)

5. **Test Calendar Regeneration:**
   - After applying adaptive changes
   - Export calendar again
   - Verify new tasks appear in calendar

---

## Demo Talking Points

### Key Features to Highlight:

1. **Intelligent Gap Analysis:**
   - "The system automatically identifies what skills you need to learn"
   - "Gaps are prioritized based on importance and evidence"

2. **Personalized Planning:**
   - "The plan adapts to your interview date and time availability"
   - "Tasks are broken down into daily, actionable items"

3. **Adaptive Learning:**
   - "The system tracks your mastery and adjusts the plan"
   - "Weak skills get reinforcement, strong skills reduce repetition"

4. **Comprehensive Practice:**
   - "Multiple practice types: quizzes, flashcards, behavioral questions"
   - "AI-powered evaluation with detailed feedback"

5. **Real-World Integration:**
   - "Export to your calendar for accountability"
   - "Track progress and see improvement over time"

---

## Troubleshooting During Demo

### If Something Doesn't Work:

1. **Backend Not Starting:**
   - Check conda environment is activated
   - Verify API keys are set in .env
   - Check port 8000 is not in use

2. **Frontend Not Loading:**
   - Check Node.js is installed
   - Run `npm install` in frontend directory
   - Check port 5173 is not in use

3. **No Study Plan:**
   - Ensure documents are uploaded first
   - Check gap analysis completed
   - Verify user_id is correct (default: 1)

4. **Practice Items Not Generating:**
   - Check LLM API key is set
   - Verify backend logs for errors
   - Check task has skill names

5. **Calendar Export Fails:**
   - Ensure study plan exists
   - Check tasks have dates
   - Verify calendar events were generated

---

## Demo Checklist

Before starting demo:
- [ ] Backend server running (port 8000)
- [ ] Frontend server running (port 5173)
- [ ] Test user created (user_id = 1)
- [ ] LLM API key configured
- [ ] Sample resume and JD ready
- [ ] Browser ready with both tabs open

During demo:
- [ ] Upload documents successfully
- [ ] View gap analysis
- [ ] Generate study plan
- [ ] View daily tasks
- [ ] Generate practice items
- [ ] Submit practice attempts
- [ ] View evaluation results
- [ ] Check mastery stats
- [ ] View adaptive recommendations
- [ ] Export calendar

After demo:
- [ ] Show system metrics
- [ ] Explain architecture
- [ ] Discuss future improvements

---

## Quick Demo (2-minute version)

For a very quick demo:

1. **Upload Resume + JD** (30 seconds)
2. **Generate Plan** (30 seconds)
3. **Generate & Submit Practice** (30 seconds)
4. **Show Results** (30 seconds)

Focus on:
- Automatic gap identification
- Personalized plan generation
- AI-powered practice and evaluation
- Adaptive learning loop

---

## Demo Success Criteria

✅ **All core features work:**
- Document upload
- Gap analysis
- Plan generation
- Practice generation
- Evaluation
- Mastery tracking
- Calendar export

✅ **No manual fixes needed:**
- System works out of the box
- No database errors
- No API errors
- Frontend loads correctly

✅ **Smooth user experience:**
- Fast response times
- Clear UI feedback
- Helpful error messages
- Intuitive navigation

