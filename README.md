# Agentic Multi Modal Interview Readiness Coach

## Project Overview

An intelligent, agentic interview preparation system that analyzes a user’s resume and target job description to identify skill gaps, generate a personalized multi-week study plan, deliver daily practice (quizzes, flashcards, challenges), evaluate responses, and adapt the plan over time based on performance and consistency.

The system functions as a **stateful AI coach**, combining planning, evaluation, memory, and adaptation into a unified experience. It integrates real-world constraints such as time availability, interview deadlines, and forgetting curves, and supports calendar-based accountability.

---

## Key Features

- **Multi-Modal Intake**
  - Resume upload (PDF/DOCX)
  - Job description input (text or PDF)
  - Optional preferences (time/day, weak areas, interview date)

- **Skill Gap Analysis**
  - Extracts required skills from job description
  - Extracts demonstrated skills from resume
  - Produces evidence-backed gap reports with priority scoring

- **Agentic Planning**
  - Multi-week, constraint-aware study plan
  - Daily task decomposition (learn → practice → review)
  - Explicit reasoning for why each task is scheduled

- **Daily Practice Engine**
  - Quizzes (MCQ, short-answer)
  - Flashcards (spaced repetition)
  - Behavioral interview prompts (STAR-based)
  - System design prompts with evaluation rubrics

- **Evaluation & Feedback**
  - LLM-based rubric scoring
  - Weakness identification
  - Actionable improvement feedback

- **Progress Tracking & Adaptation**
  - Mastery scores per skill
  - Automatic plan adjustment based on performance
  - Streaks, completion tracking, and reinforcement scheduling

- **Calendar Integration**
  - ICS calendar export for daily study reminders
  - Regeneration when plans adapt

---

## Technology Stack

| Component | Technology |
|--------|------------|
| Agent Orchestration | LangGraph |
| Agent Framework | LangChain |
| LLM | OpenAI / Anthropic / Ollama |
| Backend API | FastAPI |
| Frontend | React + Vite + Tailwind CSS |
| Persistence | PostgreSQL / SQLite |
| Vector Search | FAISS / Chroma |
| Observability | LangSmith |
| Calendar | ICS export (Google Calendar V2) |

---

### Architecture Diagram
```mermaid
flowchart TB
  %% ==== UI Layer ====
  subgraph UI["Web Frontend (React)"]
    U1["Upload Resume / JD"]
    U2["Gap Report Dashboard"]
    U3["Daily Tasks + Practice"]
    U4["Progress & Mastery"]
    U5["Calendar Export"]
  end

  %% ==== API Layer ====
  subgraph API["Backend (FastAPI)"]
    A1["Auth + User Profile"]
    A2["Document Service"]
    A3["Planning Service"]
    A4["Practice Service"]
    A5["Evaluation Service"]
    A6["Adaptation Service"]
    A7["Calendar Service"]
  end

  %% ==== Agentic Layer ====
  subgraph AG["LangGraph Agent System"]
    G1["Intake Agent"]
    G2["Gap Analysis Agent"]
    G3["Planner Agent"]
    G4["Daily Coach Agent"]
    G5["Practice Generator"]
    G6["Evaluation Agent"]
    G7["Mastery Tracker"]
    G8["Adaptive Planning Agent"]
  end

  %% ==== Data Layer ====
  subgraph DATA["Data Layer"]
    DB[(PostgreSQL / SQLite)]
    VS[(Vector Store: FAISS/Chroma)]
    FS[(File Storage: /storage or S3)]
  end

  %% ==== Connections ====
  UI -->|HTTPS| API

  A1 --> DB
  A2 --> FS
  A2 --> DB
  A3 --> DB
  A4 --> DB
  A5 --> DB
  A6 --> DB
  A7 --> DB

  API -->|invoke graph| AG

  G1 --> G2 --> G3 --> G4
  G4 --> G5 --> G6 --> G7 --> G8 --> G3

  G2 --> VS
  VS --> G2

  A2 -->|store embeddings| VS

```

### Sequence Diagram: Resume + JD → Plan → Daily Practice → Adaptation Loop

```mermaid
sequenceDiagram
  autonumber
  participant User
  participant UI as Web UI
  participant API as FastAPI
  participant Parse as Parser/Extractor
  participant Graph as LangGraph Agents
  participant DB as DB
  participant VS as Vector Store
  participant Cal as Calendar Service

  User->>UI: Upload Resume + Paste/Upload JD
  UI->>API: POST /upload (files + metadata)
  API->>Parse: Extract text + sections + chunks
  Parse-->>API: Parsed content (structured)
  API->>DB: Save Document + Chunks metadata
  API->>VS: Create embeddings + store vectors
  VS-->>API: Vector IDs stored

  UI->>API: POST /gap/analyze
  API->>Graph: Run Gap Analysis Agent
  Graph->>DB: Fetch documents + user prefs
  Graph->>VS: Retrieve similar skills/requirements
  Graph-->>API: Gap Report (skills + evidence + priority)
  API-->>UI: Return gap report

  UI->>API: POST /plan/generate (time/day, deadline)
  API->>Graph: Run Planner Agent
  Graph->>DB: Save Plan (weeks/days/tasks)
  Graph-->>API: Plan ID + summary
  API-->>UI: Show plan

  User->>UI: Open Today's Tasks
  UI->>API: GET /daily/{date}
  API->>Graph: Run Daily Coach Agent
  Graph->>DB: Load plan + mastery + history
  Graph-->>API: Today's tasks + practice items
  API-->>UI: Render tasks

  User->>UI: Submit quiz/answers
  UI->>API: POST /attempts/submit
  API->>Graph: Run Evaluation Agent
  Graph->>DB: Save attempt + evaluation
  Graph->>DB: Update mastery scores
  Graph->>DB: Log recommendations
  Graph-->>API: Feedback + updated mastery
  API-->>UI: Display score + what to improve

  API->>Graph: Run Adaptive Planning Agent (if needed)
  Graph->>DB: Modify future tasks (reinforce/advance)
  Graph-->>API: Plan change log

  User->>UI: Export calendar
  UI->>API: GET /calendar/ics?days=14
  API->>Cal: Generate ICS from latest plan
  Cal-->>API: ICS file
  API-->>UI: Download ICS
```

### Use Case Diagram

```mermaid
flowchart LR
  %% Actors
  User((User))
  Admin((Admin/Developer))

  %% System boundary
  subgraph SYS["Interview Readiness Coach System"]
    UC1["Upload Resume & Job Description"]
    UC2["Set Target Role + Time Budget"]
    UC3["View Skill Gap Report"]
    UC4["Generate Multi-Week Plan"]
    UC5["View Daily Tasks"]
    UC6["Take Quiz / Flashcards / Prompts"]
    UC7["Submit Answers"]
    UC8["Receive Feedback & Scores"]
    UC9["Track Mastery & Progress"]
    UC10["Adapt Future Schedule"]
    UC11["Export Calendar (ICS)"]
    UC12["Manage Skill Taxonomy & Rubrics"]
    UC13["System Monitoring & Logs"]
  end

  %% Relationships
  User --> UC1
  User --> UC2
  User --> UC3
  User --> UC4
  User --> UC5
  User --> UC6
  User --> UC7
  User --> UC8
  User --> UC9
  User --> UC10
  User --> UC11

  Admin --> UC12
  Admin --> UC13
```

### Data Flow Diagram
#### DFD Level 0 (Context Diagram)

```mermaid
flowchart LR
  User((User)) -->|Resume/JD, preferences, answers| System["Interview Readiness Coach"]
  System -->|Gap report, plan, daily tasks, feedback, calendar| User

  System -->|Read/Write| DB[(Database)]
  System -->|Store/Retrieve embeddings| VS[(Vector Store)]
  System -->|Store raw files| FS[(File Storage)]
```



## Core Capabilities

### 1. Skill Extraction & Evidence Mapping
- Resume skill inference with evidence snippets
- Job description requirement extraction
- Coverage scoring: Covered / Partial / Missing

### 2. Planning Under Constraints
- Time-budget aware scheduling
- Interview deadline alignment
- Priority-based topic ordering

### 3. Practice Generation
- Difficulty-controlled quizzes
- Behavioral question generation aligned to role level
- System design prompts with structured expectations

### 4. Evaluation & Feedback
- Rubric-based LLM evaluation
- Confidence and clarity scoring
- Identification of misconceptions

### 5. Adaptive Learning Loop
- Mastery tracking per skill
- Automatic reinforcement scheduling
- Reduction of repetition for mastered topics

---

## Quick Start

### Prerequisites
- **Conda** (Miniconda or Anaconda)
- **Node.js** 18+ (installed via conda)
- **Python** 3.11 (installed via conda)
- **LLM API Key** (OpenAI, Anthropic, or Ollama)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd Agentic-Multi-Modal-Interview-Readiness-Coach-IRC-
   ```

2. **Create and activate conda environment:**
   ```bash
   conda env create -f environment.yml
   conda activate irc-coach
   ```

3. **Configure environment variables:**
   ```bash
   # Copy example .env file (if exists) or create .env
   # Add your API keys:
   OPENAI_API_KEY=your_key_here
   # OR
   ANTHROPIC_API_KEY=your_key_here
   ```

4. **Initialize database:**
   ```bash
   cd backend
   python -m scripts.init_db
   ```

5. **Install frontend dependencies:**
   ```bash
   cd frontend
   npm install
   ```

### Running the Application

**Terminal 1 - Backend:**
```bash
conda activate irc-coach
cd backend
uvicorn main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**Access the application:**
- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/docs
- API: http://localhost:8000

### Using Make Commands

Alternatively, use the Makefile:
```bash
make backend    # Start backend server
make frontend   # Start frontend server
```

---

## Documentation

- **[SETUP.md](SETUP.md)** - Detailed setup instructions
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture and design
- **[DEMO_SCRIPT.md](DEMO_SCRIPT.md)** - Demo script for showcasing the system
- **[KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md)** - Known limitations and future improvements

### Phase Summaries

- **[PHASE1_SUMMARY.md](PHASE1_SUMMARY.md)** - Project scaffolding
- **[PHASE2_SUMMARY.md](PHASE2_SUMMARY.md)** - Document processing
- **[PHASE4_SUMMARY.md](PHASE4_SUMMARY.md)** - Gap analysis
- **[PHASE5_SUMMARY.md](PHASE5_SUMMARY.md)** - Study planning
- **[PHASE6_SUMMARY.md](PHASE6_SUMMARY.md)** - Daily coaching
- **[PHASE7_SUMMARY.md](PHASE7_SUMMARY.md)** - Practice generation
- **[PHASE8_SUMMARY.md](PHASE8_SUMMARY.md)** - Evaluation agent
- **[PHASE9_SUMMARY.md](PHASE9_SUMMARY.md)** - Mastery tracking
- **[PHASE10_SUMMARY.md](PHASE10_SUMMARY.md)** - Adaptive planning
- **[PHASE11_SUMMARY.md](PHASE11_SUMMARY.md)** - Calendar integration
- **[PHASE12_SUMMARY.md](PHASE12_SUMMARY.md)** - Observability & testing

---

## Usage Guide

### 1. Upload Documents

1. Navigate to the **Upload** page
2. Upload your resume (PDF or DOCX)
3. Upload or paste the job description
4. Click "Upload Documents"

### 2. Analyze Skill Gaps

1. Go to the **Dashboard**
2. Click "View Gap Analysis"
3. Review identified skill gaps with priorities

### 3. Generate Study Plan

1. From the Dashboard, click "Generate Study Plan"
2. Enter:
   - Interview date
   - Hours per week available
3. Click "Generate"
4. Review the multi-week plan

### 4. Daily Practice

1. Go to **Daily Coach** page
2. View today's tasks
3. Click "View Study Materials" on a task
4. Click "Generate Practice" → Select type
5. Complete practice items and submit
6. Review evaluation feedback

### 5. Track Progress

1. View **Dashboard** for:
   - Skill mastery overview
   - Adaptive plan recommendations
   - System metrics
2. Export calendar for accountability

---

## API Endpoints

### Core Endpoints

- `POST /api/v1/documents/upload` - Upload resume and job description
- `POST /api/v1/gaps/analyze` - Analyze skill gaps
- `POST /api/v1/plans/generate` - Generate study plan
- `GET /api/v1/coach/daily/{date}` - Get daily briefing
- `POST /api/v1/practice/generate` - Generate practice items
- `POST /api/v1/practice/attempts/submit` - Submit practice attempt
- `GET /api/v1/mastery/stats` - Get mastery statistics
- `POST /api/v1/adaptive/analyze` - Analyze adaptation needs
- `GET /api/v1/calendar/ics` - Export calendar (ICS)

### Full API Documentation

Visit http://localhost:8000/docs for interactive Swagger documentation.

---

## Testing

### Integration Tests

Run the integration test suite:
```bash
cd backend
pytest tests/test_integration.py -v
```

### Manual Testing

See [DEMO_SCRIPT.md](DEMO_SCRIPT.md) for step-by-step testing instructions.

---

## Development

### Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/    # API endpoints
│   │   ├── core/                # Configuration, LLM
│   │   ├── db/                   # Database models
│   │   ├── schemas/              # Pydantic schemas
│   │   └── services/             # Business logic
│   ├── tests/                    # Integration tests
│   └── scripts/                  # Utility scripts
├── frontend/
│   ├── src/
│   │   ├── pages/                # Page components
│   │   ├── components/           # Reusable components
│   │   └── App.jsx               # Main app
│   └── public/                   # Static assets
└── docs/                         # Documentation
```

### Adding New Features

1. **Backend:**
   - Add service in `app/services/`
   - Create API endpoint in `app/api/v1/endpoints/`
   - Add schema in `app/schemas/`
   - Update router in `app/api/v1/router.py`

2. **Frontend:**
   - Create page in `frontend/src/pages/`
   - Add route in `frontend/src/App.jsx`
   - Update navigation if needed

---

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# LLM Provider (choose one)
OPENAI_API_KEY=your_key_here
# OR
ANTHROPIC_API_KEY=your_key_here
# OR (for local LLM)
OLLAMA_BASE_URL=http://localhost:11434

# Database (optional, defaults to SQLite)
DATABASE_URL=sqlite:///./irc_coach.db
# For PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost:5432/irc_coach

# Observability (optional)
LANGSMITH_API_KEY=your_key_here
LANGSMITH_PROJECT=irc-coach
LANGSMITH_TRACING=true

# CORS (optional)
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

---

## Troubleshooting

### Common Issues

**Backend won't start:**
- Ensure conda environment is activated
- Check API keys are set in `.env`
- Verify port 8000 is not in use

**Frontend won't load:**
- Run `npm install` in `frontend/` directory
- Check Node.js version (18+)
- Verify port 5173 is not in use

**Database errors:**
- Run `python -m scripts.init_db` to recreate tables
- Check `.env` has correct `DATABASE_URL`
- Ensure database file/directory is writable

**LLM errors:**
- Verify API key is correct
- Check API quota/limits
- For Ollama, ensure service is running

See [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md) for more details.

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

---

## License

See [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- Built with [LangChain](https://www.langchain.com/) and [LangGraph](https://github.com/langchain-ai/langgraph)
- UI built with [React](https://react.dev/) and [Tailwind CSS](https://tailwindcss.com/)
- API built with [FastAPI](https://fastapi.tiangolo.com/)

---

## Support

For issues, questions, or contributions:
- Check [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md) for known issues
- Review [SETUP.md](SETUP.md) for setup help
- See [DEMO_SCRIPT.md](DEMO_SCRIPT.md) for usage examples

---

**Last Updated:** Phase 13 - Documentation Complete
**Version:** 1.0.0

