"""
Cloud account management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime
import logging

from app.database import get_db
from app.models.base import CloudAccount, Organization
from app.utils.auth import get_current_user
from app.utils.encryption import encrypt_credentials
from app.services.aws_base import AWSService

router = APIRouter()
logger = logging.getLogger(__name__)


class CloudAccountCreate(BaseModel):
    provider: str = "aws"
    account_name: str
    access_key: str
    secret_key: str
    region: str = "us-east-1"


class CloudAccountResponse(BaseModel):
    id: str
    provider: str
    account_id: str
    account_name: str
    is_active: bool
    last_sync: datetime = None
    last_sync_status: str = None


@router.post("/connect", response_model=CloudAccountResponse)
async def connect_cloud_account(
    account_data: CloudAccountCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Connect a new cloud account"""
    
    # Test credentials first
    try:
        test_creds = encrypt_credentials({
            'access_key': account_data.access_key,
            'secret_key': account_data.secret_key
        })
        
        aws_service = AWSService(test_creds, account_data.region)
        test_result = aws_service.test_connection()
        
        if not test_result['connected']:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to connect: {test_result.get('errors', ['Unknown error'])}"
            )
        
        account_id = test_result['account_id']
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid credentials: {str(e)}")
    
    # Check if account already exists
    existing = db.query(CloudAccount).filter(
        CloudAccount.account_id == account_id,
        CloudAccount.organization_id == current_user.organization_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Account already connected")
    
    # Create cloud account
    cloud_account = CloudAccount(
        organization_id=current_user.organization_id,
        provider=account_data.provider,
        account_id=account_id,
        account_name=account_data.account_name,
        credentials_encrypted=test_creds,
        is_active=True
    )
    
    db.add(cloud_account)
    db.commit()
    db.refresh(cloud_account)
    
    return CloudAccountResponse(
        id=str(cloud_account.id),
        provider=cloud_account.provider,
        account_id=cloud_account.account_id,
        account_name=cloud_account.account_name,
        is_active=cloud_account.is_active,
        last_sync=cloud_account.last_sync,
        last_sync_status=cloud_account.last_sync_status
    )


@router.get("/", response_model=List[CloudAccountResponse])
async def list_cloud_accounts(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List all cloud accounts for the organization"""
    
    accounts = db.query(CloudAccount).filter(
        CloudAccount.organization_id == current_user.organization_id
    ).all()
    
    return [
        CloudAccountResponse(
            id=str(account.id),
            provider=account.provider,
            account_id=account.account_id,
            account_name=account.account_name,
            is_active=account.is_active,
            last_sync=account.last_sync,
            last_sync_status=account.last_sync_status
        )
        for account in accounts
    ]


@router.delete("/{account_id}")
async def disconnect_cloud_account(
    account_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Disconnect a cloud account"""
    
    account = db.query(CloudAccount).filter(
        CloudAccount.id == account_id,
        CloudAccount.organization_id == current_user.organization_id
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    db.delete(account)
    db.commit()
    
    return {"message": "Account disconnected successfully"}
