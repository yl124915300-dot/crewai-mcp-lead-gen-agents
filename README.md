# CrewAI MCP Lead Gen Agents

## Evidence-gated existing-business operations

Commercial `lead-gen prospect` now requires `--evidence-case /private/path/case.json`
before importing CrewAI or contacting a paid service. Unknown operating eligibility,
fee authority, payout eligibility, buyer mandate, stale demand or missing scoped
consent blocks the command. All five documented gateway URLs must be configured;
configuration alone is not a successful connection test.

The independent operator cycle uses only Python's standard library:

```sh
PYTHONPATH=src python -m lead_gen_agents.operating_cycle /private/path/case.json --output /private/path/result.json
PYTHONPATH=src python -m pytest tests
```

The module records manager/acquisition/delivery/review decisions and exposes a
SQLite reservation/readback ledger. The current AI operator performs the reasoning
and connector actions; this is not an unattended four-model agent deployment.
It does not send email, submit referrals, charge cards, sign agreements or verify
legal eligibility. Evidence hashes detect changed snapshots, not falsified claims.
Keep case snapshots and customer materials outside this public repository.
See [the operating skill](skills/existing-business-cycle/SKILL.md) for scoped use.

Case JSON contains `case_id`, `business_id`, `mode` (LIVE/REPLAY/SIMULATION), `goal`,
`evidence` (map of ID to relative `path`, `sha256`, timezone-aware `observed_at`,
`mode`, `reviewed`), `demand` (`requested_at`, `explicit_request`, `unresolved`), `gates`
(`operating_eligibility`, `fee_authority`, `payout_eligibility`, `buyer_mandate`),
`consent` (`authorized`, `scope`) and `proposed_disclosures`. Each claim has `value`
(explicit boolean or unknown) and `evidence` (IDs). Claims require reviewed
evidence from the last seven days; LIVE cases cannot rely on test/replay evidence.
`requested_at` is the original request time, not its latest fetch time; re-reading
an expired lead does not make it fresh.
An operator must review the original source's meaning before setting a claim.
Optional `payments` require an order ID, positive integer `amount_minor`, currency,
`is_test=false`, `status=PAYMENT_VERIFIED` and a sourced `provider_readback` claim.
Do not treat a referral bounty advertised by an employer as money receivable.

**A multi-agent system that generates qualified B2B lead lists with enriched contact data and personalized outreach templates — powered by CrewAI, Google Gemini, and 5 production MCP servers from the [Vinkius AI Gateway](https://vinkius.com).**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)

---

## The Problem with Manual Prospecting

Sales teams spend an average of 21% of their day researching prospects. An SDR manually checking LinkedIn, searching Crunchbase for funding data, running Hunter.io for email addresses, and then writing a personalized email for each lead — that is 2+ hours per 10 leads, and the quality degrades with fatigue.

**This project automates the entire pipeline.** Three AI agents handle company research, contact enrichment, and outreach personalization in a single run. You define your Ideal Customer Profile, and the system delivers a qualified lead list with verified emails and ready-to-send outreach templates.

The key differentiator is that the agents access live data through the [Model Context Protocol (MCP)](https://modelcontextprotocol.io) — they query Apollo.io for firmographics, Crunchbase for funding data, Hunter for verified emails, LinkedIn for professional profiles, and Exa AI for recent company signals. No stale data. No guessing.

---

## How It Works

### Phase 1 — Company Research and Qualification

The first agent acts as a senior sales researcher. It uses two MCP servers:

- **Apollo.io** for company search, firmographics, employee count, revenue estimates, and technology stack detection
- **Crunchbase** for funding rounds, investors, total funding raised, and acquisition history

Given your ICP (industry, company size, product fit), it finds 10 qualified companies, scores each for fit from 1-10, and provides reasoning for every score.

### Phase 2 — Contact Enrichment

The second agent finds decision-makers at each qualified company. It uses two MCP servers:

- **Hunter** for email discovery and verification with confidence scores
- **LinkedIn** for professional profiles, current titles, seniority levels, and department information

It targets the specific role you define (VP of Engineering, Head of Product, CFO) and prioritizes email accuracy over speed.

### Phase 3 — Personalized Outreach

The third agent creates outreach templates. It uses one MCP server:

- **Exa AI** for semantic search of recent company news, blog posts, and hiring signals

Each email references something specific about the prospect's company — a recent funding round, a hiring trend, a technology adoption — connecting it to your value proposition. Emails are kept under 120 words with a single clear call to action.

---

## Only 5 MCP Servers Required

This project is intentionally lean. You need only 5 MCP servers to run the full pipeline:

| MCP Server | Agent | Purpose |
|---|---|---|
| [apolloio-mcp](https://vinkius.com/en/apps/apolloio-mcp) | Lead Researcher | Company search, firmographics, tech stack |
| [crunchbase-mcp](https://vinkius.com/en/apps/crunchbase-mcp) | Lead Researcher | Funding data, investors, company profiles |
| [hunter-mcp](https://vinkius.com/en/apps/hunter-mcp) | Contact Enricher | Email discovery and verification |
| [linkedin-mcp](https://vinkius.com/en/apps/linkedin-mcp) | Contact Enricher | Professional profiles, job titles |
| [exa-ai-mcp](https://vinkius.com/en/apps/exa-ai-mcp) | Outreach Strategist | Company news, signals, personalization data |

All hosted on the [Vinkius AI Gateway](https://vinkius.com). Deploy each one in under a minute and get your SSE endpoint URL.

### Want More Data Sources?

The [Vinkius AI Gateway](https://vinkius.com) offers additional sales intelligence MCP servers you can add with a one-line config change:

- [hubspot-crm-full-mcp](https://vinkius.com/en/apps/hubspot-crm-full-mcp) — sync leads directly to HubSpot
- [salesforce-sales-cloud-mcp](https://vinkius.com/en/apps/salesforce-sales-cloud-mcp) — push to Salesforce pipeline
- [pipedrive-leads-mcp](https://vinkius.com/en/apps/pipedrive-leads-mcp) — create deals in Pipedrive
- [lusha-mcp](https://vinkius.com/en/apps/lusha-mcp) — additional contact enrichment
- [zoominfo-mcp](https://vinkius.com/en/apps/zoominfo-mcp) — enterprise-grade intent data
- [instantly-mcp](https://vinkius.com/en/apps/instantly-mcp) — automated email sequences
- [lemlist-mcp](https://vinkius.com/en/apps/lemlist-mcp) — multi-channel outreach campaigns
- [similarweb-analytics-mcp](https://vinkius.com/en/apps/similarweb-analytics-mcp) — website traffic intelligence

Browse the full catalog of **2,600+ production-ready MCP servers** at [vinkius.com/en/categories](https://vinkius.com/en/categories).

---

## Getting Started

### Prerequisites

- Python 3.11+
- A [Google Gemini API key](https://aistudio.google.com/apikey) (free tier is sufficient)
- 5 MCP server endpoints from the [Vinkius AI Gateway](https://vinkius.com)

### Installation

```bash
git clone https://github.com/vinkius-labs/crewai-mcp-lead-gen-agents.git
cd crewai-mcp-lead-gen-agents

python -m venv .venv
source .venv/bin/activate    # Linux/macOS
# .venv\Scripts\activate     # Windows

pip install -e .
```

### Configuration

```bash
cp .env.example .env
```

Add your Gemini API key and 5 Vinkius MCP URLs.

### Usage

```bash
# Validate configuration
lead-gen validate

# Generate leads for FinTech VP of Engineering
lead-gen prospect "FinTech" "VP of Engineering" \
  --size "50-500" \
  --product "API monitoring platform" \
  --value "reduce API downtime by 90%"

# Generate leads for SaaS Head of Product
lead-gen prospect "SaaS" "Head of Product" \
  --size "100-1000" \
  --product "user analytics platform" \
  --value "increase feature adoption by 3x"
```

---

## Generated Output

The system produces a markdown report containing:

| Section | Content |
|---|---|
| Company Profiles | 10 qualified companies with firmographics, fit scores, and reasoning |
| Decision-Maker Contacts | Verified emails, LinkedIn profiles, titles, seniority |
| Outreach Templates | 10 personalized emails with subject lines and CTAs |
| Summary Metrics | Total leads, average fit score, email coverage rate |

---

## Technical Details

- **Framework:** [CrewAI](https://crewai.com) with Flows and `@CrewBase` decorators
- **LLM:** Google Gemini 2.0 Flash (free tier compatible)
- **State:** Pydantic models — `CompanyProfile`, `ContactProfile`, `OutreachMessage`
- **MCP:** Native CrewAI `mcps=` field with SSE transport to [Vinkius AI Gateway](https://vinkius.com)
- **CLI:** Typer with ICP-based arguments

---

## FAQ

### What is MCP?

The Model Context Protocol is an open standard for connecting AI systems to external tools. See [modelcontextprotocol.io](https://modelcontextprotocol.io).

### Can I push leads directly to my CRM?

Yes. Add the [HubSpot](https://vinkius.com/en/apps/hubspot-crm-full-mcp), [Salesforce](https://vinkius.com/en/apps/salesforce-sales-cloud-mcp), or [Pipedrive](https://vinkius.com/en/apps/pipedrive-leads-mcp) MCP server and extend the outreach agent to push leads directly.

### Is this GDPR compliant?

This tool discovers publicly available business contact information. However, compliance depends on your jurisdiction and how you use the data. Consult your legal team before using enriched contact data for outbound campaigns.

---

## Contributing

Please read the [Contributing Guide](CONTRIBUTING.md) before submitting a pull request.

## License

MIT — see [LICENSE](LICENSE).

---

Built by [Vinkius Labs](https://vinkius.com) with [CrewAI](https://crewai.com) and the [Vinkius AI Gateway](https://vinkius.com).
