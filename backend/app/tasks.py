"""
Background tasks for automated analysis
"""
from celery import shared_task
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging

from app.database import SessionLocal
from app.models.base import CloudAccount, Organization
from app.models.aws_resources import CostSnapshot, Recommendation
from app.services.aws_cost_explorer import AWSCostExplorer
from app.services.aws_ec2_analyzer import EC2Analyzer
from app.services.aws_storage_analyzer import StorageAnalyzer
from app.services.ml.cost_predictor import CostPredictor

logger = logging.getLogger(__name__)


@shared_task
def run_daily_analysis():
    """Run daily cost analysis for all active cloud accounts"""
    db = SessionLocal()
    
    try:
        # Get all active cloud accounts
        accounts = db.query(CloudAccount).filter(
            CloudAccount.is_active == True
        ).all()
        
        logger.info(f"Running daily analysis for {len(accounts)} accounts")
        
        for account in accounts:
            analyze_account.delay(str(account.id))
        
        return f"Scheduled analysis for {len(accounts)} accounts"
        
    except Exception as e:
        logger.error(f"Daily analysis failed: {str(e)}")
        return f"Error: {str(e)}"
    
    finally:
        db.close()


@shared_task
def analyze_account(account_id: str):
    """Analyze a single cloud account"""
    db = SessionLocal()
    
    try:
        account = db.query(CloudAccount).filter(
            CloudAccount.id == account_id
        ).first()
        
        if not account:
            return f"Account {account_id} not found"
        
        logger.info(f"Analyzing account {account.account_name}")
        
        # Cost Analysis
        cost_explorer = AWSCostExplorer(account.credentials_encrypted)
        current_spend = cost_explorer.get_current_month_spend()
        service_costs = cost_explorer.get_service_costs(30)
        
        # Store cost snapshot
        snapshot = CostSnapshot(
            cloud_account_id=account.id,
            organization_id=account.organization_id,
            snapshot_date=datetime.utcnow(),
            total_cost=current_spend.get('total', 0),
            service_costs=service_costs
        )
        db.add(snapshot)
        
        # EC2 Analysis
        ec2_analyzer = EC2Analyzer(account.credentials_encrypted)
        opportunities = ec2_analyzer.find_optimization_opportunities()
        
        # Store recommendations
        for opp in opportunities:
            existing = db.query(Recommendation).filter(
                Recommendation.organization_id == account.organization_id,
                Recommendation.recommendation_type == opp['type'],
                Recommendation.description == opp['reason'],
                Recommendation.status == 'active'
            ).first()
            
            if not existing:
                rec = Recommendation(
                    organization_id=account.organization_id,
                    recommendation_type=opp['type'],
                    title=opp['type'].replace('_', ' ').title(),
                    description=opp['reason'],
                    monthly_savings=opp.get('monthly_savings', 0),
                    risk_level=opp.get('risk', 'medium'),
                    confidence_score=opp.get('confidence', 0.5),
                    action_steps=[opp['action']]
                )
                db.add(rec)
        
        # Update last sync
        account.last_sync = datetime.utcnow()
        account.last_sync_status = 'success'
        
        db.commit()
        
        logger.info(f"Successfully analyzed account {account.account_name}")
        return f"Analysis complete for {account.account_name}"
        
    except Exception as e:
        logger.error(f"Failed to analyze account {account_id}: {str(e)}")
        
        if account:
            account.last_sync = datetime.utcnow()
            account.last_sync_status = f'failed: {str(e)}'
            db.commit()
        
        return f"Error: {str(e)}"
    
    finally:
        db.close()


@shared_task
def check_cost_anomalies():
    """Check for cost anomalies across all accounts"""
    db = SessionLocal()
    
    try:
        # Get accounts with recent cost data
        accounts = db.query(CloudAccount).filter(
            CloudAccount.is_active == True,
            CloudAccount.last_sync != None
        ).all()
        
        anomalies_found = []
        
        for account in accounts:
            # Get recent cost snapshots
            snapshots = db.query(CostSnapshot).filter(
                CostSnapshot.cloud_account_id == account.id
            ).order_by(CostSnapshot.snapshot_date.desc()).limit(30).all()
            
            if len(snapshots) >= 7:
                # Prepare data for ML
                costs = [
                    {
                        'date': s.snapshot_date.strftime('%Y-%m-%d'),
                        'cost': float(s.total_cost)
                    }
                    for s in reversed(snapshots)
                ]
                
                # Train and detect anomalies
                predictor = CostPredictor()
                if predictor.train(costs[:-1]):
                    anomalies = predictor.detect_anomalies([costs[-1]])
                    
                    if anomalies:
                        anomalies_found.append({
                            'account': account.account_name,
                            'anomalies': anomalies
                        })
                        
                        # Create high-priority recommendation
                        for anomaly in anomalies:
                            if anomaly['severity'] in ['critical', 'high']:
                                rec = Recommendation(
                                    organization_id=account.organization_id,
                                    recommendation_type='cost_anomaly',
                                    title=f"Cost Anomaly Detected",
                                    description=f"Unusual {anomaly['type']} detected: "
                                               f"${anomaly['actual_cost']:.2f} vs expected "
                                               f"${anomaly['expected_cost']:.2f}",
                                    monthly_savings=0,  # Not a savings opportunity
                                    risk_level='high',
                                    confidence_score=anomaly['confidence'],
                                    action_steps=[
                                        "Investigate recent changes",
                                        "Check for unauthorized resources",
                                        "Review auto-scaling settings"
                                    ]
                                )
                                db.add(rec)
        
        db.commit()
        
        logger.info(f"Anomaly check complete. Found {len(anomalies_found)} anomalies")
        return anomalies_found
        
    except Exception as e:
        logger.error(f"Anomaly check failed: {str(e)}")
        return f"Error: {str(e)}"
    
    finally:
        db.close()


@shared_task
def generate_optimization_report(organization_id: str = None):
    """Generate weekly optimization report"""
    db = SessionLocal()
    
    try:
        # Get all organizations or specific one
        if organization_id:
            orgs = [db.query(Organization).get(organization_id)]
        else:
            orgs = db.query(Organization).all()
        
        reports = []
        
        for org in orgs:
            # Get active recommendations
            recommendations = db.query(Recommendation).filter(
                Recommendation.organization_id == org.id,
                Recommendation.status == 'active'
            ).all()
            
            # Calculate totals
            total_savings = sum(r.monthly_savings for r in recommendations)
            
            # Get recent cost
            latest_snapshot = db.query(CostSnapshot).filter(
                CostSnapshot.organization_id == org.id
            ).order_by(CostSnapshot.snapshot_date.desc()).first()
            
            current_spend = latest_snapshot.total_cost if latest_snapshot else 0
            
            report = {
                'organization': org.name,
                'current_monthly_spend': current_spend,
                'potential_savings': total_savings,
                'savings_percentage': (total_savings / current_spend * 100) if current_spend > 0 else 0,
                'top_recommendations': [
                    {
                        'title': r.title,
                        'savings': r.monthly_savings,
                        'risk': r.risk_level
                    }
                    for r in sorted(recommendations, key=lambda x: x.monthly_savings, reverse=True)[:5]
                ],
                'generated_at': datetime.utcnow().isoformat()
            }
            
            reports.append(report)
            
            # TODO: Send email report to organization
            # send_email_report(org.email, report)
        
        logger.info(f"Generated {len(reports)} optimization reports")
        return reports
        
    except Exception as e:
        logger.error(f"Report generation failed: {str(e)}")
        return f"Error: {str(e)}"
    
    finally:
        db.close()
