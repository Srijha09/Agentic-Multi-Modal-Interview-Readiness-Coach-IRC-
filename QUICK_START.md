# Quick Start Guide

Get the Interview Readiness Coach running in 5 minutes!

---

## Prerequisites Check

- [ ] Conda installed
- [ ] Node.js 18+ (or will be installed via conda)
- [ ] LLM API key (OpenAI, Anthropic, or Ollama)

---

## Step 1: Setup Environment (2 minutes)

```bash
# 1. Create conda environment
conda env create -f environment.yml
conda activate irc-coach

# 2. Create .env file
echo "OPENAI_API_KEY=your_key_here" > .env
# OR
echo "ANTHROPIC_API_KEY=your_key_here" > .env

# 3. Initialize database
cd backend
python -m scripts.init_db
cd ..

# 4. Install frontend dependencies
cd frontend
npm install
cd ..
```

---

## Step 2: Start Servers (1 minute)

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

**Or use Make:**
```bash
make backend    # Terminal 1
make frontend   # Terminal 2
```

---

## Step 3: Verify (1 minute)

1. **Check Backend:**
   - Visit: http://localhost:8000/docs
   - Should see Swagger API documentation

2. **Check Frontend:**
   - Visit: http://localhost:5173
   - Should see "Interview Readiness Coach" homepage

---

## Step 4: Test the System (1 minute)

1. **Upload Documents:**
   - Go to http://localhost:5173/upload
   - Upload a resume (PDF/DOCX)
   - Paste or upload a job description
   - Click "Upload Documents"

2. **Generate Plan:**
   - Go to Dashboard
   - Click "Generate Study Plan"
   - Enter interview date and hours per week
   - Click "Generate"

3. **View Daily Tasks:**
   - Go to Daily Coach page
   - See today's tasks
   - Generate practice items

---

## Troubleshooting

### Backend won't start?
```bash
# Check environment
conda activate irc-coach
python --version  # Should be 3.11

# Check API key
cat .env | grep API_KEY

# Check port
lsof -i :8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows
```

### Frontend won't start?
```bash
# Reinstall dependencies
cd frontend
rm -rf node_modules package-lock.json
npm install

# Check Node version
node --version  # Should be 18+
```

### Database errors?
```bash
# Recreate database
cd backend
python -m scripts.init_db
```

---

## Next Steps

- Read [SETUP.md](SETUP.md) for detailed setup
- See [DEMO_SCRIPT.md](DEMO_SCRIPT.md) for full demo flow
- Check [ARCHITECTURE.md](ARCHITECTURE.md) for system design
- Review [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md) for known issues

---

## Quick Commands Reference

```bash
# Start everything
make backend    # Terminal 1
make frontend   # Terminal 2

# Database
cd backend && python -m scripts.init_db

# Tests
cd backend && pytest tests/test_integration.py -v

# API Docs
open http://localhost:8000/docs

# Frontend
open http://localhost:5173
```

---

**That's it! You're ready to go! 🚀**

