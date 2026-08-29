"""Crew definition — 3-agent lead generation team."""

from __future__ import annotations

import os

from crewai import LLM, Agent, Crew, Process, Task, TaskOutput
from crewai.project import CrewBase, agent, crew, task

from lead_gen_agents.domain_preflight import JarvisDomainGate, PreflightBlockedError
from lead_gen_agents.state import CompanyResearchBatch
from lead_gen_agents.tools.mcp_factory import get_enrichment_mcps, get_outreach_mcps, get_research_mcps


@CrewBase
class LeadGenCrew:
    """Lead Gen Crew — 3 agents, 5 MCP servers, qualified leads."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self):
        self.gemini_llm = LLM(model="gemini/gemini-2.0-flash", api_key=os.getenv("GEMINI_API_KEY"))
        self.domain_gate = JarvisDomainGate()

    def jarvis_domain_preflight(self, result: TaskOutput) -> tuple[bool, str]:
        """Transform research output to canonical domains or block enrichment."""

        try:
            batch = result.pydantic or CompanyResearchBatch.model_validate_json(result.raw)
            if not isinstance(batch, CompanyResearchBatch):
                batch = CompanyResearchBatch.model_validate(batch)
            verified, _decisions = self.domain_gate.guard_batch(
                batch,
                downstream_consumes_credits=True,
                estimated_downstream_spend_usd=0.11,
            )
            return True, verified.model_dump_json()
        except (ValueError, PreflightBlockedError) as error:
            return False, f"JARVIS_PREFLIGHT_BLOCKED: {error}"

    @agent
    def lead_researcher(self) -> Agent:
        return Agent(config=self.agents_config["lead_researcher"], llm=self.gemini_llm, mcps=get_research_mcps())

    @agent
    def contact_enricher(self) -> Agent:
        return Agent(config=self.agents_config["contact_enricher"], llm=self.gemini_llm, mcps=get_enrichment_mcps())

    @agent
    def outreach_strategist(self) -> Agent:
        return Agent(config=self.agents_config["outreach_strategist"], llm=self.gemini_llm, mcps=get_outreach_mcps())

    @task
    def research_companies(self) -> Task:
        return Task(
            config=self.tasks_config["research_companies"],
            output_pydantic=CompanyResearchBatch,
            guardrail=self.jarvis_domain_preflight,
            guardrail_max_retries=0,
        )

    @task
    def enrich_contacts(self) -> Task:
        return Task(config=self.tasks_config["enrich_contacts"])

    @task
    def create_outreach(self) -> Task:
        return Task(config=self.tasks_config["create_outreach"])

    @crew
    def crew(self) -> Crew:
        return Crew(agents=self.agents, tasks=self.tasks, process=Process.sequential, verbose=True)
