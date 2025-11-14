"""
EC2 instance analyzer for finding optimization opportunities
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

from app.services.aws_base import AWSService

logger = logging.getLogger(__name__)


class EC2Analyzer(AWSService):
    """Analyze EC2 instances for cost optimization"""
    
    def __init__(self, encrypted_credentials: str, region: str = 'us-east-1'):
        super().__init__(encrypted_credentials, region)
        self.ec2_client = self.session.client('ec2', region_name=region)
        self.cw_client = self.session.client('cloudwatch', region_name=region)
        
        # Simplified pricing (in production, use AWS Pricing API)
        self.instance_hourly_pricing = {
            't2.micro': 0.0116, 't2.small': 0.023, 't2.medium': 0.0464,
            't2.large': 0.0928, 't2.xlarge': 0.1856, 't2.2xlarge': 0.3712,
            't3.micro': 0.0104, 't3.small': 0.0208, 't3.medium': 0.0416,
            't3.large': 0.0832, 't3.xlarge': 0.1664, 't3.2xlarge': 0.3328,
            'm5.large': 0.096, 'm5.xlarge': 0.192, 'm5.2xlarge': 0.384,
            'c5.large': 0.085, 'c5.xlarge': 0.17, 'c5.2xlarge': 0.34,
        }
    
    def get_all_instances(self) -> List[Dict[str, Any]]:
        """Get all EC2 instances in the region"""
        instances = []
        
        try:
            paginator = self.ec2_client.get_paginator('describe_instances')
            
            for page in paginator.paginate():
                for reservation in page['Reservations']:
                    for instance in reservation['Instances']:
                        instances.append(self._parse_instance(instance))
            
            logger.info(f"Found {len(instances)} EC2 instances")
            return instances
            
        except Exception as e:
            logger.error(f"Failed to get instances: {str(e)}")
            return []
    
    def _parse_instance(self, instance: Dict) -> Dict[str, Any]:
        """Parse instance data into our format"""
        instance_type = instance.get('InstanceType', 'unknown')
        state = instance['State']['Name']
        
        # Calculate monthly cost
        hourly_cost = self.instance_hourly_pricing.get(instance_type, 0.1)  # Default $0.1/hour
        monthly_cost = hourly_cost * 730  # Average hours per month
        
        # Get name tag
        name = 'Unnamed'
        for tag in instance.get('Tags', []):
            if tag['Key'] == 'Name':
                name = tag['Value']
                break
        
        return {
            'instance_id': instance['InstanceId'],
            'name': name,
            'type': instance_type,
            'state': state,
            'launch_time': instance.get('LaunchTime'),
            'region': self.region,
            'availability_zone': instance.get('Placement', {}).get('AvailabilityZone'),
            'tags': {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])},
            'hourly_cost': hourly_cost,
            'monthly_cost': monthly_cost,
            'vpc_id': instance.get('VpcId'),
            'subnet_id': instance.get('SubnetId'),
            'public_ip': instance.get('PublicIpAddress'),
            'private_ip': instance.get('PrivateIpAddress')
        }
    
    def analyze_instance_utilization(self, instance_id: str, days: int = 7) -> Dict[str, Any]:
        """Analyze CPU utilization for an instance"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days)
            
            response = self.cw_client.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName='CPUUtilization',
                Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,  # 1 hour intervals
                Statistics=['Average', 'Maximum']
            )
            
            if not response['Datapoints']:
                return {'average': 0, 'maximum': 0, 'data_points': 0}
            
            datapoints = response['Datapoints']
            avg_utilization = sum(dp['Average'] for dp in datapoints) / len(datapoints)
            max_utilization = max(dp['Maximum'] for dp in datapoints)
            
            return {
                'average': round(avg_utilization, 2),
                'maximum': round(max_utilization, 2),
                'data_points': len(datapoints)
            }
            
        except Exception as e:
            logger.error(f"Failed to get utilization for {instance_id}: {str(e)}")
            return {'average': None, 'maximum': None, 'error': str(e)}
    
    def find_optimization_opportunities(self) -> List[Dict[str, Any]]:
        """Find EC2 optimization opportunities"""
        recommendations = []
        
        try:
            instances = self.get_all_instances()
            
            for instance in instances:
                # Check stopped instances
                if instance['state'] == 'stopped':
                    if instance.get('launch_time'):
                        stopped_days = (datetime.now(instance['launch_time'].tzinfo) - instance['launch_time']).days
                        if stopped_days > 7:
                            recommendations.append({
                                'type': 'terminate_stopped',
                                'resource_id': instance['instance_id'],
                                'resource_name': instance['name'],
                                'reason': f"Instance stopped for {stopped_days} days",
                                'monthly_savings': instance['monthly_cost'],
                                'risk': 'low',
                                'action': 'Terminate instance or create AMI backup',
                                'confidence': 0.9
                            })
                
                # Check running instances for low utilization
                elif instance['state'] == 'running':
                    utilization = self.analyze_instance_utilization(instance['instance_id'])
                    
                    if utilization.get('average') is not None and utilization['average'] < 10:
                        recommendations.append({
                            'type': 'low_utilization',
                            'resource_id': instance['instance_id'],
                            'resource_name': instance['name'],
                            'reason': f"Average CPU utilization only {utilization['average']}%",
                            'current_type': instance['type'],
                            'monthly_savings': instance['monthly_cost'] * 0.5,  # Assume 50% savings
                            'risk': 'medium',
                            'action': 'Downsize or terminate instance',
                            'confidence': 0.7,
                            'metrics': utilization
                        })
                    
                    # Check for instances without tags (poor governance)
                    if len(instance.get('tags', {})) < 2:
                        recommendations.append({
                            'type': 'governance',
                            'resource_id': instance['instance_id'],
                            'resource_name': instance['name'],
                            'reason': 'Instance lacks proper tagging',
                            'risk': 'none',
                            'action': 'Add tags: Environment, Owner, Project',
                            'confidence': 1.0
                        })
            
            logger.info(f"Found {len(recommendations)} optimization opportunities")
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to find opportunities: {str(e)}")
            return []
