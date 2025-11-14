"""
Analyze AWS storage services (EBS, S3) for optimization
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
import logging

from app.services.aws_base import AWSService

logger = logging.getLogger(__name__)


class StorageAnalyzer(AWSService):
    """Analyze storage resources for cost optimization"""
    
    def __init__(self, encrypted_credentials: str, region: str = 'us-east-1'):
        super().__init__(encrypted_credentials, region)
        self.ec2_client = self.session.client('ec2', region_name=region)
        self.s3_client = self.session.client('s3')
        self.cw_client = self.session.client('cloudwatch', region_name=region)
    
    def analyze_ebs_volumes(self) -> Dict[str, Any]:
        """Analyze EBS volumes for optimization"""
        results = {
            'total_volumes': 0,
            'total_size_gb': 0,
            'total_monthly_cost': 0,
            'unattached_volumes': [],
            'low_iops_volumes': [],
            'recommendations': []
        }
        
        try:
            response = self.ec2_client.describe_volumes()
            volumes = response['Volumes']
            
            results['total_volumes'] = len(volumes)
            
            for volume in volumes:
                size_gb = volume['Size']
                volume_type = volume['VolumeType']
                state = volume['State']
                
                results['total_size_gb'] += size_gb
                
                # Calculate cost (simplified)
                monthly_cost = self._calculate_ebs_cost(size_gb, volume_type)
                results['total_monthly_cost'] += monthly_cost
                
                # Check for unattached volumes
                if state == 'available':
                    results['unattached_volumes'].append({
                        'volume_id': volume['VolumeId'],
                        'size_gb': size_gb,
                        'type': volume_type,
                        'monthly_cost': monthly_cost,
                        'created': volume['CreateTime']
                    })
                    
                    results['recommendations'].append({
                        'type': 'delete_unattached_volume',
                        'resource_id': volume['VolumeId'],
                        'reason': f'Unattached {size_gb}GB {volume_type} volume',
                        'monthly_savings': monthly_cost,
                        'risk': 'low',
                        'action': 'Snapshot and delete volume',
                        'confidence': 0.95
                    })
                
                # Check for oversized gp2 volumes (should be gp3)
                if volume_type == 'gp2' and size_gb > 100:
                    gp3_cost = self._calculate_ebs_cost(size_gb, 'gp3')
                    savings = monthly_cost - gp3_cost
                    
                    if savings > 5:  # Only recommend if saving > $5/month
                        results['recommendations'].append({
                            'type': 'migrate_to_gp3',
                            'resource_id': volume['VolumeId'],
                            'reason': f'Large gp2 volume ({size_gb}GB) should be gp3',
                            'monthly_savings': savings,
                            'risk': 'low',
                            'action': 'Migrate volume from gp2 to gp3',
                            'confidence': 0.9
                        })
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to analyze EBS volumes: {str(e)}")
            return results
    
    def analyze_s3_buckets(self) -> Dict[str, Any]:
        """Analyze S3 buckets for optimization"""
        results = {
            'total_buckets': 0,
            'total_size_gb': 0,
            'total_monthly_cost': 0,
            'lifecycle_opportunities': [],
            'recommendations': []
        }
        
        try:
            # List all buckets
            response = self.s3_client.list_buckets()
            buckets = response['Buckets']
            results['total_buckets'] = len(buckets)
            
            for bucket in buckets:
                bucket_name = bucket['Name']
                
                try:
                    # Get bucket location
                    location = self.s3_client.get_bucket_location(Bucket=bucket_name)
                    
                    # Get bucket metrics
                    metrics = self._get_s3_metrics(bucket_name)
                    
                    if metrics['size_gb'] > 100:  # Only analyze larger buckets
                        # Check for lifecycle policies
                        try:
                            lifecycle = self.s3_client.get_bucket_lifecycle_configuration(
                                Bucket=bucket_name
                            )
                            has_lifecycle = len(lifecycle.get('Rules', [])) > 0
                        except:
                            has_lifecycle = False
                        
                        if not has_lifecycle and metrics['size_gb'] > 500:
                            results['lifecycle_opportunities'].append(bucket_name)
                            results['recommendations'].append({
                                'type': 's3_lifecycle',
                                'resource_id': bucket_name,
                                'reason': f'Large bucket ({metrics["size_gb"]:.0f}GB) without lifecycle policy',
                                'monthly_savings': metrics['monthly_cost'] * 0.3,  # Assume 30% savings
                                'risk': 'low',
                                'action': 'Add lifecycle policy to move old data to Glacier',
                                'confidence': 0.8
                            })
                    
                    results['total_size_gb'] += metrics['size_gb']
                    results['total_monthly_cost'] += metrics['monthly_cost']
                    
                except Exception as e:
                    logger.warning(f"Could not analyze bucket {bucket_name}: {str(e)}")
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to analyze S3 buckets: {str(e)}")
            return results
    
    def _calculate_ebs_cost(self, size_gb: int, volume_type: str) -> float:
        """Calculate monthly cost for EBS volume"""
        # Simplified pricing (actual prices vary by region)
        pricing = {
            'gp3': 0.08,  # per GB-month
            'gp2': 0.10,
            'io1': 0.125,
            'io2': 0.125,
            'st1': 0.045,
            'sc1': 0.025,
            'standard': 0.05
        }
        
        base_cost = size_gb * pricing.get(volume_type, 0.10)
        
        # Add IOPS costs for io1/io2
        if volume_type in ['io1', 'io2']:
            base_cost += 100 * 0.065  # Assume 100 IOPS at $0.065 per IOPS
        
        return base_cost
    
    def _get_s3_metrics(self, bucket_name: str) -> Dict[str, float]:
        """Get S3 bucket size and cost metrics"""
        try:
            # Get bucket size from CloudWatch
            response = self.cw_client.get_metric_statistics(
                Namespace='AWS/S3',
                MetricName='BucketSizeBytes',
                Dimensions=[
                    {'Name': 'BucketName', 'Value': bucket_name},
                    {'Name': 'StorageType', 'Value': 'StandardStorage'}
                ],
                StartTime=datetime.utcnow() - timedelta(days=2),
                EndTime=datetime.utcnow(),
                Period=86400,  # Daily
                Statistics=['Average']
            )
            
            size_bytes = 0
            if response['Datapoints']:
                size_bytes = response['Datapoints'][-1]['Average']
            
            size_gb = size_bytes / (1024 ** 3)
            
            # Simple cost calculation ($0.023 per GB for first 50TB)
            monthly_cost = size_gb * 0.023
            
            return {
                'size_gb': size_gb,
                'monthly_cost': monthly_cost
            }
            
        except Exception:
            return {'size_gb': 0, 'monthly_cost': 0}
