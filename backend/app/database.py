"""
Database configuration and session management

This module sets up SQLAlchemy engine, session factory, and base class
for all database models.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

# Create SQLAlchemy engine
# echo=True enables SQL query logging in development
engine = create_engine(
    DATABASE_URL,
    pool_size=int(os.getenv("DATABASE_POOL_SIZE", "20")),
    max_overflow=int(os.getenv("DATABASE_MAX_OVERFLOW", "0")),
    echo=os.getenv("DEBUG", "False").lower() == "true",
    future=True
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True
)

# Create base class for declarative models
Base = declarative_base()


def get_db():
    """
    Database session dependency for FastAPI.
    
    Usage in route:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database by creating all tables.
    Only run this in development or during initial setup.
    For production, use Alembic migrations.
    """
    Base.metadata.create_all(bind=engine)
