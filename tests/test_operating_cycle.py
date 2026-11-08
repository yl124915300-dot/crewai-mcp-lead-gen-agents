import hashlib
import json
import sqlite3
from datetime import UTC, datetime

import pytest

from lead_gen_agents.operating_cycle import ActionLedger, evaluate

NOW = datetime(2026, 11, 8, 8, 0, tzinfo=UTC)


@pytest.fixture
def case(tmp_path):
    raw = b"reviewed fixture, not a real customer"
    (tmp_path / "source.txt").write_bytes(raw)
    claim = {"value": True, "evidence": ["source"]}
    return {
        "case_id": "test",
        "business_id": "test-business",
        "mode": "LIVE",
        "goal": "test gates",
        "evidence": {
            "source": {
                "path": "source.txt",
                "sha256": hashlib.sha256(raw).hexdigest(),
                "observed_at": NOW.isoformat(),
                "mode": "LIVE",
                "reviewed": True,
            }
        },
        "demand": {"requested_at": NOW.isoformat(), "explicit_request": claim, "unresolved": claim},
        "gates": {k: claim for k in ["operating_eligibility", "fee_authority", "payout_eligibility", "buyer_mandate"]},
        "consent": {"authorized": claim, "scope": ["resume"]},
        "proposed_disclosures": ["resume"],
    }


def test_missing_operating_eligibility_blocks_submission(case, tmp_path):
    case["gates"]["operating_eligibility"] = {"value": "UNKNOWN"}
    result = evaluate(case, tmp_path, NOW)
    assert not result["delivery"]["formal_submission_allowed"]
    assert result["delivery"]["internal_review_allowed"]


@pytest.mark.parametrize("field,value", [("mode", "SIMULATION"), ("mode", "REPLAY")])
def test_non_live_never_allows_submission_or_payment(case, tmp_path, field, value):
    case[field] = value
    case["payments"] = [
        {
            "status": "PAYMENT_VERIFIED",
            "is_test": False,
            "order_id": "order-1",
            "amount_minor": 100,
            "currency": "USD",
            "provider_readback": {"value": True, "evidence": ["source"]},
        }
    ]
    result = evaluate(case, tmp_path, NOW)
    assert not result["delivery"]["formal_submission_allowed"]
    assert result["review"]["verified_paid_order_ids"] == []


@pytest.mark.parametrize("change", ["stale", "future", "test", "unreviewed", "hash", "path"])
def test_bad_evidence(case, tmp_path, change):
    item = case["evidence"]["source"]
    if change == "stale":
        item["observed_at"] = "2026-07-27T08:00:00Z"
    if change == "future":
        item["observed_at"] = "2026-11-09T08:00:00Z"
    if change == "test":
        item["mode"] = "SIMULATION"
    if change == "unreviewed":
        item["reviewed"] = False
    if change == "hash":
        item["sha256"] = "tampered"
    if change == "path":
        item["path"] = "../source.txt"
    if change in {"hash", "path"}:
        with pytest.raises(ValueError):
            evaluate(case, tmp_path, NOW)
    else:
        assert not evaluate(case, tmp_path, NOW)["delivery"]["formal_submission_allowed"]


def test_consent_is_scoped(case, tmp_path):
    case["proposed_disclosures"].append("private-email-body")
    assert not evaluate(case, tmp_path, NOW)["delivery"]["formal_submission_allowed"]


def test_boolean_must_be_explicit(case, tmp_path):
    case["demand"]["explicit_request"] = {"value": "true", "evidence": ["source"]}
    assert not evaluate(case, tmp_path, NOW)["acquisition"]["fresh_unresolved_request"]


def test_fresh_fetch_does_not_refresh_old_request(case, tmp_path):
    case["demand"]["requested_at"] = "2026-07-27T08:00:00Z"
    assert not evaluate(case, tmp_path, NOW)["acquisition"]["fresh_unresolved_request"]


def test_paid_order_requires_provider_evidence_and_deduplicates(case, tmp_path):
    payment = {
        "status": "PAYMENT_VERIFIED",
        "is_test": False,
        "order_id": "order-1",
        "amount_minor": 100,
        "currency": "USD",
        "provider_readback": {"value": True, "evidence": ["source"]},
    }
    case["payments"] = [
        payment,
        payment,
        dict(payment, order_id="test", is_test=True),
        dict(payment, order_id="unverified", provider_readback={}),
    ]
    assert evaluate(case, tmp_path, NOW)["review"]["verified_paid_order_ids"] == ["order-1"]


def test_duplicate_reservation_across_runs(tmp_path):
    path = tmp_path / "actions.sqlite3"
    first = ActionLedger(path)
    key = first.reserve("business", "reply", "Candidate@example.com", "gmail-1")
    first.record(key, "UNKNOWN")
    with pytest.raises(sqlite3.IntegrityError):
        ActionLedger(path).reserve("business", "reply", "candidate@example.com", "gmail-1")
    ActionLedger(path).reserve("different-business", "reply", "candidate@example.com", "gmail-1")


def test_receipt_requires_matching_sent_message(tmp_path):
    ledger = ActionLedger(tmp_path / "actions.sqlite3")
    key = ledger.reserve("business", "reply", "candidate@example.com", "gmail-1")
    with pytest.raises(ValueError):
        ledger.record(key, "SENT_READBACK", "gmail-2", b'{"id":"other","label_ids":["SENT"]}')
    ledger.record(key, "SENT_READBACK", "gmail-2", json.dumps({"id": "gmail-2", "label_ids": ["SENT"]}).encode())
    with pytest.raises(ValueError):
        ledger.record(key, "FAILED")
