import pytest

from lead_gen_agents.config_policy import gateway_url_valid


@pytest.mark.parametrize(
    "url",
    [
        "",
        "http://edge.vinkius.com/token/mcp",
        "https://localhost/token/mcp",
        "https://127.0.0.1/token/mcp",
        "https://edge.vinkius.com.evil.test/token/mcp",
        "https://user:secret@edge.vinkius.com/token/mcp",
        "https://edge.vinkius.com:bad/token/mcp",
        "https://edge.vinkius.com/token/mcp?key=secret",
        "https://edge.vinkius.com/vk_live_REPLACE_ME/mcp",
    ],
)
def test_invalid_gateway_urls(url):
    assert not gateway_url_valid(url)


def test_documented_gateway():
    assert gateway_url_valid("https://edge.vinkius.com/test-token/mcp")
