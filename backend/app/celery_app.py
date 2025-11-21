"""
Celery configuration for background tasks
"""
from celery import Celery
from celery.schedules import crontab
import os
from dotenv import load_dotenv

load_dotenv()

# Create Celery instance
celery_app = Celery(
    'finops_analyzer',
    broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    include=['app.tasks']
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Configure periodic tasks
celery_app.conf.beat_schedule = {
    'daily-cost-analysis': {
        'task': 'app.tasks.run_daily_analysis',
        'schedule': crontab(hour=2, minute=0),  # Run at 2 AM UTC daily
    },
    'hourly-anomaly-check': {
        'task': 'app.tasks.check_cost_anomalies',
        'schedule': crontab(minute=0),  # Run every hour
    },
    'weekly-optimization-report': {
        'task': 'app.tasks.generate_optimization_report',
        'schedule': crontab(day_of_week=1, hour=9, minute=0),  # Monday 9 AM UTC
    },
}
