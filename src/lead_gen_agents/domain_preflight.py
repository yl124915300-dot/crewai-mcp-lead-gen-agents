"""Hard pre-enrichment domain gate backed by Jarvis and x402.

The default transport performs only the unpaid discovery request. It never
returns protected data. A real paid call requires an operator-owned EVM key and
the optional ``x402`` dependency group.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from pydantic import BaseModel, Field

from lead_gen_agents.state import CompanyProfile, CompanyResearchBatch

JARVIS_DOMAIN_VERIFY_URL = "https://jarvis-problem-intake.naijunyu.chatgpt.site/b2b/domain-verify"
MAX_PAYMENT_USD = "0.01"
DEFAULT_SPEND_THRESHOLD_USD = 0.10


class PaymentCapabilityRequiredError(RuntimeError):
    """Raised when Jarvis correctly requests payment but no buyer wallet exists."""


class PreflightBlockedError(RuntimeError):
    """Raised when enrichment must not continue."""


class DomainPreflightResponse(BaseModel):
    verdict: str
    canonical_domain: str
    redirected_from: str | None = None
    confidence: float = 0.0
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    checked_at: str = ""
    safe_for_downstream_enrichment: bool = False


class PaymentTransport(Protocol):
    """Minimal adapter contract for a buyer-funded x402 HTTP client."""

    def post_json(self, url: str, payload: Mapping[str, Any], idempotency_key: str) -> Mapping[str, Any]: ...


class DiscoveryOnlyTransport:
    """Prove the 402 challenge is reachable without bypassing payment."""

    def post_json(self, url: str, payload: Mapping[str, Any], idempotency_key: str) -> Mapping[str, Any]:
        request = Request(
            url,
            data=json.dumps(dict(payload)).encode(),
            headers={"Content-Type": "application/json", "Idempotency-Key": idempotency_key},
            method="POST",
        )
        try:
            with urlopen(request, timeout=30) as response:  # noqa: S310 - fixed HTTPS endpoint
                return json.loads(response.read())
        except HTTPError as error:
            if error.code == 402:
                challenge = error.headers.get("PAYMENT-REQUIRED")
                detail = "standard v2 PAYMENT-REQUIRED challenge received" if challenge else "402 received"
                raise PaymentCapabilityRequiredError(
                    f"Jarvis payment required ({detail}); configure an external x402 buyer wallet"
                ) from error
            raise


class X402EvmTransport:
    """Standard x402 v2 buyer transport with a hard $0.01 per-call cap."""

    def __init__(self, private_key: str):
        try:
            from eth_account import Account
            from x402 import x402ClientSync
            from x402.http.clients import x402_requests
            from x402.mechanisms.evm import EthAccountSigner
            from x402.mechanisms.evm.exact.register import register_exact_evm_client
        except ImportError as error:
            raise RuntimeError('Install the optional buyer adapter with: pip install -e ".[x402]"') from error

        client = x402ClientSync()
        client.set_spend_controls({"max_amount_per_payment": f"${MAX_PAYMENT_USD}"})
        register_exact_evm_client(client, EthAccountSigner(Account.from_key(private_key)))
        self._session = x402_requests(client)

    def post_json(self, url: str, payload: Mapping[str, Any], idempotency_key: str) -> Mapping[str, Any]:
        if url != JARVIS_DOMAIN_VERIFY_URL:
            raise ValueError("x402 transport is restricted to the configured Jarvis endpoint")
        response = self._session.post(
            url,
            json=dict(payload),
            headers={"Idempotency-Key": idempotency_key},
            timeout=60,
        )
        response.raise_for_status()
        return response.json()


def transport_from_environment() -> PaymentTransport:
    """Use only the adopter's wallet; never fall back to a project/internal wallet."""

    private_key = os.getenv("JARVIS_X402_EVM_PRIVATE_KEY", "").strip()
    return X402EvmTransport(private_key) if private_key else DiscoveryOnlyTransport()


@dataclass(frozen=True)
class GateDecision:
    company_name: str
    candidate_domain: str
    canonical_domain: str
    verdict: str
    redirected_from: str | None


class JarvisDomainGate:
    """Deterministic, fail-closed gate placed before credit-consuming enrichment."""

    def __init__(self, transport: PaymentTransport | None = None):
        self._transport = transport or transport_from_environment()
        self._cache: dict[str, DomainPreflightResponse] = {}

    @staticmethod
    def _idempotency_key(company: CompanyProfile, context: str) -> str:
        stable = json.dumps(
            {
                "company_name": company.name.strip().casefold(),
                "candidate_domain": company.domain.strip().casefold(),
                "context": context.strip(),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return "jarvis-domain-preflight-" + hashlib.sha256(stable.encode()).hexdigest()

    def verify(self, company: CompanyProfile, context: str = "") -> tuple[CompanyProfile, GateDecision]:
        if not company.name.strip() or not company.domain.strip():
            raise PreflightBlockedError("company_name and candidate_domain are required before enrichment")

        key = self._idempotency_key(company, context)
        if key not in self._cache:
            raw = self._transport.post_json(
                JARVIS_DOMAIN_VERIFY_URL,
                {
                    "company_name": company.name,
                    "candidate_domain": company.domain,
                    "context": context,
                },
                key,
            )
            self._cache[key] = DomainPreflightResponse.model_validate(raw)

        result = self._cache[key]
        verdict = result.verdict.upper()
        if verdict == "UNCERTAIN":
            raise PreflightBlockedError(f"UNCERTAIN domain for {company.name}; pause or request approval")
        if verdict not in {"MATCH", "MISMATCH"}:
            raise PreflightBlockedError(f"unsupported Jarvis verdict for {company.name}: {result.verdict}")
        if not result.safe_for_downstream_enrichment or not result.canonical_domain.strip():
            raise PreflightBlockedError(f"Jarvis did not mark {company.name} safe for downstream enrichment")

        canonical = result.canonical_domain.strip().lower()
        verified = company.model_copy(update={"domain": canonical})
        return verified, GateDecision(
            company_name=company.name,
            candidate_domain=company.domain,
            canonical_domain=canonical,
            verdict=verdict,
            redirected_from=result.redirected_from,
        )

    def guard_batch(
        self,
        batch: CompanyResearchBatch,
        *,
        downstream_consumes_credits: bool,
        estimated_downstream_spend_usd: float,
        context: str = "lead contact enrichment",
    ) -> tuple[CompanyResearchBatch, list[GateDecision]]:
        should_preflight = downstream_consumes_credits or (estimated_downstream_spend_usd > DEFAULT_SPEND_THRESHOLD_USD)
        if not should_preflight:
            return batch, []

        verified: list[CompanyProfile] = []
        decisions: list[GateDecision] = []
        try:
            for company in batch.companies:
                canonical_company, decision = self.verify(company, context)
                verified.append(canonical_company)
                decisions.append(decision)
        except Exception as error:
            if isinstance(error, PreflightBlockedError):
                raise
            raise PreflightBlockedError(f"Jarvis preflight failed closed: {error}") from error
        return CompanyResearchBatch(companies=verified), decisions
