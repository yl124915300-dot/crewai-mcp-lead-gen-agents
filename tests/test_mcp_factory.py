import pytest

from lead_gen_agents.tools.mcp_factory import get_research_mcps, validate_environment

ENV_NAMES = [
    "VINKIUS_APOLLOIO_MCP_URL",
    "VINKIUS_CRUNCHBASE_MCP_URL",
    "VINKIUS_HUNTER_MCP_URL",
    "VINKIUS_LINKEDIN_MCP_URL",
    "VINKIUS_EXA_MCP_URL",
]


def test_partial_group_is_not_ready(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fixture-not-a-real-key")
    for key in ENV_NAMES:
        monkeypatch.setenv(key, "https://edge.vinkius.com/test-token/mcp")
    monkeypatch.delenv("VINKIUS_CRUNCHBASE_MCP_URL")
    assert not validate_environment()
    with pytest.raises(ValueError, match="VINKIUS_CRUNCHBASE"):
        get_research_mcps()


def test_all_configured_is_not_connection_verification(monkeypatch, capsys):
    monkeypatch.setenv("GEMINI_API_KEY", "fixture-not-a-real-key")
    for key in ENV_NAMES:
        monkeypatch.setenv(key, "https://edge.vinkius.com/test-token/mcp")
    assert validate_environment()
    assert len(get_research_mcps()) == 2
    assert "connectivity unverified" in capsys.readouterr().out
