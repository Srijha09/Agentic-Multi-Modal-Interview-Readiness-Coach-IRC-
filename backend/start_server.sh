#!/bin/bash
# Start the FastAPI backend server
# Make sure conda environment is activated first!

echo "Starting Interview Readiness Coach Backend Server..."
echo ""
echo "Make sure you have activated the conda environment:"
echo "  conda activate irc-coach"
echo ""

cd "$(dirname "$0")"
uvicorn main:app --reload --port 8000


