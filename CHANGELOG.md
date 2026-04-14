# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2026-04-14

### Added

- Three-agent CrewAI pipeline: Lead Researcher, Contact Enricher, Outreach Strategist
- Integration with 5 MCP servers via [Vinkius AI Gateway](https://vinkius.com):
  - [apolloio-mcp](https://vinkius.com/en/apps/apolloio-mcp) — company prospecting
  - [crunchbase-mcp](https://vinkius.com/en/apps/crunchbase-mcp) — funding and company data
  - [hunter-mcp](https://vinkius.com/en/apps/hunter-mcp) — email discovery and verification
  - [linkedin-mcp](https://vinkius.com/en/apps/linkedin-mcp) — professional profiles
  - [exa-ai-mcp](https://vinkius.com/en/apps/exa-ai-mcp) — company signals and news
- ICP-based prospecting CLI with `--size`, `--product`, `--value` flags
- Personalized outreach templates with company-specific hooks
- Google Gemini 2.0 Flash (free tier compatible)
