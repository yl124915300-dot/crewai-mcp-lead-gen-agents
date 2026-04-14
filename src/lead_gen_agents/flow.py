"""Flow orchestration — lead generation pipeline."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from crewai.flow.flow import Flow, listen, start
from rich.console import Console
from rich.panel import Panel

from lead_gen_agents.crew import LeadGenCrew
from lead_gen_agents.state import LeadGenFlowState

console = Console()
OUTPUT_DIR = Path(__file__).parent.parent.parent / "output"


class LeadGenFlow(Flow[LeadGenFlowState]):
    """Orchestrates the 3-phase lead generation pipeline."""

    @start()
    def initialize(self):
        console.print(Panel(
            f"[bold green]Starting Lead Generation[/bold green]\n\n"
            f"  Industry: [bold]{self.state.target_industry}[/bold]\n"
            f"  Target Role: [bold]{self.state.target_role}[/bold]\n"
            f"  Company Size: [bold]{self.state.target_company_size}[/bold]\n\n"
            f"  [dim]Using CrewAI + Vinkius AI Gateway + Google Gemini[/dim]",
            title="[bold]Lead Gen Agents[/bold]", border_style="green",
        ))

    @listen(initialize)
    def run_lead_crew(self):
        console.print("\n[bold yellow]Launching crew...[/bold yellow]\n")
        result = LeadGenCrew().crew().kickoff(inputs={
            "target_industry": self.state.target_industry,
            "target_role": self.state.target_role,
            "target_company_size": self.state.target_company_size,
            "product_description": self.state.product_description,
            "value_proposition": self.state.value_proposition,
        })
        self.state.report_markdown = result.raw
        self.state.research_raw = str(result.tasks_output[0]) if len(result.tasks_output) > 0 else ""
        self.state.enrichment_raw = str(result.tasks_output[1]) if len(result.tasks_output) > 1 else ""

    @listen(run_lead_crew)
    def export_report(self):
        slug = re.sub(r"[^a-z0-9]+", "-", self.state.target_industry.lower()).strip("-")
        role_slug = re.sub(r"[^a-z0-9]+", "-", self.state.target_role.lower()).strip("-")
        filename = f"{slug}-{role_slug}-leads.md"
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_path = OUTPUT_DIR / filename

        report = (
            f"---\ntitle: \"{self.state.target_industry} Lead List — {self.state.target_role}\"\n"
            f"industry: \"{self.state.target_industry}\"\ntarget_role: \"{self.state.target_role}\"\n"
            f"generated: \"{datetime.now().isoformat()}\"\n"
            f"generator: crewai-mcp-lead-gen-agents\nmcps_used: 5\n"
            f"llm: gemini-2.0-flash\n---\n\n{self.state.report_markdown}"
        )

        output_path.write_text(report, encoding="utf-8")
        self.state.output_path = str(output_path)
        self.state.is_complete = True

        console.print(Panel(
            f"[bold green]Lead list generated successfully.[/bold green]\n\n"
            f"  File: [bold]{output_path}[/bold]\n"
            f"  Agents: 3 | MCP Servers: 5\n"
            f"  Powered by Google Gemini + Vinkius AI Gateway",
            title="[bold]Output[/bold]", border_style="green",
        ))
