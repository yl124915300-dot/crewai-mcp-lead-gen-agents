# Contributing to CrewAI MCP Lead Gen Agents

Thank you for your interest in contributing.

## How to Contribute

1. Fork and branch from `main`
2. `pip install -e ".[dev]"`
3. `ruff check src/ && ruff format src/`
4. Use conventional commits
5. Open a Pull Request

## Adding a CRM Integration

1. Add the CRM MCP server to `config/mcp_servers.yaml`
2. Add the env var to `.env.example`
3. Extend the outreach agent to push leads to the CRM
4. Update `README.md` with the new integration

---

Thank you for helping improve this project.
