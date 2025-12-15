# Agentic Multi-Modal Interview Readiness Coach

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

## Architecture

┌────────────────────────────────────────────┐
│ React Frontend │
│ • Intake & Upload │
│ • Gap Report Dashboard │
│ • Daily Tasks & Practice │
│ • Progress & Mastery Charts │
└───────────────┬────────────────────────────┘
│
▼
┌────────────────────────────────────────────┐
│ FastAPI Backend │
│ │
│ ┌──────────────────────────────────────┐ │
│ │ LangGraph Agent System │ │
│ │ │ │
│ │ Intake Agent │ │
│ │ Gap Analysis Agent │ │
│ │ Planner Agent │ │
│ │ Daily Coach Agent │ │
│ │ Evaluation Agent │ │
│ │ Adaptation Agent │ │
│ └──────────────────────────────────────┘ │
│ │
│ Tools: Resume Parser, JD Parser, │
│ Skill Extractor, Quiz Generator, │
│ Evaluation Rubrics, Calendar Tool │
└───────────────┬────────────────────────────┘
│
▼
┌────────────────────────────────────────────┐
│ Data Layer │
│ • Users, Skills, Gaps │
│ • Plans, Tasks, Practice Items │
│ • Attempts, Evaluations, Mastery │
│ • Calendar Events │
└────────────────────────────────────────────┘

yaml
Copy code

---

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

# Agentic Interview Readiness Coach: Implementation Plan

## Overview

This plan breaks the system into **13 verifiable, sequential phases**, mirroring real-world AI system development. Each phase produces concrete artifacts and is independently testable.

**Total Phases:** 13  
**Critical Path:** Phases 1 → 7 → 12 → 13  
**Parallelization:** Frontend (Phases 8–11) after Phase 7

---

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

**Explicitly Out of Scope (V2)**
- Live mock interviews
- Video/voice analysis
- Coding execution sandbox

---

## Why This Is a Flagship Project

- Demonstrates **agentic planning**
- Shows **evaluation-driven adaptation**
- Uses **real-world constraints**
- Avoids toy-chatbot patterns
- Maps directly to production AI systems

## Architecture

