"""
Analysis API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime
from pydantic import BaseModel
import logging

from app.database import get_db
from app.models.base import CloudAccount, Organization
from app.models.aws_resources import AWSResource, Recommendation, CostSnapshot
from app.utils.auth import get_current_user
from app.services.aws_cost_explorer import AWSCostExplorer
from app.services.aws_ec2_analyzer import EC2Analyzer
from app.services.aws_storage_analyzer import StorageAnalyzer

router = APIRouter()
logger = logging.getLogger(__name__)


class AnalysisRequest(BaseModel):
    cloud_account_id: str
    analysis_types: List[str] = ["cost", "ec2", "storage"]


class AnalysisResponse(BaseModel):
    status: str
    message: str
    analysis_id: str
    results: Dict[str, Any] = {}


@router.post("/analyze", response_model=AnalysisResponse)
async def run_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Run cost analysis on a cloud account"""
    
    # Verify account belongs to user's organization
    account = db.query(CloudAccount).filter(
        CloudAccount.id == request.cloud_account_id,
        CloudAccount.organization_id == current_user.organization_id
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Cloud account not found")
    
    # Run analysis in background
    background_tasks.add_task(
        run_account_analysis,
        account.id,
        account.credentials_encrypted,
        request.analysis_types,
        db
    )
    
    return AnalysisResponse(
        status="started",
        message="Analysis started in background",
        analysis_id=str(account.id)
    )


def run_account_analysis(
    account_id: str,
    encrypted_credentials: str,
    analysis_types: List[str],
    db: Session
):
    """Run the actual analysis (background task)"""
    try:
        results = {}
        
        # Cost Analysis
        if "cost" in analysis_types:
            cost_explorer = AWSCostExplorer(encrypted_credentials)
            results['cost'] = {
                'current_month': cost_explorer.get_current_month_spend(),
                'daily_costs': cost_explorer.get_daily_costs(30),
                'service_breakdown': cost_explorer.get_service_costs(30),
                'anomalies': cost_explorer.detect_cost_anomalies()
            }
            
            # Store cost snapshot
            if results['cost']['current_month'].get('total'):
                snapshot = CostSnapshot(
                    cloud_account_id=account_id,
                    organization_id=db.query(CloudAccount).get(account_id).organization_id,
                    snapshot_date=datetime.utcnow(),
                    total_cost=results['cost']['current_month']['total'],
                    service_costs=results['cost']['service_breakdown']
                )
                db.add(snapshot)
        
        # EC2 Analysis
        if "ec2" in analysis_types:
            ec2_analyzer = EC2Analyzer(encrypted_credentials)
            instances = ec2_analyzer.get_all_instances()
            opportunities = ec2_analyzer.find_optimization_opportunities()
            
            results['ec2'] = {
                'total_instances': len(instances),
                'total_monthly_cost': sum(i['monthly_cost'] for i in instances),
                'opportunities': opportunities,
                'potential_savings': sum(o.get('monthly_savings', 0) for o in opportunities)
            }
            
            # Store recommendations in database
            for opp in opportunities:
                rec = Recommendation(
                    organization_id=db.query(CloudAccount).get(account_id).organization_id,
                    recommendation_type=opp['type'],
                    title=f"{opp['type'].replace('_', ' ').title()}",
                    description=opp['reason'],
                    monthly_savings=opp.get('monthly_savings', 0),
                    risk_level=opp.get('risk', 'medium'),
                    confidence_score=opp.get('confidence', 0.5),
                    action_steps=[opp['action']]
                )
                db.add(rec)
        
        # Storage Analysis
        if "storage" in analysis_types:
            storage_analyzer = StorageAnalyzer(encrypted_credentials)
            ebs_results = storage_analyzer.analyze_ebs_volumes()
            s3_results = storage_analyzer.analyze_s3_buckets()
            
            results['storage'] = {
                'ebs': ebs_results,
                's3': s3_results,
                'total_monthly_cost': ebs_results['total_monthly_cost'] + s3_results['total_monthly_cost'],
                'total_recommendations': len(ebs_results['recommendations']) + len(s3_results['recommendations'])
            }
            
            # Store storage recommendations
            for rec_data in ebs_results['recommendations'] + s3_results['recommendations']:
                rec = Recommendation(
                    organization_id=db.query(CloudAccount).get(account_id).organization_id,
                    recommendation_type=rec_data['type'],
                    title=f"{rec_data['type'].replace('_', ' ').title()}",
                    description=rec_data['reason'],
                    monthly_savings=rec_data.get('monthly_savings', 0),
                    risk_level=rec_data.get('risk', 'medium'),
                    confidence_score=rec_data.get('confidence', 0.5),
                    action_steps=[rec_data['action']]
                )
                db.add(rec)
        
        # Update last sync status
        account = db.query(CloudAccount).get(account_id)
        account.last_sync = datetime.utcnow()
        account.last_sync_status = "success"
        
        db.commit()
        logger.info(f"Analysis completed for account {account_id}")
        
    except Exception as e:
        logger.error(f"Analysis failed for account {account_id}: {str(e)}")
        
        # Update sync status
        account = db.query(CloudAccount).get(account_id)
        if account:
            account.last_sync = datetime.utcnow()
            account.last_sync_status = f"failed: {str(e)}"
            db.commit()


@router.get("/recommendations")
async def get_recommendations(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get top recommendations for the organization"""
    
    recommendations = db.query(Recommendation).filter(
        Recommendation.organization_id == current_user.organization_id,
        Recommendation.status == "active"
    ).order_by(
        Recommendation.monthly_savings.desc()
    ).limit(limit).all()
    
    return {
        'total': len(recommendations),
        'potential_monthly_savings': sum(r.monthly_savings for r in recommendations),
        'recommendations': [
            {
                'id': str(r.id),
                'type': r.recommendation_type,
                'title': r.title,
                'description': r.description,
                'monthly_savings': r.monthly_savings,
                'risk_level': r.risk_level,
                'confidence': r.confidence_score,
                'actions': r.action_steps,
                'created_at': r.created_at.isoformat()
            }
            for r in recommendations
        ]
    }


@router.get("/dashboard")
async def get_dashboard_data(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get dashboard summary data"""
    
    # Get latest cost snapshot
    latest_snapshot = db.query(CostSnapshot).filter(
        CostSnapshot.organization_id == current_user.organization_id
    ).order_by(CostSnapshot.snapshot_date.desc()).first()
    
    # Get active recommendations
    recommendations = db.query(Recommendation).filter(
        Recommendation.organization_id == current_user.organization_id,
        Recommendation.status == "active"
    ).all()
    
    # Calculate totals
    total_spend = latest_snapshot.total_cost if latest_snapshot else 0
    potential_savings = sum(r.monthly_savings for r in recommendations)
    
    return {
        'current_month_spend': total_spend,
        'potential_monthly_savings': potential_savings,
        'savings_percentage': (potential_savings / total_spend * 100) if total_spend > 0 else 0,
        'active_recommendations': len(recommendations),
        'top_recommendations': [
            {
                'title': r.title,
                'savings': r.monthly_savings,
                'risk': r.risk_level
            }
            for r in sorted(recommendations, key=lambda x: x.monthly_savings, reverse=True)[:5]
        ],
        'service_breakdown': latest_snapshot.service_costs if latest_snapshot else {},
        'last_analysis': latest_snapshot.snapshot_date.isoformat() if latest_snapshot else None
    }
