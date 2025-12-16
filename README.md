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


## Phase 1: Project Setup & Core Infrastructure

### Goal
Establish backend/frontend scaffolding, environments, and baseline project structure.

### Deliverables
- [ ] Conda environment (`environment.yml`)
- [ ] Backend folder structure
- [ ] React + Vite frontend scaffold
- [ ] `.env.example`
- [ ] Basic README
- [ ] Database initialization

### Validation
- Backend and frontend boot successfully
- All dependencies import without error

---

## Phase 2: Core Data Models & Skill/Gaps Schema

### Goal
Define shared schemas for all agents and persistent state.

### Core Models
- User
- Skill
- SkillEvidence
- Gap
- StudyPlan / Week / Day
- Task
- PracticeItem
- Attempt
- Evaluation
- Mastery
- CalendarEvent

### Validation
- Models validate correctly
- Sample plans can be serialized/deserialized

---

## Phase 3: Resume & Job Description Parsing

### Goal
Extract clean, structured text and sections.

### Deliverables
- Resume parser (PDF/DOCX)
- JD parser
- Chunking & normalization pipeline

### Validation
- Parsed content matches uploaded documents
- Sections stored with metadata

---

## Phase 4: Skill Extraction & Gap Analysis Agent

### Goal
Generate prioritized, evidence-backed skill gaps.

### Deliverables
- Skill extraction logic
- Coverage scoring
- Gap priority ranking
- Gap report API

### Validation
- Gap report is explainable and reproducible
- Evidence snippets traceable to source text

---

## Phase 5: Planner Agent (Multi-Week Study Plan)

### Goal
Create a personalized study plan based on gaps and constraints.

### Deliverables
- Weekly themes
- Daily task breakdown
- Estimated time per task

### Validation
- Plans respect time limits
- Tasks map directly to gaps

---

## Phase 6: Daily Coach Agent

### Goal
Orchestrate daily execution and accountability.

### Deliverables
- Daily task briefing
- Missed-task rescheduling
- Carry-over logic

### Validation
- Daily plan updates correctly after completion/miss

---

## Phase 7: Practice Generator

### Goal
Generate aligned practice material.

### Deliverables
- Quiz generator
- Flashcard generator
- Behavioral prompt generator
- System design prompts

### Validation
- Practice difficulty aligns with skill level
- Items stored and retrievable

---

## Phase 8: Evaluation Agent & Rubrics

### Goal
Score user responses and generate feedback.

### Deliverables
- Rubric definitions
- LLM-based evaluation
- Score normalization

### Validation
- Evaluations are consistent
- Feedback is actionable

---

## Phase 9: Progress Tracking & Mastery Updates

### Goal
Track learning over time.

### Deliverables
- Mastery scoring
- Trend tracking
- Streaks and completion stats

### Validation
- Mastery evolves with performance

---

## Phase 10: Adaptive Planning Agent

### Goal
Modify future plans based on learning signals.

### Deliverables
- Reinforcement scheduling
- Difficulty adjustment
- Plan diff logging

### Validation
- Weak skills trigger reinforcement
- Strong skills reduce repetition

---

## Phase 11: Calendar Integration

### Goal
Make the plan actionable in real life.

### Deliverables
- ICS export
- Regeneration on plan updates

### Validation
- Calendar imports correctly
- Events reflect latest plan

---

## Phase 12: Integration Testing & Observability

### Goal
Validate end-to-end system behavior.

### Deliverables
- LangSmith tracing
- End-to-end test flows
- Performance benchmarks

### Validation
- All agents execute in correct order
- No hallucinated gaps or tasks

---

## Phase 13: Documentation & Demo Readiness

### Goal
Prepare project for submission and interviews.

### Deliverables
- Full README
- Architecture diagrams
- Demo script
- Known limitations

### Validation
- Fresh install works
- Demo runs without manual fixes

---

## MVP Scope (Flagship-Ready)

**Must-Have**
- Resume + JD → Gap Report
- 4-week adaptive plan
- Daily quizzes + evaluation
- Mastery tracking
- Calendar export