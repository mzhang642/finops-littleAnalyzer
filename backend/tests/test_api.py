"""
API endpoint tests
"""
def test_root(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "FinOps Little Analyzer API"

def test_health(client):
    """Test health check"""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_signup(client, test_user):
    """Test user signup"""
    response = client.post("/api/v1/auth/signup", json=test_user)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user["email"]
    assert data["role"] == "admin"