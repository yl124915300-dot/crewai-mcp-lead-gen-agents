"""Validate the documented gateway contract without exposing tokenized URLs."""

from urllib.parse import urlsplit


def gateway_url_valid(value: str) -> bool:
    try:
        url = urlsplit(value)
        return bool(
            url.scheme == "https"
            and url.hostname == "edge.vinkius.com"
            and not url.username
            and not url.password
            and url.port in {None, 443}
            and not url.query
            and not url.fragment
            and url.path.endswith("/mcp")
            and len(url.path.strip("/").split("/")) == 2
            and "REPLACE_ME" not in value
        )
    except ValueError:
        return False
