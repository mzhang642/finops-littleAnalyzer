"""
Test configuration using Supabase
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

from app.main import app
from app.database import Base, get_db

load_dotenv()

# Use Supabase for tests (same as development)
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def client():
    """Create test client"""
    yield TestClient(app)
    # Clean up test data after tests
    db = TestingSessionLocal()
    # Use text() wrapper for raw SQL
    db.execute(text("DELETE FROM users WHERE email LIKE 'test%'"))
    db.execute(text("DELETE FROM organizations WHERE email LIKE 'test%'"))
    db.commit()
    db.close()

@pytest.fixture
def test_user():
    """Create test user data"""
    return {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User",
        "organization_name": "Test Org"
    }