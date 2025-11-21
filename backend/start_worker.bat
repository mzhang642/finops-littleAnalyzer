@echo off
cd backend
call venv\Scripts\activate
celery -A app.celery_app worker --loglevel=info --pool=solo
