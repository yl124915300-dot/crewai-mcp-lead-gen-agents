from __future__ import annotations

import pytest

from lead_gen_agents.domain_preflight import JarvisDomainGate, PreflightBlockedError
from lead_gen_agents.state import CompanyProfile, CompanyResearchBatch


class FakeTransport:
    def __init__(self, responses=None, error: Exception | None = None):
        self.responses = list(responses or [])
        self.error = error
        self.calls = []

    def post_json(self, url, payload, idempotency_key):
        self.calls.append((url, payload, idempotency_key))
        if self.error:
            raise self.error
        return self.responses.pop(0)


def response(verdict="MATCH", canonical="example.com", safe=True, redirected_from=None):
    return {
        "verdict": verdict,
        "canonical_domain": canonical,
        "redirected_from": redirected_from,
        "confidence": 0.98,
        "evidence": [],
        "checked_at": "2026-08-29T00:00:00Z",
        "safe_for_downstream_enrichment": safe,
    }


def batch(domain="example.com"):
    return CompanyResearchBatch(companies=[CompanyProfile(name="Example", domain=domain)])


def guard(gate, data=None, *, consumes=True, spend=0.0):
    return gate.guard_batch(
        data or batch(),
        downstream_consumes_credits=consumes,
        estimated_downstream_spend_usd=spend,
    )


def test_match_allows_canonical_domain():
    transport = FakeTransport([response()])
    verified, decisions = guard(JarvisDomainGate(transport))
    assert verified.companies[0].domain == "example.com"
    assert decisions[0].verdict == "MATCH"


def test_mismatch_replaces_domain_before_enrichment():
    transport = FakeTransport([response("MISMATCH", "canonical.com")])
    verified, _ = guard(JarvisDomainGate(transport), batch("wrong.com"))
    assert verified.companies[0].domain == "canonical.com"


def test_redirected_domain_is_canonicalized():
    transport = FakeTransport([response("MATCH", "new.example", redirected_from="old.example")])
    verified, decisions = guard(JarvisDomainGate(transport), batch("old.example"))
    assert verified.companies[0].domain == "new.example"
    assert decisions[0].redirected_from == "old.example"


@pytest.mark.parametrize(
    "reply",
    [response("UNCERTAIN", "example.com", False), response("MATCH", "example.com", False)],
)
def test_uncertain_or_unsafe_blocks_downstream(reply):
    with pytest.raises(PreflightBlockedError):
        guard(JarvisDomainGate(FakeTransport([reply])))


def test_transport_failure_fails_closed():
    with pytest.raises(PreflightBlockedError, match="failed closed"):
        guard(JarvisDomainGate(FakeTransport(error=TimeoutError("timeout"))))


def test_idempotent_retry_does_not_pay_twice():
    transport = FakeTransport([response()])
    gate = JarvisDomainGate(transport)
    guard(gate)
    guard(gate)
    assert len(transport.calls) == 1
    assert transport.calls[0][2].startswith("jarvis-domain-preflight-")


def test_preflight_is_skipped_when_no_paid_or_credit_step_follows():
    transport = FakeTransport(error=AssertionError("must not be called"))
    verified, decisions = guard(JarvisDomainGate(transport), consumes=False, spend=0.10)
    assert verified == batch()
    assert decisions == []


def test_spend_above_threshold_triggers_preflight_even_without_credit_flag():
    transport = FakeTransport([response()])
    guard(JarvisDomainGate(transport), consumes=False, spend=0.11)
    assert len(transport.calls) == 1
