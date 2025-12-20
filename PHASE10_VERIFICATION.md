# Phase 10: Adaptive Planning - Frontend Verification Guide

## How to Verify Phase 10 Works in the Frontend

### Prerequisites
1. ✅ You have a study plan created (upload resume + job description)
2. ✅ You have submitted at least 2-3 practice attempts (quizzes/flashcards)
3. ✅ Some skills have mastery scores (from Phase 9)

---

## Step-by-Step Verification

### Step 1: Navigate to Dashboard
1. Open your browser and go to the Dashboard page
2. URL: `http://localhost:5173/dashboard` (or your frontend URL)

### Step 2: Check for Adaptive Recommendations Section
Look for a section titled **"🔄 Adaptive Plan Recommendations"** on the Dashboard page.

**Expected Location:**
- Below the "Skill Mastery Overview" section
- Above the "Today's Tasks" section

### Step 3: What You Should See

#### If You Have Weak Skills (Mastery < 0.5):
You should see:
- **Red/Yellow/Blue boxes** with recommendations
- Each recommendation shows:
  - **Action**: "Add 2 reinforcement practice tasks"
  - **Skill**: Name of the weak skill (e.g., "TensorFlow")
  - **Reason**: Why it needs reinforcement (e.g., "low mastery, declining performance")
  - **Priority badge**: high/medium/low
- **"Apply Recommendations" button** (enabled)

#### If You Have Strong Skills (Mastery >= 0.8):
You should see:
- Recommendations to reduce repetition
- **Action**: "Reduce X redundant tasks"
- **Skill name** and reason

#### If No Adaptations Needed:
You should see:
- Message: "No adaptations needed. Your plan is well-balanced!"
- **"Apply Recommendations" button** (disabled)

### Step 4: Check the Stats
At the bottom of the Adaptive Recommendations section, you should see:
- **Weak Skills**: Count of skills needing reinforcement
- **Strong Skills**: Count of skills that are strong

### Step 5: Apply Recommendations (If Available)
1. Click the **"Apply Recommendations"** button
2. You should see:
   - Button text changes to "Applying..."
   - Success alert: "Plan adapted successfully! Added X reinforcement tasks."
   - Dashboard refreshes automatically
   - New reinforcement tasks appear in your study plan

### Step 6: Verify Tasks Were Added
1. Scroll down to see your study plan weeks
2. Look for new tasks with titles like:
   - "Reinforcement Practice: [Skill Name]"
3. These tasks should have:
   - Type: Practice
   - Estimated time: 30 minutes
   - Skill name in the task
   - Content with "adaptive_note" indicating they were added by adaptive planner

---

## Troubleshooting

### Issue: Adaptive Recommendations Section Not Showing

**Possible Causes:**
1. No study plan exists
   - **Fix**: Upload resume and job description to create a plan
2. No mastery data yet
   - **Fix**: Submit some practice attempts first (quizzes/flashcards)
3. API error
   - **Fix**: Check browser console (F12) for errors
   - Check backend logs for API errors

**Check Browser Console:**
```javascript
// Open DevTools (F12) and check Console tab
// Look for errors like:
// - "Could not fetch adaptation analysis"
// - Network errors (404, 500, etc.)
```

### Issue: "No adaptations needed" But You Expect Recommendations

**Possible Causes:**
1. All skills have mastery >= 0.5 (not weak enough)
2. Skills haven't been practiced enough (< 3 attempts)
3. No declining trends detected

**To Test:**
1. Submit practice attempts with low scores
2. Wait for mastery to update
3. Refresh Dashboard

### Issue: Button Doesn't Work

**Check:**
1. Is the button disabled? (grayed out)
   - It's disabled if there are no recommendations
2. Check browser console for JavaScript errors
3. Check network tab in DevTools to see if API call is made

---

## Manual API Testing (Alternative Verification)

If frontend doesn't show recommendations, test the API directly:

### 1. Analyze Adaptation Needs
```bash
curl "http://localhost:8000/api/v1/adaptive/analyze?user_id=1&study_plan_id=1"
```

**Expected Response:**
```json
{
  "study_plan_id": 1,
  "analysis": {
    "weak_skills": [...],
    "strong_skills": [...],
    "recommendations": [...],
    "total_weak": 1,
    "total_strong": 0
  },
  "recommendations_count": 1
}
```

### 2. Apply Adaptations
```bash
curl -X POST "http://localhost:8000/api/v1/adaptive/adapt?user_id=1&study_plan_id=1&apply_recommendations=true"
```

**Expected Response:**
```json
{
  "study_plan_id": 1,
  "success": true,
  "summary": {
    "reinforcement_tasks_added": 2,
    "tasks_marked_optional": 0
  },
  "changes": [...],
  "analysis": {...}
}
```

---

## Visual Checklist

✅ **Section appears on Dashboard**
- Title: "🔄 Adaptive Plan Recommendations"
- Located between Mastery Stats and Today's Tasks

✅ **Recommendations display correctly**
- Color-coded boxes (red/yellow/blue based on priority)
- Shows skill name, action, and reason
- Priority badge visible

✅ **Stats display**
- Weak Skills count
- Strong Skills count

✅ **Button works**
- "Apply Recommendations" button is clickable (when recommendations exist)
- Shows "Applying..." during submission
- Success message appears
- Dashboard refreshes

✅ **Tasks added**
- New reinforcement tasks appear in study plan
- Tasks have correct skill names
- Tasks are scheduled appropriately

---

## Quick Test Scenario

To quickly test Phase 10:

1. **Create a study plan** (if you don't have one)
2. **Submit 2-3 practice attempts** with low scores (to create weak skills)
3. **Go to Dashboard**
4. **Look for Adaptive Recommendations section**
5. **Click "Apply Recommendations"**
6. **Verify new tasks appear**

---

## Success Criteria

Phase 10 is working correctly if:
- ✅ Adaptive Recommendations section appears on Dashboard
- ✅ Recommendations are shown for weak/strong skills
- ✅ "Apply Recommendations" button works
- ✅ New reinforcement tasks are added to the plan
- ✅ Tasks are properly scheduled and have correct skill associations
- ✅ Plan diff is logged (check `plan_data.adaptation_history` in database)

---

**If all checks pass, Phase 10 is working correctly!** 🎉

