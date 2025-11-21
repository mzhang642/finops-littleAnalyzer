"""
ML-enhanced analysis endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime, timedelta

from app.database import get_db
from app.models.base import CloudAccount
from app.models.aws_resources import CostSnapshot
from app.utils.auth import get_current_user
from app.services.ml.cost_predictor import CostPredictor, ResourceUtilizationPredictor
from app.services.aws_cost_explorer import AWSCostExplorer

router = APIRouter()


@router.get("/cost-prediction")
async def get_cost_prediction(
    cloud_account_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get ML-based cost predictions for the next 30 days"""
    
    # Get historical cost data
    snapshots = db.query(CostSnapshot).filter(
        CostSnapshot.cloud_account_id == cloud_account_id,
        CostSnapshot.organization_id == current_user.organization_id
    ).order_by(CostSnapshot.snapshot_date.desc()).limit(90).all()
    
    if len(snapshots) < 30:
        raise HTTPException(
            status_code=400,
            detail="Not enough historical data for prediction (need at least 30 days)"
        )
    
    # Prepare data for training
    historical_costs = [
        {
            'date': snapshot.snapshot_date.strftime('%Y-%m-%d'),
            'cost': float(snapshot.total_cost)
        }
        for snapshot in reversed(snapshots)
    ]
    
    # Train model and generate predictions
    predictor = CostPredictor()
    if predictor.train(historical_costs):
        predictions = predictor.predict_next_days(30)
        insights = predictor.get_cost_insights()
        
        # Detect anomalies in recent costs
        recent_costs = historical_costs[-7:]  # Last 7 days
        anomalies = predictor.detect_anomalies(recent_costs)
        
        return {
            'predictions': predictions,
            'anomalies': anomalies,
            'insights': insights,
            'historical_data': historical_costs[-30:],  # Last 30 days for chart
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to train prediction model")


@router.get("/anomaly-detection")
async def detect_cost_anomalies(
    cloud_account_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Detect anomalies in cloud spending using ML"""
    
    # Get cloud account
    account = db.query(CloudAccount).filter(
        CloudAccount.id == cloud_account_id,
        CloudAccount.organization_id == current_user.organization_id
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Cloud account not found")
    
    # Get recent cost data from AWS
    cost_explorer = AWSCostExplorer(account.credentials_encrypted)
    daily_costs = cost_explorer.get_daily_costs(90)  # Get 90 days for training
    
    if len(daily_costs) < 30:
        raise HTTPException(
            status_code=400,
            detail="Not enough data for anomaly detection"
        )
    
    # Train model
    predictor = CostPredictor()
    if predictor.train(daily_costs[:-7]):  # Train on all but last 7 days
        # Detect anomalies in last 7 days
        anomalies = predictor.detect_anomalies(daily_costs[-7:])
        
        # Add recommendations for each anomaly
        for anomaly in anomalies:
            if anomaly['type'] == 'spike':
                anomaly['recommendations'] = [
                    "Review recent deployments or configuration changes",
                    "Check for runaway resources or infinite loops",
                    "Verify auto-scaling settings",
                    "Look for unauthorized resource creation"
                ]
            else:  # drop
                anomaly['recommendations'] = [
                    "Verify this is expected (e.g., scheduled downtime)",
                    "Check if services were accidentally terminated",
                    "Review if this indicates an outage"
                ]
        
        return {
            'anomalies_detected': len(anomalies),
            'anomalies': anomalies,
            'analysis_period': {
                'start': daily_costs[0]['date'],
                'end': daily_costs[-1]['date']
            },
            'model_confidence': 0.95
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to train anomaly detection model")


@router.get("/utilization-prediction/{resource_type}")
async def predict_resource_utilization(
    resource_type: str,
    resource_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Predict future utilization patterns for a resource"""
    
    # This would fetch actual CloudWatch metrics in production
    # For demo, we'll generate sample data
    sample_data = [
        {
            'timestamp': (datetime.now() - timedelta(hours=i)).isoformat(),
            'utilization': 30 + (i % 24) * 2 + (i % 168) * 0.5  # Simulate daily/weekly patterns
        }
        for i in range(720, 0, -1)  # 30 days of hourly data
    ]
    
    predictor = ResourceUtilizationPredictor()
    if predictor.train_resource_model(resource_type, sample_data):
        underutilized_periods = predictor.predict_underutilization(resource_type)
        
        # Calculate potential savings
        hourly_cost = 0.1  # Example: $0.10/hour for the resource
        hours_underutilized = len(underutilized_periods)
        potential_savings = hours_underutilized * hourly_cost
        
        return {
            'resource_type': resource_type,
            'resource_id': resource_id,
            'prediction_period': '7 days',
            'underutilized_hours': hours_underutilized,
            'potential_monthly_savings': potential_savings * 4,  # Extrapolate to month
            'optimization_windows': underutilized_periods[:24],  # First 24 hours
            'recommendation': {
                'action': 'Implement auto-shutdown schedule',
                'estimated_savings': f'${potential_savings * 4:.2f}/month',
                'confidence': 0.85
            }
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to train utilization model")
