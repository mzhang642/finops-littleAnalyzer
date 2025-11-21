"""
Demo script to showcase the analyzer to beta users
"""
import asyncio
from app.services.aws_cost_explorer import AWSCostExplorer
from app.services.aws_ec2_analyzer import EC2Analyzer
from app.services.aws_storage_analyzer import StorageAnalyzer
from app.utils.encryption import encrypt_credentials
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

async def run_demo(access_key: str, secret_key: str):
    """Run a demo analysis and display results"""
    
    console.print("\n[bold blue]íº€ FinOps Analyzer - Beta Demo[/bold blue]\n")
    
    # Encrypt credentials
    encrypted = encrypt_credentials({
        'access_key': access_key,
        'secret_key': secret_key
    })
    
    with console.status("[bold green]Connecting to AWS...[/bold green]"):
        # Cost Analysis
        cost_explorer = AWSCostExplorer(encrypted)
        current_spend = cost_explorer.get_current_month_spend()
        service_costs = cost_explorer.get_service_costs(30)
        anomalies = cost_explorer.detect_cost_anomalies()
    
    # Display Current Spend
    console.print(Panel(
        f"[bold]Current Month Spend:[/bold] ${current_spend.get('total', 0):,.2f}",
        title="í²° Cost Overview",
        border_style="green"
    ))
    
    # Service Breakdown Table
    if service_costs:
        table = Table(title="Service Breakdown (Top 5)")
        table.add_column("Service", style="cyan")
        table.add_column("Monthly Cost", style="green")
        
        for service, cost in list(service_costs.items())[:5]:
            table.add_row(service, f"${cost:,.2f}")
        
        console.print(table)
    
    with console.status("[bold green]Analyzing EC2 instances...[/bold green]"):
        # EC2 Analysis
        ec2_analyzer = EC2Analyzer(encrypted)
        instances = ec2_analyzer.get_all_instances()
        opportunities = ec2_analyzer.find_optimization_opportunities()
    
    # Display EC2 Results
    console.print(f"\n[bold]EC2 Analysis:[/bold]")
    console.print(f"  â€¢ Total Instances: {len(instances)}")
    console.print(f"  â€¢ Optimization Opportunities: {len(opportunities)}")
    
    total_savings = sum(o.get('monthly_savings', 0) for o in opportunities)
    console.print(f"  â€¢ [bold green]Potential Savings: ${total_savings:,.2f}/month[/bold green]")
    
    # Top Recommendations
    if opportunities:
        console.print("\n[bold]Top 3 Recommendations:[/bold]")
        for i, opp in enumerate(opportunities[:3], 1):
            console.print(f"\n  {i}. [yellow]{opp['reason']}[/yellow]")
            console.print(f"     Savings: [green]${opp.get('monthly_savings', 0):,.2f}/month[/green]")
            console.print(f"     Action: {opp['action']}")
            console.print(f"     Risk: {opp.get('risk', 'medium')}")
    
    with console.status("[bold green]Analyzing storage...[/bold green]"):
        # Storage Analysis
        storage_analyzer = StorageAnalyzer(encrypted)
        ebs_results = storage_analyzer.analyze_ebs_volumes()
        s3_results = storage_analyzer.analyze_s3_buckets()
    
    # Display Storage Results
    console.print(f"\n[bold]Storage Analysis:[/bold]")
    console.print(f"  â€¢ EBS Volumes: {ebs_results['total_volumes']}")
    console.print(f"  â€¢ Unattached Volumes: {len(ebs_results['unattached_volumes'])}")
    console.print(f"  â€¢ S3 Buckets: {s3_results['total_buckets']}")
    
    storage_savings = sum(r['monthly_savings'] for r in ebs_results['recommendations'])
    if storage_savings > 0:
        console.print(f"  â€¢ [bold green]Storage Savings: ${storage_savings:,.2f}/month[/bold green]")
    
    # Summary Panel
    total_potential_savings = total_savings + storage_savings
    savings_percentage = (total_potential_savings / current_spend.get('total', 1)) * 100
    
    console.print("\n")
    console.print(Panel(
        f"[bold green]âœ¨ Total Potential Savings: ${total_potential_savings:,.2f}/month[/bold green]\n"
        f"[bold]í³Š Savings Percentage: {savings_percentage:.1f}%[/bold]\n"
        f"[bold]í²Ž Annual Savings: ${total_potential_savings * 12:,.2f}[/bold]",
        title="í¾¯ Analysis Summary",
        border_style="bold green"
    ))
    
    console.print("\n[bold blue]Ready to save? Sign up for beta access at finopsanalyzer.com/beta[/bold blue]\n")

if __name__ == "__main__":
    print("FinOps Analyzer - Beta Demo")
    print("-" * 40)
    
    access_key = input("Enter AWS Access Key: ")
    secret_key = input("Enter AWS Secret Key: ")
    
    asyncio.run(run_demo(access_key, secret_key))
