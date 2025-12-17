# Setup Instructions

## Phase 1: Project Scaffolding

This document provides step-by-step instructions to set up and validate the Interview Readiness Coach project.

---

## Prerequisites

- **Conda** (Miniconda or Anaconda)
- **Node.js** 18+ (will be installed via conda)
- **Python** 3.11 (will be installed via conda)

---

## Step 1: Create Conda Environment

```bash
# Create and activate the conda environment
conda env create -f environment.yml
conda activate irc-coach
```

This will install:
- Python 3.11
- Node.js 22 (installed)
- All Python dependencies (FastAPI, LangChain, LangGraph, etc.)
- All system dependencies

---

## Step 2: Configure Environment Variables

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your API keys:
   ```bash
   # Required for LLM functionality
   OPENAI_API_KEY=your_openai_api_key_here
   # OR
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   
   # Optional - for observability
   LANGSMITH_API_KEY=your_langsmith_api_key_here
   ```

---

## Step 3: Initialize Database

From the project root:

```bash
cd backend
python -m scripts.init_db
```

This creates all necessary database tables using SQLite (default). The database file will be created at `backend/irc_coach.db`.

**For PostgreSQL:**
1. Update `.env` with your PostgreSQL connection string:
   ```
   DATABASE_URL=postgresql://user:password@localhost:5432/irc_coach
   ```
2. Run the initialization script again.

---

## Step 4: Install Frontend Dependencies

```bash
cd frontend
npm install
```

This installs:
- React 18
- Vite
- Tailwind CSS
- React Router
- Axios

---

## Step 5: Start Backend Server

From the `backend` directory:

```bash
# Make sure you're in the conda environment
conda activate irc-coach

# Start the FastAPI server
uvicorn main:app --reload --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Step 6: Start Frontend Development Server

In a new terminal (from the `frontend` directory):

```bash
npm run dev
```

The frontend will be available at:
- **Frontend**: http://localhost:5173

---

## Validation Checklist

### Backend Validation

1. **Server starts successfully**
   ```bash
   cd backend
   uvicorn main:app --reload
   ```
   - Should see: `Application startup complete`
   - No import errors

2. **Health check endpoint works**
   ```bash
   curl http://localhost:8000/health
   ```
   - Should return: `{"status": "healthy", ...}`

3. **API documentation accessible**
   - Visit: http://localhost:8000/docs
   - Should see Swagger UI with all endpoints

4. **Database tables created**
   ```bash
   cd backend
   python -c "from app.db.database import engine; from app.db.models import Base; Base.metadata.create_all(bind=engine); print('Tables created')"
   ```
   - Should print: `Tables created`
   - Check `backend/irc_coach.db` exists (SQLite)

5. **All imports work**
   ```bash
   cd backend
   python -c "from app.core.config import settings; from app.db.database import get_db; from app.api.v1.router import api_router; print('All imports successful')"
   ```
   - Should print: `All imports successful`
   - No import errors

### Frontend Validation

1. **Development server starts**
   ```bash
   cd frontend
   npm run dev
   ```
   - Should see: `Local: http://localhost:5173`
   - No compilation errors

2. **All dependencies install**
   ```bash
   cd frontend
   npm install
   ```
   - Should complete without errors
   - `node_modules` directory created

3. **React app renders**
   - Visit: http://localhost:5173
   - Should see "Interview Readiness Coach" homepage
   - Navigation links work

4. **Tailwind CSS works**
   - Check that styles are applied (colors, spacing, etc.)
   - No console errors about missing styles

5. **All imports work**
   ```bash
   cd frontend
   npm run build
   ```
   - Should complete without errors
   - `dist` directory created

---

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── endpoints/
│   │   │       └── router.py
│   │   ├── core/
│   │   │   └── config.py
│   │   └── db/
│   │       ├── database.py
│   │       └── models.py
│   ├── scripts/
│   │   └── init_db.py
│   ├── main.py
│   ├── requirements.txt
│   └── alembic.ini
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
├── environment.yml
├── .env.example
└── SETUP.md
```

---

## Troubleshooting

### Backend Issues

**Import errors:**
- Ensure conda environment is activated: `conda activate irc-coach`
- Verify all dependencies installed: `pip list | grep fastapi`

**Database errors:**
- Check `.env` file has correct `DATABASE_URL`
- Ensure database file/directory is writable
- For PostgreSQL: verify database exists and credentials are correct

**Port already in use:**
- Change port in `uvicorn` command: `--port 8001`
- Update `CORS_ORIGINS` in `.env` if frontend uses different port

### Frontend Issues

**npm install fails:**
- Clear cache: `npm cache clean --force`
- Delete `node_modules` and `package-lock.json`, then reinstall

**Vite server errors:**
- Check Node.js version: `node --version` (should be 18+)
- Verify `vite.config.js` is correct

**Tailwind not working:**
- Ensure `postcss.config.js` exists
- Check `tailwind.config.js` content paths are correct
- Restart dev server

---

## Next Steps (Phase 2+)

Once Phase 1 is validated, you can proceed to:
- Document processing and extraction
- LangGraph agent implementation
- Vector store integration
- Practice generation
- Evaluation system

---

## Quick Start Commands

```bash
# Terminal 1: Backend
conda activate irc-coach
cd backend
uvicorn main:app --reload

# Terminal 2: Frontend
cd frontend
npm run dev
```

Visit http://localhost:5173 to see the application!




