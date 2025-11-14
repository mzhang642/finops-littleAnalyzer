"""
Test AWS integration with your own account
"""
import asyncio
import os
from dotenv import load_dotenv

from app.services.aws_cost_explorer import AWSCostExplorer
from app.services.aws_ec2_analyzer import EC2Analyzer
from app.services.aws_storage_analyzer import StorageAnalyzer
from app.utils.encryption import encrypt_credentials

load_dotenv()


async def test_your_account():
    """Test with your AWS account"""
    
    # Use your AWS credentials
    access_key = input("Enter your AWS Access Key: ")
    secret_key = input("Enter your AWS Secret Key: ")
    
    # Encrypt credentials
    encrypted = encrypt_credentials({
        'access_key': access_key,
        'secret_key': secret_key
    })
    
    print("\n=== Testing AWS Connection ===")
    
    # Test Cost Explorer
    print("\n1. Cost Analysis:")
    cost_explorer = AWSCostExplorer(encrypted)
    
    current_spend = cost_explorer.get_current_month_spend()
    print(f"   Current month spend: ${current_spend.get('total', 0):.2f}")
    
    service_costs = cost_explorer.get_service_costs(30)
    print(f"   Services used: {len(service_costs)}")
    for service, cost in list(service_costs.items())[:5]:
        print(f"     - {service}: ${cost:.2f}")
    
    anomalies = cost_explorer.detect_cost_anomalies()
    print(f"   Cost anomalies detected: {len(anomalies)}")
    
    # Test EC2 Analysis
    print("\n2. EC2 Analysis:")
    ec2_analyzer = EC2Analyzer(encrypted)
    
    instances = ec2_analyzer.get_all_instances()
    print(f"   Total instances: {len(instances)}")
    
    opportunities = ec2_analyzer.find_optimization_opportunities()
    print(f"   Optimization opportunities: {len(opportunities)}")
    
    total_savings = sum(o.get('monthly_savings', 0) for o in opportunities)
    print(f"   Potential monthly savings: ${total_savings:.2f}")
    
    # Test Storage Analysis
    print("\n3. Storage Analysis:")
    storage_analyzer = StorageAnalyzer(encrypted)
    
    ebs_results = storage_analyzer.analyze_ebs_volumes()
    print(f"   EBS volumes: {ebs_results['total_volumes']}")
    print(f"   Unattached volumes: {len(ebs_results['unattached_volumes'])}")
    
    s3_results = storage_analyzer.analyze_s3_buckets()
    print(f"   S3 buckets: {s3_results['total_buckets']}")
    
    # Summary
    print("\n=== ANALYSIS SUMMARY ===")
    print(f"Total Monthly Spend: ${current_spend.get('total', 0):.2f}")
    print(f"Potential Savings: ${total_savings:.2f}")
    if current_spend.get('total', 0) > 0:
        savings_percent = (total_savings / current_spend['total']) * 100
        print(f"Savings Percentage: {savings_percent:.1f}%")
    
    print("\n✅ AWS Integration Test Complete!")
    

if __name__ == "__main__":
    asyncio.run(test_your_account())
