"""Evidence gates for an operator's four-role cycle; no network or payment executor.

The AI operator supplies sourced observations. These deterministic checks cannot
establish legal eligibility, authenticate a source, or replace an independent review.
Private case bundles and the durable action database stay outside the repository.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path


def timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamps require a timezone")
    return parsed


def verify_evidence(case: dict, root: Path) -> dict:
    """Validate bounded local snapshots before using their operator-reviewed claims."""
    root = root.resolve()
    verified = {}
    for key, item in case["evidence"].items():
        path = (root / item["path"]).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError(f"invalid evidence path: {key}")
        if hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError(f"evidence digest mismatch: {key}")
        if item["mode"] not in {"LIVE", "REPLAY", "SIMULATION"}:
            raise ValueError(f"invalid evidence mode: {key}")
        timestamp(item["observed_at"])
        verified[key] = item
    return verified


def evaluate(case: dict, root: Path, now: datetime | None = None) -> dict:
    now = now or datetime.now(UTC)
    evidence = verify_evidence(case, root)
    live = case.get("mode") == "LIVE"

    def supported(claim: dict | None, expected=True, max_age_days=7) -> bool:
        claim = claim or {}
        refs = claim.get("evidence", [])
        if claim.get("value") is not expected or not refs:
            return False
        for ref in refs:
            item = evidence.get(ref)
            if not item or item.get("reviewed") is not True:
                return False
            age = now - timestamp(item["observed_at"])
            if age < timedelta(0) or age > timedelta(days=max_age_days):
                return False
            if live and item["mode"] != "LIVE":
                return False
        return True

    demand = case.get("demand", {})
    try:
        request_age = now - timestamp(demand["requested_at"])
        request_fresh = timedelta(0) <= request_age <= timedelta(days=7)
    except (KeyError, TypeError, ValueError):
        request_fresh = False
    demand_ok = request_fresh and all(supported(demand.get(k)) for k in ("explicit_request", "unresolved"))
    gates = {
        k: supported(case.get("gates", {}).get(k))
        for k in (
            "operating_eligibility",
            "fee_authority",
            "payout_eligibility",
            "buyer_mandate",
        )
    }
    consent = case.get("consent", {})
    consent_ok = supported(consent.get("authorized"))
    scoped = consent_ok and set(case.get("proposed_disclosures", [])).issubset(consent.get("scope", []))
    commercial = live and demand_ok and scoped and all(gates.values())
    blockers = [k for k, passed in gates.items() if not passed]
    if not demand_ok:
        blockers.append("fresh_unresolved_demand")
    if not scoped:
        blockers.append("disclosure_consent")
    if not live:
        blockers.append("non_live_case")

    verified_payments = []
    for payment in case.get("payments", []):
        if (
            live
            and payment.get("is_test") is False
            and payment.get("status") == "PAYMENT_VERIFIED"
            and supported(payment.get("provider_readback"))
            and payment.get("order_id")
            and isinstance(payment.get("amount_minor"), int)
            and not isinstance(payment.get("amount_minor"), bool)
            and payment["amount_minor"] > 0
            and isinstance(payment.get("currency"), str)
            and len(payment["currency"]) == 3
        ):
            verified_payments.append(payment)

    return {
        "case_id": case["case_id"],
        "business_id": case["business_id"],
        "mode": case["mode"],
        "observed_at": now.isoformat(),
        "manager": {
            "goal": case["goal"],
            "blockers": blockers,
            "next_action": "REVIEW_COMMERCIAL_ACTION" if commercial else "RESOLVE_EVIDENCE_GAPS",
            "failure_hypotheses": case.get("failure_hypotheses", []),
        },
        "acquisition": {
            "fresh_unresolved_request": demand_ok,
            "payer_demand_verified": gates["buyer_mandate"],
            "lead_is_not_order": True,
        },
        "delivery": {
            "internal_review_allowed": live and demand_ok,
            "formal_submission_allowed": commercial,
            "disclosure_scope_valid": scoped,
            "artifact": case.get("delivery_artifact"),
        },
        "review": {
            "gates": gates,
            "evidence_digests": {k: v["sha256"] for k, v in evidence.items()},
            "verified_paid_order_ids": sorted({p["order_id"] for p in verified_payments}),
            "costs": case.get("costs", {"total": None, "reason": "UNKNOWN"}),
            "net_profit": None,
            "bank_balance": "NOT_READ",
        },
    }


class ActionLedger:
    """Reserve before dispatch. Any uncertain attempt blocks automatic retries.

    Unique business/action/recipient/source_message prevents duplicates across runs.
    SQLite transactions also prevent two concurrent operators reserving the same action.
    A Gmail SENT readback establishes submission, never delivery or acceptance.
    """

    def __init__(self, path: Path):
        self.db = sqlite3.connect(path)
        self.db.execute("""CREATE TABLE IF NOT EXISTS actions (
            action_key TEXT PRIMARY KEY, status TEXT NOT NULL, provider_id TEXT,
            evidence_sha256 TEXT, created_at TEXT NOT NULL)""")
        self.db.commit()

    def reserve(self, business: str, action: str, recipient: str, source_message: str) -> str:
        if not all(x.strip() for x in (business, action, recipient, source_message)):
            raise ValueError("business, action, recipient and source_message required")
        key = hashlib.sha256(
            json.dumps(
                [business, action, recipient.strip().casefold(), source_message],
                separators=(",", ":"),
            ).encode()
        ).hexdigest()
        with self.db:
            self.db.execute(
                "INSERT INTO actions VALUES (?, 'RESERVED', NULL, NULL, ?)", (key, datetime.now(UTC).isoformat())
            )
        return key

    def record(self, key: str, status: str, provider_id: str | None = None, readback: bytes | None = None) -> None:
        if status not in {"SENT_READBACK", "FAILED", "UNKNOWN"}:
            raise ValueError("invalid terminal action status")
        if status == "SENT_READBACK":
            if not provider_id or not readback:
                raise ValueError("provider ID and readback required")
            receipt = json.loads(readback)
            if receipt.get("id") != provider_id or "SENT" not in receipt.get("label_ids", []):
                raise ValueError("receipt must match provider ID and SENT label")
        with self.db:
            cursor = self.db.execute(
                "UPDATE actions SET status=?, provider_id=?, evidence_sha256=? "
                "WHERE action_key=? AND status='RESERVED'",
                (status, provider_id, hashlib.sha256(readback).hexdigest() if readback else None, key),
            )
            if cursor.rowcount != 1:
                raise ValueError("missing reservation or already finalized")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = evaluate(json.loads(args.case.read_text()), args.case.parent)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
