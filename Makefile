.PHONY: help setup backend frontend test clean

help:
	@echo "Interview Readiness Coach - Makefile Commands"
	@echo ""
	@echo "  make setup       - Set up conda environment and install dependencies"
	@echo "  make backend     - Start backend server"
	@echo "  make frontend    - Start frontend dev server"
	@echo "  make init-db     - Initialize database"
	@echo "  make test        - Run tests"
	@echo "  make clean       - Clean build artifacts"

setup:
	@echo "Creating conda environment..."
	conda env create -f environment.yml
	@echo "Installing frontend dependencies..."
	cd frontend && npm install

backend:
	@echo "Starting backend server..."
	cd backend && uvicorn main:app --reload --port 8000

frontend:
	@echo "Starting frontend dev server..."
	cd frontend && npm run dev

init-db:
	@echo "Initializing database..."
	cd backend && python scripts/init_db.py

test:
	@echo "Running tests..."
	cd backend && pytest

clean:
	@echo "Cleaning build artifacts..."
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	rm -rf backend/dist backend/build
	rm -rf frontend/dist frontend/node_modules




