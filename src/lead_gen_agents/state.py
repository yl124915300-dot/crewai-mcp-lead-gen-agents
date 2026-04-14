"""Pydantic state models for the lead generation flow."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CompanyProfile(BaseModel):
    """A target company profile."""

    name: str = ""
    domain: str = ""
    industry: str = ""
    employee_count: str = ""
    revenue_estimate: str = ""
    funding_stage: str = ""
    total_funding: str = ""
    headquarters: str = ""
    founded_year: str = ""
    tech_stack: list[str] = Field(default_factory=list)
    recent_news: list[str] = Field(default_factory=list)
    linkedin_url: str = ""
    fit_score: str = ""
    fit_reasoning: str = ""


class ContactProfile(BaseModel):
    """An enriched decision-maker contact."""

    full_name: str = ""
    title: str = ""
    email: str = ""
    email_confidence: str = ""
    linkedin_url: str = ""
    company: str = ""
    seniority: str = ""
    department: str = ""
    location: str = ""


class OutreachMessage(BaseModel):
    """A personalized outreach message for a lead."""

    contact_name: str = ""
    company_name: str = ""
    subject_line: str = ""
    email_body: str = ""
    personalization_hook: str = ""
    call_to_action: str = ""


class LeadGenFlowState(BaseModel):
    """Full state for the lead generation pipeline."""

    # Input — Ideal Customer Profile
    target_industry: str = ""
    target_role: str = ""
    target_company_size: str = ""
    product_description: str = ""
    value_proposition: str = ""

    # Phase 1 — Company Research
    companies: list[CompanyProfile] = Field(default_factory=list)
    research_raw: str = ""

    # Phase 2 — Contact Enrichment
    contacts: list[ContactProfile] = Field(default_factory=list)
    enrichment_raw: str = ""

    # Phase 3 — Outreach
    outreach_messages: list[OutreachMessage] = Field(default_factory=list)
    report_markdown: str = ""

    # Metadata
    is_complete: bool = False
    output_path: str = ""
