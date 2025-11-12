"""
Main FastAPI application for FinOps Cost Analyzer

This is the entry point for the backend API. It configures:
- CORS middleware for frontend communication
- API routers for different features
- Database initialization
- Health check endpoints
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
import logging

from app.database import engine, Base

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events.
    Runs on startup and shutdown.
    """
    # Startup
    logger.info("Starting FinOps Cost Analyzer API...")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'production')}")
    
    # Create database tables (development only - use Alembic in production)
    if os.getenv("DEBUG", "False").lower() == "true":
        logger.info("Creating database tables (development mode)...")
        Base.metadata.create_all(bind=engine)
    
    yield
    
    # Shutdown
    logger.info("Shutting down FinOps Cost Analyzer API...")


# Create FastAPI application
app = FastAPI(
    title=os.getenv("APP_NAME", "FinOps Cost Analyzer API"),
    description="AI-powered cloud cost optimization for startups",
    version=os.getenv("APP_VERSION", "0.1.0"),
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)


# Configure CORS
origins = [
    "http://localhost:3000",  # Next.js frontend (development)
    "http://localhost:8000",  # FastAPI docs
]

# Add additional origins from environment
if os.getenv("BACKEND_CORS_ORIGINS"):
    import json
    origins.extend(json.loads(os.getenv("BACKEND_CORS_ORIGINS")))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint - API information
    """
    return {
        "message": "FinOps Cost Analyzer API",
        "version": os.getenv("APP_VERSION", "0.1.0"),
        "environment": os.getenv("ENVIRONMENT", "production"),
        "documentation": "/api/docs",
        "status": "operational"
    }


# Health check endpoint
@app.get("/api/health")
async def health_check():
    """
    Health check endpoint for monitoring and load balancers
    """
    return {
        "status": "healthy",
        "environment": os.getenv("ENVIRONMENT", "production"),
        "version": os.getenv("APP_VERSION", "0.1.0")
    }


# Database connection test
@app.get("/api/health/db")
async def database_health():
    """
    Database connection health check
    """
    try:
        from app.database import SessionLocal
        db = SessionLocal()
        result = db.execute("SELECT 1 as health_check")
        db.close()
        
        return {
            "status": "healthy",
            "database": "connected",
            "message": "Database connection successful"
        }
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Database connection failed: {str(e)}"
        )


# Redis connection test (for Celery)
@app.get("/api/health/redis")
async def redis_health():
    """
    Redis connection health check
    """
    try:
        import redis
        r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
        r.ping()
        
        return {
            "status": "healthy",
            "redis": "connected",
            "message": "Redis connection successful"
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Redis connection failed: {str(e)}"
        )


# API Routes will be added here as we build them
# Example:
# from app.routers import auth, cloud_accounts, analysis
# app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
# app.include_router(cloud_accounts.router, prefix="/api/v1/cloud-accounts", tags=["cloud-accounts"])


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=os.getenv("DEBUG", "False").lower() == "true",
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )
