#!/bin/bash
# Development server startup script

# Activate virtual environment
source venv/bin/activate

# Run uvicorn with hot reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
