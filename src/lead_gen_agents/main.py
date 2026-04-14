"""CLI entry point for Lead Gen Agents."""

from __future__ import annotations
from pathlib import Path
import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from lead_gen_agents import __version__

_PROJECT_ROOT = Path(__file__).parent.parent.parent
load_dotenv(_PROJECT_ROOT / ".env")

console = Console()
app = typer.Typer(name="lead-gen", help="AI agent crew that generates qualified B2B lead lists.", add_completion=False)


@app.command()
def prospect(
    industry: str = typer.Argument(..., help="Target industry (e.g., 'FinTech')"),
    role: str = typer.Argument(..., help="Target decision-maker role (e.g., 'VP of Engineering')"),
    size: str = typer.Option("50-500", "--size", "-s", help="Company size range (e.g., '50-500')"),
    product: str = typer.Option("", "--product", "-p", help="Your product/service description"),
    value_prop: str = typer.Option("", "--value", "-v", help="Your value proposition"),
):
    """Generate a qualified lead list with enriched contacts and outreach templates."""
    from lead_gen_agents.flow import LeadGenFlow
    from lead_gen_agents.state import LeadGenFlowState
    from lead_gen_agents.tools.mcp_factory import validate_environment

    if not validate_environment():
        raise typer.Exit(code=1)

    flow = LeadGenFlow()
    flow.state = LeadGenFlowState(
        target_industry=industry,
        target_role=role,
        target_company_size=size,
        product_description=product or f"a solution for {industry} companies",
        value_proposition=value_prop or f"helping {industry} teams scale faster",
    )

    try:
        flow.kickoff()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted.[/yellow]")
        raise typer.Exit(code=130)
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        raise typer.Exit(code=1)

    if flow.state.is_complete:
        console.print(f"\n[bold green]Done. Lead list: {flow.state.output_path}[/bold green]")


@app.command()
def validate():
    """Validate your environment configuration."""
    from lead_gen_agents.tools.mcp_factory import validate_environment
    if validate_environment():
        console.print("\n[bold green]Environment is ready.[/bold green]")
    else:
        raise typer.Exit(code=1)


@app.command()
def info():
    """Show project information."""
    console.print(Panel(
        f"[bold]CrewAI MCP Lead Gen Agents[/bold] v{__version__}\n\n"
        f"AI agent crew that generates qualified B2B lead lists\n"
        f"with enriched contacts and personalized outreach.\n\n"
        f"[dim]Powered by CrewAI + Vinkius AI Gateway + Google Gemini[/dim]",
        border_style="blue",
    ))
    table = Table(title="Agent Pipeline", show_header=True, header_style="bold")
    table.add_column("Phase", style="bold")
    table.add_column("Agent", style="cyan")
    table.add_column("MCP Servers", style="green")
    table.add_row("1", "Lead Researcher", "Apollo.io, Crunchbase")
    table.add_row("2", "Contact Enricher", "Hunter, LinkedIn")
    table.add_row("3", "Outreach Strategist", "Exa AI")
    console.print(table)


if __name__ == "__main__":
    app()
