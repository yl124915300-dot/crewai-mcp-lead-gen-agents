"""MCP Server Factory — builds MCP URL lists from environment variables."""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from rich.console import Console

console = Console()

_CONFIG_DIR = Path(__file__).parent.parent / "config"
_MCP_REGISTRY = _CONFIG_DIR / "mcp_servers.yaml"


def _load_registry() -> dict:
    with open(_MCP_REGISTRY) as f:
        return yaml.safe_load(f)


def _get_mcp_urls(group: str) -> list[str]:
    registry = _load_registry()
    servers = registry.get(group, [])
    urls = []
    for server in servers:
        env_var = server["env_var"]
        url = os.getenv(env_var)
        if not url or "REPLACE_ME" in url:
            console.print(f"  [yellow]! {server['name']}:[/yellow] [dim]{env_var} not configured[/dim]")
            continue
        urls.append(url)
        console.print(f"  [green]+ {server['name']}:[/green] [dim]connected[/dim]")
    return urls


def get_research_mcps() -> list[str]:
    """Apollo.io, Crunchbase."""
    console.print("\n[bold blue]Loading Research MCP Servers...[/bold blue]")
    return _get_mcp_urls("research")


def get_enrichment_mcps() -> list[str]:
    """Hunter, LinkedIn."""
    console.print("\n[bold magenta]Loading Enrichment MCP Servers...[/bold magenta]")
    return _get_mcp_urls("enrichment")


def get_outreach_mcps() -> list[str]:
    """Exa AI."""
    console.print("\n[bold cyan]Loading Outreach MCP Servers...[/bold cyan]")
    return _get_mcp_urls("outreach")


def validate_environment() -> bool:
    console.print("\n[bold]Validating environment...[/bold]\n")
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key or gemini_key == "your_gemini_api_key_here":
        console.print("[red]x GEMINI_API_KEY not configured[/red]")
        return False
    console.print("[green]+ GEMINI_API_KEY configured[/green]")

    registry = _load_registry()
    all_ok = True
    for group_name, servers in registry.items():
        configured = sum(1 for s in servers if os.getenv(s["env_var"], "") and "REPLACE_ME" not in os.getenv(s["env_var"], ""))
        if configured == 0:
            console.print(f"[red]x No MCP servers for '{group_name}'[/red]")
            all_ok = False
        else:
            console.print(f"[green]+ {group_name}: {configured}/{len(servers)} configured[/green]")
    if not all_ok:
        console.print("\n[yellow]Copy .env.example to .env and add your Vinkius MCP URLs.[/yellow]")
    return all_ok
