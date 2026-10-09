import pytest

from scripts.project_os_runtime.secretary_receipts import (
    ReceiptValidationError,
    sanitize_receipt,
    validate_live_receipt,
)


def receipt(**overrides):
    value = {
        "schema": "project-os.secretary-live-receipt.v1",
        "status": "READY",
        "task_id": "task-1",
        "plan_revision": "plan-1",
        "attempt_id": "attempt-1",
        "run_id": "run-1",
        "provider": "9router",
        "model": "combo-high",
        "timestamps": {"entry_at": "2026-10-09T10:00:00Z", "exit_at": "2026-10-09T10:00:01Z"},
        "completion": {"observed": True, "operation": "secretary_smoke"},
        "provenance": {
            "source_type": "runtime",
            "producer": "secretary-live-runtime",
            "source_ref": "launcher:attempt-1",
            "observed": True,
        },
        "metrics": {
            "cos_turns": 1,
            "secretary_turns": 1,
            "human_interventions": 0,
            "token_usage": None,
            "cost": None,
        },
        "outcomes": {
            "publication": "success",
            "settlement": "observed",
            "acceptance": "accepted",
        },
    }
    value.update(overrides)
    return value


def test_validate_accepts_observed_runtime_receipt() -> None:
    result = validate_live_receipt(receipt(), expected={"attempt_id": "attempt-1"})
    assert result["status"] == "READY"
    assert result["provenance"]["source_type"] == "runtime"


@pytest.mark.parametrize(
    "change",
    [
        {"schema": "project-os.secretary-live-receipt.v99"},
        {"provenance": {"source_type": "deterministic-fake", "observed": True}},
        {"completion": {"observed": False, "operation": "secretary_smoke"}},
        {"attempt_id": "caller-attempt"},
    ],
)
def test_validate_rejects_unsupported_or_untrusted_receipts(change) -> None:
    with pytest.raises(ReceiptValidationError):
        validate_live_receipt(receipt(**change), expected={"attempt_id": "attempt-1"})


def test_sanitize_receipt_drops_credentials_prompts_and_raw_transport() -> None:
    safe = sanitize_receipt(
        receipt(
            api_key="secret",
            prompt="private prompt",
            raw_transport_body="private body",
            error="token=secret",
        )
    )
    assert "api_key" not in safe
    assert "prompt" not in safe
    assert "raw_transport_body" not in safe
    assert "error" not in safe
    assert safe["run_id"] == "run-1"
    assert safe["metrics"]["secretary_turns"] == 1
