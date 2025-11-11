"""
Core database models for FinOps Analyzer

Models:
- Organization: Company/team using the platform
- User: Individual user accounts
- CloudAccount: Connected cloud provider accounts (AWS/GCP/Azure)
- Resource: Individual cloud resources being tracked
- Anomaly: Detected cost anomalies and waste
- Recommendation: Optimization recommendations
- SavingsReport: Historical savings reports
"""
from sqlalchemy import Column, String, Float, DateTime, JSON, ForeignKey, Boolean, Integer, Enum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


# Enums
class SubscriptionTier(str, enum.Enum):
    """Subscription tiers with increasing features"""
    TRIAL = "trial"
    STARTER = "starter"
    GROWTH = "growth"
    ENTERPRISE = "enterprise"


class UserRole(str, enum.Enum):
    """User roles with different permission levels"""
    ADMIN = "admin"  # Full access
    MEMBER = "member"  # Standard access
    VIEWER = "viewer"  # Read-only access


class CloudProvider(str, enum.Enum):
    """Supported cloud providers"""
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"


class AnomalySeverity(str, enum.Enum):
    """Anomaly severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnomalyStatus(str, enum.Enum):
    """Anomaly lifecycle status"""
    ACTIVE = "active"
    RESOLVED = "resolved"
    IGNORED = "ignored"
    IN_PROGRESS = "in_progress"


# Models
class Organization(Base):
    """
    Organization/Company using the FinOps platform.
    Each org can have multiple users and cloud accounts.
    """
    __tablename__ = "organizations"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic information
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Subscription information
    subscription_tier = Column(Enum(SubscriptionTier), default=SubscriptionTier.TRIAL, nullable=False)
    subscription_status = Column(String(50), default="active", nullable=False)
    subscription_start_date = Column(DateTime)
    subscription_end_date = Column(DateTime)
    stripe_customer_id = Column(String(255), unique=True, index=True)
    stripe_subscription_id = Column(String(255))
    
    # Usage metrics
    monthly_cloud_spend = Column(Float, default=0.0)
    total_savings_identified = Column(Float, default=0.0)
    total_savings_implemented = Column(Float, default=0.0)
    
    # Settings (JSON field for flexible configuration)
    settings = Column(JSON, default={})
    
    # Soft delete
    is_active = Column(Boolean, default=True, nullable=False)
    deleted_at = Column(DateTime)
    
    # Relationships
    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    cloud_accounts = relationship("CloudAccount", back_populates="organization", cascade="all, delete-orphan")
    savings_reports = relationship("SavingsReport", back_populates="organization", cascade="all, delete-orphan")


class User(Base):
    """
    Individual user accounts.
    Each user belongs to one organization.
    """
    __tablename__ = "users"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Authentication
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    
    # Profile
    full_name = Column(String(255))
    avatar_url = Column(String(512))
    
    # Authorization
    role = Column(Enum(UserRole), default=UserRole.MEMBER, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_email_verified = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime)
    
    # Email verification
    email_verification_token = Column(String(255))
    email_verified_at = Column(DateTime)
    
    # Password reset
    password_reset_token = Column(String(255))
    password_reset_expires = Column(DateTime)
    
    # Relationships
    organization = relationship("Organization", back_populates="users")


class CloudAccount(Base):
    """
    Connected cloud provider accounts (AWS, GCP, Azure).
    Stores encrypted credentials and sync status.
    """
    __tablename__ = "cloud_accounts"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Account information
    provider = Column(Enum(CloudProvider), nullable=False)
    account_id = Column(String(255), nullable=False)  # AWS Account ID, GCP Project ID, etc.
    account_name = Column(String(255))
    
    # Credentials (encrypted at rest)
    credentials_encrypted = Column(Text, nullable=False)
    encryption_key_id = Column(String(255))  # Reference to encryption key
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_syncing = Column(Boolean, default=False, nullable=False)
    last_sync = Column(DateTime)
    last_sync_status = Column(String(50))  # success, failed, partial
    last_sync_error = Column(Text)
    next_sync_scheduled = Column(DateTime)
    
    # Metrics
    resource_count = Column(Integer, default=0)
    monthly_spend = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Settings
    sync_frequency_hours = Column(Integer, default=24)  # How often to sync
    regions_enabled = Column(JSON, default=[])  # Which regions to analyze
    
    # Relationships
    organization = relationship("Organization", back_populates="cloud_accounts")
    resources = relationship("Resource", back_populates="cloud_account", cascade="all, delete-orphan")
    anomalies = relationship("Anomaly", back_populates="cloud_account", cascade="all, delete-orphan")


class Resource(Base):
    """
    Individual cloud resources (EC2 instances, RDS databases, S3 buckets, etc.)
    """
    __tablename__ = "resources"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    cloud_account_id = Column(UUID(as_uuid=True), ForeignKey("cloud_accounts.id"), nullable=False, index=True)
    
    # Resource identification
    resource_type = Column(String(100), nullable=False, index=True)  # ec2_instance, rds_instance, s3_bucket
    resource_id = Column(String(255), nullable=False)  # Cloud provider's resource ID
    resource_name = Column(String(255))
    resource_arn = Column(String(512))  # AWS ARN or equivalent
    
    # Location
    region = Column(String(50))
    availability_zone = Column(String(50))
    
    # Tags (from cloud provider)
    tags = Column(JSON, default={})
    
    # State
    state = Column(String(50))  # running, stopped, terminated, etc.
    
    # Cost information
    cost_per_hour = Column(Float, default=0.0)
    cost_per_day = Column(Float, default=0.0)
    cost_per_month = Column(Float, default=0.0)
    currency = Column(String(3), default="USD")
    
    # Utilization metrics
    utilization_percent = Column(Float)  # Average utilization
    utilization_metrics = Column(JSON, default={})  # Detailed metrics
    
    # Specifications
    size_spec = Column(JSON, default={})  # Instance type, storage size, etc.
    
    # Additional metadata
    metadata = Column(JSON, default={})
    
    # Timestamps
    first_seen = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_seen = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    cloud_account = relationship("CloudAccount", back_populates="resources")
    anomalies = relationship("Anomaly", back_populates="resource")


class Anomaly(Base):
    """
    Detected cost anomalies and optimization opportunities.
    Generated by ML models and rule-based systems.
    """
    __tablename__ = "anomalies"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    cloud_account_id = Column(UUID(as_uuid=True), ForeignKey("cloud_accounts.id"), nullable=False, index=True)
    resource_id = Column(UUID(as_uuid=True), ForeignKey("resources.id"), nullable=True, index=True)
    
    # Classification
    anomaly_type = Column(String(100), nullable=False, index=True)  # unused, overprovisioned, cost_spike
    category = Column(String(100))  # compute, storage, network, database
    
    # Severity and confidence
    severity = Column(Enum(AnomalySeverity), default=AnomalySeverity.MEDIUM, nullable=False)
    confidence_score = Column(Float)  # 0.0 to 1.0
    
    # Status
    status = Column(Enum(AnomalyStatus), default=AnomalyStatus.ACTIVE, nullable=False)
    
    # Timestamps
    detected_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    resolved_at = Column(DateTime)
    acknowledged_at = Column(DateTime)
    
    # Financial impact
    potential_monthly_savings = Column(Float, default=0.0)
    actual_savings_achieved = Column(Float, default=0.0)
    cost_impact = Column(Float, default=0.0)
    
    # Description and recommendation
    title = Column(String(255), nullable=False)
    description = Column(Text)
    recommendation = Column(JSON, default={})  # Structured recommendation with steps
    
    # Detection method
    detection_method = Column(String(100))  # ml_model, rule_based, user_reported
    model_version = Column(String(50))
    
    # Additional data
    evidence = Column(JSON, default={})  # Supporting data for the anomaly
    
    # Relationships
    cloud_account = relationship("CloudAccount", back_populates="anomalies")
    resource = relationship("Resource", back_populates="anomalies")


class SavingsReport(Base):
    """
    Historical savings reports generated for organizations.
    Tracks progress over time.
    """
    __tablename__ = "savings_reports"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Report metadata
    report_date = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    report_type = Column(String(50), default="monthly")  # daily, weekly, monthly, quarterly
    
    # Financial metrics
    total_spend = Column(Float, default=0.0)
    identified_savings = Column(Float, default=0.0)
    implemented_savings = Column(Float, default=0.0)
    savings_percentage = Column(Float, default=0.0)
    
    # Breakdown by service/category
    spend_by_service = Column(JSON, default={})
    savings_by_category = Column(JSON, default={})
    
    # Top recommendations
    top_recommendations = Column(JSON, default=[])
    
    # Full report data
    report_data = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="savings_reports")
