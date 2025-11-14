"""
AWS-specific resource models
"""
from sqlalchemy import Column, String, Float, DateTime, JSON, ForeignKey, Boolean, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class AWSResource(Base):
    """Generic AWS resource tracking"""
    __tablename__ = "aws_resources"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cloud_account_id = Column(UUID(as_uuid=True), ForeignKey("cloud_accounts.id"))
    
    # Resource identification
    resource_type = Column(String, nullable=False)  # ec2, rds, s3, ebs, etc.
    resource_id = Column(String, nullable=False)
    resource_arn = Column(String)
    resource_name = Column(String)
    
    # Location
    region = Column(String, nullable=False)
    availability_zone = Column(String)
    
    # Status
    state = Column(String)  # running, stopped, terminated, available
    created_time = Column(DateTime)
    
    # Cost data
    hourly_cost = Column(Float, default=0.0)
    monthly_cost = Column(Float, default=0.0)
    
    # Metadata
    tags = Column(JSON)
    specifications = Column(JSON)  # Instance type, size, etc.
    metrics = Column(JSON)  # CPU, memory, network usage
    
    # Tracking
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    last_analyzed = Column(DateTime)
    
    # Relationships
    cloud_account = relationship("CloudAccount", back_populates="aws_resources")
    recommendations = relationship("Recommendation", back_populates="resource")


class Recommendation(Base):
    """Cost optimization recommendations"""
    __tablename__ = "recommendations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resource_id = Column(UUID(as_uuid=True), ForeignKey("aws_resources.id"))
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"))
    
    # Recommendation details
    recommendation_type = Column(String, nullable=False)  # terminate, resize, schedule, reserve
    title = Column(String, nullable=False)
    description = Column(Text)
    
    # Financial impact
    monthly_savings = Column(Float, nullable=False)
    annual_savings = Column(Float)
    implementation_cost = Column(Float, default=0.0)
    
    # Risk and complexity
    risk_level = Column(String, default="low")  # low, medium, high
    complexity = Column(String, default="simple")  # simple, moderate, complex
    confidence_score = Column(Float)  # 0-1 confidence in the recommendation
    
    # Implementation
    action_steps = Column(JSON)  # List of steps to implement
    automation_possible = Column(Boolean, default=False)
    
    # Status tracking
    status = Column(String, default="active")  # active, implemented, dismissed, expired
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    implemented_at = Column(DateTime)
    dismissed_at = Column(DateTime)
    
    # Relationships
    resource = relationship("AWSResource", back_populates="recommendations")
    organization = relationship("Organization")


class CostSnapshot(Base):
    """Daily/hourly cost tracking for trends"""
    __tablename__ = "cost_snapshots"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"))
    cloud_account_id = Column(UUID(as_uuid=True), ForeignKey("cloud_accounts.id"))
    
    # Snapshot data
    snapshot_date = Column(DateTime, nullable=False)
    granularity = Column(String, default="daily")  # hourly, daily, monthly
    
    # Cost breakdown
    total_cost = Column(Float, nullable=False)
    compute_cost = Column(Float)
    storage_cost = Column(Float)
    network_cost = Column(Float)
    database_cost = Column(Float)
    other_cost = Column(Float)
    
    # Service breakdown (JSON for flexibility)
    service_costs = Column(JSON)  # {"EC2": 100.50, "RDS": 50.25, ...}
    
    # Resource counts
    resource_counts = Column(JSON)  # {"ec2_instances": 10, "rds_instances": 2, ...}
    
    created_at = Column(DateTime, default=datetime.utcnow)
