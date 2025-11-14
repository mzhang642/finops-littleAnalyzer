"""
AWS Cost Explorer service for cost analysis
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, date
import logging
from decimal import Decimal

from app.services.aws_base import AWSService

logger = logging.getLogger(__name__)


class AWSCostExplorer(AWSService):
    """AWS Cost Explorer service for fetching cost data"""
    
    def __init__(self, encrypted_credentials: str, region: str = 'us-east-1'):
        super().__init__(encrypted_credentials, region)
        self.ce_client = self.session.client('ce', region_name='us-east-1')  # CE is only in us-east-1
    
    def get_current_month_spend(self) -> Dict[str, Any]:
        """Get current month's spend to date"""
        try:
            today = date.today()
            start = today.replace(day=1)
            
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start.isoformat(),
                    'End': today.isoformat()
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost', 'UsageQuantity']
            )
            
            if response['ResultsByTime']:
                result = response['ResultsByTime'][0]
                return {
                    'period': result['TimePeriod'],
                    'total': float(result['Total']['UnblendedCost']['Amount']),
                    'currency': result['Total']['UnblendedCost']['Unit'],
                    'usage': result['Total'].get('UsageQuantity', {})
                }
            
            return {'total': 0.0, 'currency': 'USD'}
            
        except Exception as e:
            logger.error(f"Failed to get current month spend: {str(e)}")
            return {'error': str(e)}
    
    def get_daily_costs(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get daily costs for the past N days"""
        try:
            end = date.today()
            start = end - timedelta(days=days)
            
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start.isoformat(),
                    'End': end.isoformat()
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost']
            )
            
            daily_costs = []
            for result in response['ResultsByTime']:
                daily_costs.append({
                    'date': result['TimePeriod']['Start'],
                    'cost': float(result['Total']['UnblendedCost']['Amount']),
                    'currency': result['Total']['UnblendedCost']['Unit']
                })
            
            return daily_costs
            
        except Exception as e:
            logger.error(f"Failed to get daily costs: {str(e)}")
            return []
    
    def get_service_costs(self, days: int = 30) -> Dict[str, float]:
        """Get costs broken down by service"""
        try:
            end = date.today()
            start = end - timedelta(days=days)
            
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start.isoformat(),
                    'End': end.isoformat()
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost'],
                GroupBy=[{
                    'Type': 'DIMENSION',
                    'Key': 'SERVICE'
                }]
            )
            
            service_costs = {}
            if response['ResultsByTime']:
                for group in response['ResultsByTime'][0]['Groups']:
                    service = group['Keys'][0]
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    if cost > 0.01:  # Filter out tiny costs
                        service_costs[service] = cost
            
            return service_costs
            
        except Exception as e:
            logger.error(f"Failed to get service costs: {str(e)}")
            return {}
    
    def get_top_cost_resources(self, service: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top cost resources, optionally filtered by service"""
        try:
            end = date.today()
            start = end - timedelta(days=7)  # Last 7 days for more recent data
            
            filters = {}
            if service:
                filters = {
                    'Dimensions': {
                        'Key': 'SERVICE',
                        'Values': [service]
                    }
                }
            
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start.isoformat(),
                    'End': end.isoformat()
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost'],
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'USAGE_TYPE'},
                    {'Type': 'DIMENSION', 'Key': 'SERVICE'}
                ],
                Filter=filters if filters else None
            )
            
            # Aggregate costs by resource
            resource_costs = {}
            for day in response['ResultsByTime']:
                for group in day['Groups']:
                    key = f"{group['Keys'][1]}::{group['Keys'][0]}"  # SERVICE::USAGE_TYPE
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    resource_costs[key] = resource_costs.get(key, 0) + cost
            
            # Sort and limit
            top_resources = sorted(
                [{'resource': k, 'cost': v} for k, v in resource_costs.items()],
                key=lambda x: x['cost'],
                reverse=True
            )[:limit]
            
            return top_resources
            
        except Exception as e:
            logger.error(f"Failed to get top cost resources: {str(e)}")
            return []
    
    def detect_cost_anomalies(self, threshold_percent: float = 20) -> List[Dict[str, Any]]:
        """Detect cost spikes and anomalies"""
        anomalies = []
        
        try:
            daily_costs = self.get_daily_costs(14)  # Get 2 weeks of data
            
            if len(daily_costs) < 3:
                return anomalies
            
            # Calculate moving average
            for i in range(3, len(daily_costs)):
                current_cost = daily_costs[i]['cost']
                # Average of previous 3 days
                avg_cost = sum(daily_costs[j]['cost'] for j in range(i-3, i)) / 3
                
                if avg_cost > 0:
                    percent_change = ((current_cost - avg_cost) / avg_cost) * 100
                    
                    if percent_change > threshold_percent:
                        anomalies.append({
                            'date': daily_costs[i]['date'],
                            'cost': current_cost,
                            'expected_cost': avg_cost,
                            'percent_increase': percent_change,
                            'severity': 'high' if percent_change > 50 else 'medium'
                        })
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Failed to detect anomalies: {str(e)}")
            return []
