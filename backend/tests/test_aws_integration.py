"""
Test AWS integration endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from app.main import app


@pytest.mark.skip(reason="bcrypt initialization issue in test environment")
def test_connect_cloud_account(client, test_user):
    """Test connecting AWS account"""
    
    # Mock AWS connection test
    with patch('app.services.aws_base.AWSService.test_connection') as mock_test:
        mock_test.return_value = {
            'connected': True,
            'account_id': '123456789012',
            'permissions': {'ec2:DescribeInstances': True}
        }
        
        # First login
        client.post("/api/v1/auth/signup", json=test_user)
        login_response = client.post("/api/v1/auth/login", data={
            "username": test_user["email"],
            "password": test_user["password"]
        })
        token = login_response.json()["access_token"]
        
        # Connect account
        response = client.post(
            "/api/v1/cloud-accounts/connect",
            json={
                "provider": "aws",
                "account_name": "Test Account",
                "access_key": "AKIAIOSFODNN7EXAMPLE",
                "secret_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                "region": "us-east-1"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["account_id"] == "123456789012"
        assert data["provider"] == "aws"


@pytest.mark.skip(reason="bcrypt initialization issue in test environment")
def test_run_analysis(client, test_user):
    """Test running analysis"""
    
    # Setup
    client.post("/api/v1/auth/signup", json=test_user)
    login_response = client.post("/api/v1/auth/login", data={
        "username": test_user["email"],
        "password": test_user["password"]
    })
    token = login_response.json()["access_token"]
    
    # Mock cloud account exists
    with patch('app.routers.analysis.db') as mock_db:
        mock_account = Mock()
        mock_account.id = "test-account-id"
        mock_account.organization_id = "test-org-id"
        mock_db.query().filter().first.return_value = mock_account
        
        response = client.post(
            "/api/v1/analysis/analyze",
            json={
                "cloud_account_id": "test-account-id",
                "analysis_types": ["cost", "ec2"]
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "started"
