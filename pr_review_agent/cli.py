"""
Command-line interface for PR Review Agent
"""
import click
import json
import os
import sys
from typing import Dict, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from .core.config import Config

# Optional imports for full functionality
try:
    from .core.reviewer import PRReviewer
    FULL_FEATURES_AVAILABLE = True
except ImportError as e:
    PRReviewer = None
    FULL_FEATURES_AVAILABLE = False
    MISSING_DEPENDENCIES_MSG = str(e)


console = Console()


def require_full_features():
    """Check if full features are available, exit with helpful message if not."""
    if not FULL_FEATURES_AVAILABLE:
        console.print("[red]❌ Full features not available[/red]")
        console.print("[yellow]Missing dependencies. Install with:[/yellow]")
        console.print("[cyan]pipx install pr-review-agent[full][/cyan]")
        console.print("[cyan]# or[/cyan]")
        console.print("[cyan]pip install 'pr-review-agent[full]'[/cyan]")
        sys.exit(1)


def get_reviewer(config_path: Optional[str] = None):
    """Get a PRReviewer instance, checking dependencies first."""
    require_full_features()
    return PRReviewer(config_path)


@click.group()
@click.option('--config', '-c', help='Path to configuration file')
@click.pass_context
def cli(ctx, config):
    """AI-powered Pull Request Review Agent
    
    Review pull requests across GitHub, GitLab, and Bitbucket with intelligent
    feedback and automated code quality analysis.
    """
    ctx.ensure_object(dict)
    ctx.obj['config_path'] = config


@cli.command()
@click.option('--server', '-s', required=True, help='Git server name (from config)')
@click.option('--repo', '-r', required=True, help='Repository (owner/repo)')
@click.option('--pr', '-p', required=True, type=int, help='Pull request number')
@click.option('--post/--no-post', default=True, help='Post review to server')
@click.option('--output', '-o', help='Save results to JSON file')
@click.pass_context
def review(ctx, server, repo, pr, post, output):
    """Review a pull request"""
    console.print(f"[bold blue]🤖 Starting PR Review[/bold blue]")
    console.print(f"Server: {server}")
    console.print(f"Repository: {repo}")
    console.print(f"PR: #{pr}")
    console.print()
    
    try:
        reviewer = get_reviewer(ctx.obj.get('config_path'))
        
        with console.status("[bold green]Analyzing pull request..."):
            result = reviewer.review_pr(server, repo, pr, post_review=post)
        
        if result['success']:
            _display_review_results(result)
            
            if output:
                _save_results_to_file(result, output)
                console.print(f"\n[green]✅ Results saved to {output}[/green]")
        else:
            console.print(f"[red]❌ Error: {result['error']}[/red]")
            sys.exit(1)
            
    except Exception as e:
        console.print(f"[red]❌ Unexpected error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('files', nargs=-1, required=True)
@click.option('--output', '-o', help='Save results to JSON file')
@click.pass_context
def analyze(ctx, files, output):
    """Analyze local files"""
    console.print(f"[bold blue]🔍 Analyzing {len(files)} file(s)[/bold blue]")
    
    try:
        reviewer = get_reviewer(ctx.obj.get('config_path'))
        
        # Read files
        file_contents = {}
        for file_path in files:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_contents[file_path] = f.read()
            else:
                console.print(f"[yellow]⚠️  File not found: {file_path}[/yellow]")
        
        if not file_contents:
            console.print("[red]❌ No valid files to analyze[/red]")
            sys.exit(1)
        
        with console.status("[bold green]Analyzing files..."):
            result = reviewer.analyze_files(file_contents)
        
        if result['success']:
            _display_analysis_results(result)
            
            if output:
                _save_results_to_file(result, output)
                console.print(f"\n[green]✅ Results saved to {output}[/green]")
        else:
            console.print(f"[red]❌ Error: {result['error']}[/red]")
            sys.exit(1)
            
    except Exception as e:
        console.print(f"[red]❌ Unexpected error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--server', '-s', help='Check specific server')
@click.pass_context
def status(ctx, server):
    """Check server connection status"""
    console.print("[bold blue]🔗 Checking server status[/bold blue]")
    
    # Try to use basic config first
    try:
        config = Config(ctx.obj.get('config_path'))
        servers = list(config.servers.keys()) if config.servers else []
        
        if server and server not in servers:
            console.print(f"[red]❌ Server '{server}' not found in configuration[/red]")
            return
        
        if server:
            servers = [server]
        
        if not servers:
            console.print("[yellow]⚠️  No servers configured[/yellow]")
            servers = ["github", "gitlab", "bitbucket"]  # Show defaults
        
        table = Table(title="Server Status")
        table.add_column("Server", style="cyan")
        table.add_column("Type", style="magenta") 
        table.add_column("URL", style="blue")
        table.add_column("Status", style="green")
        
        for server_name in servers:
            if server_name in config.servers:
                server_config = config.servers[server_name]
                table.add_row(
                    server_name,
                    server_config.type,
                    server_config.base_url,
                    "🔧 Configured"
                )
            else:
                table.add_row(
                    server_name,
                    "Unknown",
                    "Unknown", 
                    "❌ Not configured"
                )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]❌ Error checking status: {e}[/red]")
        console.print("[dim]Use 'pr-review init' to create a configuration file[/dim]")


@cli.command()
@click.option('--name', '-n', required=True, help='Server configuration name')
@click.option('--type', '-t', required=True, 
              type=click.Choice(['github', 'gitlab', 'bitbucket']),
              help='Server type')
@click.option('--url', '-u', required=True, help='Server base URL')
@click.option('--token', required=True, help='Authentication token')
@click.pass_context
def configure(ctx, name, type, url, token):
    """Configure a git server"""
    console.print(f"[bold blue]⚙️  Configuring server: {name}[/bold blue]")
    
    try:
        reviewer = get_reviewer(ctx.obj.get('config_path'))
        
        success = reviewer.configure_server(name, type, url, token)
        
        if success:
            console.print(f"[green]✅ Server '{name}' configured successfully[/green]")
            
            # Test connection
            with console.status("Testing connection..."):
                status_info = reviewer.get_server_status(name)
            
            if status_info['connected']:
                console.print("[green]✅ Connection test successful[/green]")
            else:
                console.print("[yellow]⚠️  Connection test failed[/yellow]")
        else:
            console.print("[red]❌ Failed to configure server[/red]")
            sys.exit(1)
            
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.pass_context
def init(ctx):
    """Initialize configuration file"""
    config_path = ctx.obj.get('config_path') or 'pr_review_config.yaml'
    
    console.print(f"[bold blue]🔧 Initializing configuration[/bold blue]")
    
    try:
        config = Config(config_path)
        console.print(f"[green]✅ Configuration file created: {config_path}[/green]")
        
        console.print("\n[yellow]📝 Next steps:[/yellow]")
        console.print("1. Edit the configuration file to add your API tokens")
        console.print("2. Configure servers with: pr-review configure")
        console.print("3. Test connections with: pr-review status")
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.pass_context  
def list_servers(ctx):
    """List supported server types"""
    console.print("[bold blue]📋 Supported Git Servers[/bold blue]")
    
    # Show supported server types
    supported_servers = ["github", "gitlab", "bitbucket"]
    console.print("\nSupported server types:")
    for server_type in supported_servers:
        console.print(f"• {server_type}")
    
    console.print("\n[dim]Use 'pr-review configure' to set up a server[/dim]")


@cli.command()
@click.pass_context
def version(ctx):
    """Show version information"""
    from . import __version__
    console.print(f"[bold blue]PR Review Agent v{__version__}[/bold blue]")


def _display_review_results(result: Dict[str, Any]):
    """Display review results in a formatted way"""
    score_breakdown = result['score_breakdown']
    ai_feedback = result['ai_feedback']
    
    # Display score
    score_color = "green" if score_breakdown.overall_score >= 80 else "yellow" if score_breakdown.overall_score >= 60 else "red"
    
    console.print(Panel(
        f"[bold {score_color}]Grade: {score_breakdown.grade} ({score_breakdown.overall_score:.1f}/100)[/bold {score_color}]",
        title="🎯 Quality Score",
        border_style=score_color
    ))
    
    # Display category scores
    table = Table(title="📊 Category Breakdown")
    table.add_column("Category", style="cyan")
    table.add_column("Score", style="magenta")
    table.add_column("Status", style="green")
    
    for category, score in score_breakdown.category_scores.items():
        status = "✅ Good" if score >= 80 else "⚠️  Fair" if score >= 60 else "❌ Poor"
        table.add_row(
            category.replace('_', ' ').title(),
            f"{score:.1f}/100",
            status
        )
    
    console.print(table)
    
    # Display summary
    console.print(Panel(
        score_breakdown.summary,
        title="📝 Summary",
        border_style="blue"
    ))
    
    # Display issues count
    metrics = score_breakdown.metrics
    issues_text = f"Total Issues: {metrics['total_issues']}\n"
    issues_text += f"• Errors: {metrics['issues_by_severity']['error']}\n"
    issues_text += f"• Warnings: {metrics['issues_by_severity']['warning']}\n"
    issues_text += f"• Info: {metrics['issues_by_severity']['info']}"
    
    console.print(Panel(
        issues_text,
        title="🔍 Issues Found",
        border_style="yellow"
    ))


def _display_analysis_results(result: Dict[str, Any]):
    """Display analysis results in a formatted way"""
    summary_metrics = result['summary_metrics']
    
    # Display summary
    console.print(Panel(
        f"Files Analyzed: {summary_metrics['files_analyzed']}\n"
        f"Total Issues: {summary_metrics['total_issues']}\n"
        f"Quality Score: {summary_metrics['quality_score']:.1f}/100",
        title="📊 Analysis Summary",
        border_style="blue"
    ))
    
    # Display issues by severity
    table = Table(title="🔍 Issues by Severity")
    table.add_column("Severity", style="cyan")
    table.add_column("Count", style="magenta")
    
    for severity, count in summary_metrics['issues_by_severity'].items():
        table.add_row(severity.title(), str(count))
    
    console.print(table)
    
    # Display issues by category
    if summary_metrics['issues_by_category']:
        table = Table(title="📋 Issues by Category")
        table.add_column("Category", style="cyan")
        table.add_column("Count", style="magenta")
        
        for category, count in summary_metrics['issues_by_category'].items():
            table.add_row(category.title(), str(count))
        
        console.print(table)


def _save_results_to_file(result: Dict[str, Any], filename: str):
    """Save results to JSON file"""
    # Convert result to JSON-serializable format
    json_result = _make_json_serializable(result)
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(json_result, f, indent=2, default=str)


def _make_json_serializable(obj):
    """Convert objects to JSON-serializable format"""
    if hasattr(obj, '__dict__'):
        return {key: _make_json_serializable(value) for key, value in obj.__dict__.items()}
    elif isinstance(obj, dict):
        return {key: _make_json_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [_make_json_serializable(item) for item in obj]
    else:
        return obj


def main():
    """Main entry point"""
    cli()


if __name__ == '__main__':
    main()
