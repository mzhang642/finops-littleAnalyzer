@echo off
cd backend
call venv\Scripts\activate
celery -A app.celery_app beat --loglevel=info
