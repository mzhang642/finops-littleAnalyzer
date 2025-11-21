"""
Main FastAPI application for FinOps Analyzer
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
from app.routers import auth
from app.database import engine, Base
from app.routers import analysis
from app.routers import cloud_accounts

# Load environment variables
load_dotenv()

# Create database tables (they already exist in Supabase, but this is safe)
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="FinOps Little Analyzer API",
    description="AI-powered cloud cost optimization for startups",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "FinOps Little Analyzer API",
        "version": "0.1.0",
        "documentation": "/api/docs"
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": os.getenv("ENVIRONMENT", "development")
    }

@app.get("/api/v1/test-db")
async def test_database():
    """Test database connection"""
    try:
        from app.database import SessionLocal
        db = SessionLocal()
        # Simple query to test connection
        result = db.execute("SELECT 1")
        db.close()
        return {"status": "connected", "message": "Database connection successful"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")
    
    
# Add auth router
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])

# Add analysis router
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["analysis"])

# Add router
app.include_router(cloud_accounts.router, prefix="/api/v1/cloud-accounts", tags=["cloud-accounts"])


from app.routers import ml_analysis
app.include_router(ml_analysis.router, prefix="/api/v1/ml", tags=["ml-analysis"])

