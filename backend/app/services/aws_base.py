"""
Base AWS service class with authentication and common methods
"""
import boto3
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging
from botocore.exceptions import ClientError, NoCredentialsError

from app.utils.encryption import decrypt_credentials

logger = logging.getLogger(__name__)


class AWSService:
    """Base class for AWS service integration"""
    
    def __init__(self, encrypted_credentials: str, region: str = 'us-east-1'):
        """Initialize AWS service with encrypted credentials"""
        try:
            # Decrypt credentials
            creds = decrypt_credentials(encrypted_credentials)
            
            # Create session
            self.session = boto3.Session(
                aws_access_key_id=creds['access_key'],
                aws_secret_access_key=creds['secret_key'],
                region_name=region
            )
            
            self.region = region
            self.account_id = self._get_account_id()
            
        except Exception as e:
            logger.error(f"Failed to initialize AWS service: {str(e)}")
            raise
    
    def _get_account_id(self) -> str:
        """Get AWS account ID"""
        try:
            sts = self.session.client('sts')
            return sts.get_caller_identity()['Account']
        except Exception as e:
            logger.error(f"Failed to get account ID: {str(e)}")
            return "unknown"
    
    def test_connection(self) -> Dict[str, Any]:
        """Test AWS connection and permissions"""
        results = {
            'connected': False,
            'account_id': None,
            'permissions': {},
            'errors': []
        }
        
        try:
            # Test STS (basic connectivity)
            sts = self.session.client('sts')
            identity = sts.get_caller_identity()
            results['connected'] = True
            results['account_id'] = identity['Account']
            
            # Test required permissions
            permission_tests = [
                ('ec2:DescribeInstances', self._test_ec2_permissions),
                ('ce:GetCostAndUsage', self._test_cost_explorer_permissions),
                ('cloudwatch:GetMetricStatistics', self._test_cloudwatch_permissions),
                ('rds:DescribeDBInstances', self._test_rds_permissions),
            ]
            
            for permission, test_func in permission_tests:
                try:
                    test_func()
                    results['permissions'][permission] = True
                except ClientError as e:
                    results['permissions'][permission] = False
                    results['errors'].append(f"{permission}: {str(e)}")
                    
        except Exception as e:
            results['errors'].append(str(e))
            
        return results
    
    def _test_ec2_permissions(self):
        """Test EC2 permissions"""
        ec2 = self.session.client('ec2')
        ec2.describe_instances(MaxResults=1)
    
    def _test_cost_explorer_permissions(self):
        """Test Cost Explorer permissions"""
        ce = self.session.client('ce')
        end = datetime.now().date()
        start = end - timedelta(days=1)
        ce.get_cost_and_usage(
            TimePeriod={'Start': start.isoformat(), 'End': end.isoformat()},
            Granularity='DAILY',
            Metrics=['UnblendedCost']
        )
    
    def _test_cloudwatch_permissions(self):
        """Test CloudWatch permissions"""
        cw = self.session.client('cloudwatch')
        cw.list_metrics(MaxResults=1)
    
    def _test_rds_permissions(self):
        """Test RDS permissions"""
        rds = self.session.client('rds')
        rds.describe_db_instances(MaxRecords=20)
