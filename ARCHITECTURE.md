# Architecture Documentation

## System Architecture Overview

The Interview Readiness Coach is built as a **multi-agent system** using LangChain/LangGraph for orchestration, with a FastAPI backend and React frontend.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React)                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │  Upload │  │Dashboard │  │  Coach   │  │  Home    │     │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘     │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTP/REST
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Backend API (FastAPI)                          │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │ Documents  │  │   Plans    │  │  Practice   │           │
│  └────────────┘  └────────────┘  └────────────┘           │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │    Gaps    │  │   Coach    │  │  Adaptive  │           │
│  └────────────┘  └────────────┘  └────────────┘           │
│  ┌────────────┐  ┌────────────┐                            │
│  │  Mastery   │  │  Calendar  │                            │
│  └────────────┘  └────────────┘                            │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Service Calls
                            ▼
┌─────────────────────────────────────────────────────────────┐
│            Agent Services (LangChain)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │Skill Extract │  │ Gap Analysis │  │   Planner    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │Practice Gen  │  │ Evaluator    │  │Mastery Track │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │Adaptive Plan │  │Calendar Svc  │                        │
│  └──────────────┘  └──────────────┘                        │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ LLM Calls
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              LLM Providers                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │  OpenAI  │  │Anthropic │  │  Ollama  │                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Data Access
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Data Layer                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │Database  │  │  Vector   │  │   File   │                  │
│  │(SQLite/ │  │   Store   │  │  Storage │                  │
│  │Postgres)│  │(FAISS/    │  │          │                  │
│  │         │  │Chroma)    │  │          │                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Architecture

### Frontend Layer

**Technology:** React 18 + Vite + Tailwind CSS

**Components:**
- `Home.jsx` - Landing page
- `Upload.jsx` - Document upload interface
- `Dashboard.jsx` - Main dashboard with plan overview
- `DailyCoach.jsx` - Daily tasks and practice interface
- `ErrorBoundary.jsx` - Error handling component

**State Management:**
- React hooks (useState, useEffect, useMemo)
- Axios for API calls
- Local state (no global state management)

**Key Features:**
- Responsive design
- Real-time updates
- Error boundaries
- Loading states

### Backend API Layer

**Technology:** FastAPI + Uvicorn

**API Structure:**
```
/api/v1/
├── /health          - Health checks
├── /documents       - Document upload/management
├── /gaps            - Gap analysis
├── /plans           - Study plan management
├── /coach           - Daily coaching
├── /practice        - Practice items and attempts
├── /mastery         - Mastery tracking
├── /adaptive        - Adaptive planning
├── /calendar        - Calendar export
└── /observability   - System metrics
```

**Key Features:**
- RESTful API design
- Pydantic validation
- SQLAlchemy ORM
- CORS enabled
- Automatic API documentation (Swagger)

### Agent Services Layer

**Technology:** LangChain + LangGraph

**Services:**
1. **SkillExtractor** - Extracts skills from documents
2. **GapAnalyzer** - Identifies skill gaps
3. **StudyPlanner** - Generates study plans
4. **PracticeGenerator** - Creates practice items
5. **EvaluationAgent** - Evaluates practice attempts
6. **MasteryTracker** - Tracks skill mastery
7. **AdaptivePlanner** - Adapts plans based on mastery
8. **CalendarService** - Generates calendar events

**LLM Integration:**
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- Ollama (local LLMs)

### Data Layer

**Database (SQLite/PostgreSQL):**
- User management
- Study plans and tasks
- Practice items and attempts
- Evaluations and mastery
- Calendar events

**Vector Store (FAISS/Chroma):**
- Document embeddings
- Skill similarity search
- (Currently configured but not fully utilized)

**File Storage:**
- Uploaded documents (PDF, DOCX)
- User-specific directories

---

## Data Flow

### 1. Document Upload Flow

```
User → Frontend → API → Document Parser → Database
                              │
                              ▼
                         File Storage
```

### 2. Gap Analysis Flow

```
User → API → SkillExtractor → LLM → Skills
                              │
                              ▼
                         GapAnalyzer → LLM → Gaps → Database
```

### 3. Plan Generation Flow

```
User → API → StudyPlanner → LLM → Plan Structure
                              │
                              ▼
                         Database (Weeks, Days, Tasks)
```

### 4. Practice Flow

```
User → API → PracticeGenerator → LLM → Practice Item
                              │
                              ▼
                         User Submits → EvaluationAgent → LLM
                              │
                              ▼
                         MasteryTracker → Database
```

### 5. Adaptive Planning Flow

```
Mastery Data → AdaptivePlanner → Analysis
                              │
                              ▼
                         Add/Modify Tasks → Database
```

---

## Database Schema

### Core Models

**User**
- id, email, full_name, created_at

**StudyPlan**
- id, user_id, weeks, hours_per_week, interview_date, plan_data

**Week**
- id, study_plan_id, week_number, theme, estimated_hours

**Day**
- id, week_id, day_number, date, theme, estimated_hours

**DailyTask**
- id, study_plan_id, day_id, task_date, task_type, status
- title, description, skill_names, estimated_minutes
- content (JSON), completed, completed_at

**PracticeItem**
- id, task_id, practice_type, title, question
- expected_answer, skill_names, difficulty, content (JSON)

**PracticeAttempt**
- id, user_id, practice_item_id, task_id
- answer, time_spent_seconds, score, feedback

**Evaluation**
- id, practice_attempt_id, rubric_id
- overall_score, criterion_scores (JSON)
- strengths, weaknesses, feedback

**SkillMastery**
- id, user_id, skill_name
- mastery_score, last_practiced, practice_count
- improvement_trend

**CalendarEvent**
- id, study_plan_id, task_id
- title, description, start_time, end_time
- ics_uid, synced

---

## API Design Patterns

### RESTful Endpoints

**Resources:**
- `/documents` - Document resource
- `/gaps` - Gap resource
- `/plans` - Study plan resource
- `/practice` - Practice resource
- `/mastery` - Mastery resource

**Actions:**
- GET - Retrieve
- POST - Create
- PUT/PATCH - Update
- DELETE - Remove

### Error Handling

**Standard Error Response:**
```json
{
  "detail": "Error message",
  "status_code": 400
}
```

**Error Codes:**
- 400 - Bad Request
- 404 - Not Found
- 500 - Internal Server Error

---

## Security Architecture

### Current Security Measures:
- CORS configuration
- Input validation (Pydantic)
- SQL injection prevention (SQLAlchemy ORM)
- File type validation

### Future Security:
- JWT authentication
- Rate limiting
- API key management
- File scanning
- Input sanitization

---

## Observability Architecture

### Logging
- Python logging module
- Structured logging
- Error tracking

### Tracing
- LangSmith integration
- LLM call tracing
- Performance monitoring

### Metrics
- System health endpoints
- Performance metrics
- User activity tracking

---

## Deployment Architecture

### Development
```
Frontend (Vite Dev Server) → Backend (Uvicorn) → SQLite
```

### Production (Recommended)
```
Frontend (Nginx) → Backend (Uvicorn/Gunicorn) → PostgreSQL
                              │
                              ▼
                         Redis (Caching)
                              │
                              ▼
                         LangSmith (Tracing)
```

---

## Scalability Considerations

### Current Limitations:
- Single server deployment
- Synchronous processing
- No caching layer

### Future Scalability:
- Microservices architecture
- Background job queue
- Redis caching
- Load balancing
- CDN for static assets

---

## Technology Decisions

### Why FastAPI?
- Fast performance
- Automatic API docs
- Type validation
- Async support

### Why React?
- Component reusability
- Large ecosystem
- Good performance
- Easy to maintain

### Why LangChain?
- LLM abstraction
- Prompt management
- Chain composition
- LangSmith integration

### Why SQLite/PostgreSQL?
- SQLAlchemy abstraction
- Easy development (SQLite)
- Production ready (PostgreSQL)
- Good performance

---

## Development Workflow

### Backend Development:
1. Make changes to services/models
2. Test with API docs (Swagger)
3. Run integration tests
4. Check LangSmith traces

### Frontend Development:
1. Make changes to components
2. Hot reload in browser
3. Test user flows
4. Check browser console

### Testing:
1. Unit tests (services)
2. Integration tests (end-to-end)
3. Manual testing (UI)
4. Performance benchmarks

---

## File Structure

```
backend/
├── app/
│   ├── api/v1/endpoints/    # API endpoints
│   ├── core/                # Configuration, LLM
│   ├── db/                   # Database models
│   ├── schemas/              # Pydantic schemas
│   └── services/             # Business logic
├── tests/                    # Integration tests
└── scripts/                  # Utility scripts

frontend/
├── src/
│   ├── pages/                # Page components
│   ├── components/           # Reusable components
│   └── App.jsx               # Main app
└── public/                   # Static assets
```

---

## Phase Implementation Summary

**Phase 1-3:** Infrastructure & Data Models
**Phase 4-5:** Core Agents (Gap Analysis, Planning)
**Phase 6:** Daily Coaching
**Phase 7-9:** Practice & Evaluation Loop
**Phase 10:** Adaptive Planning
**Phase 11:** Calendar Integration
**Phase 12:** Observability & Testing
**Phase 13:** Documentation (This phase)

---

**Last Updated:** Phase 13
**Architecture Version:** 1.0

