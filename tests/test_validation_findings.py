from __future__ import annotations

from scripts.validation_findings import (
    ValidationFinding,
    has_blocking_findings,
    severity_for,
)


def test_finding_exposes_stable_code_and_legacy_category() -> None:
    finding = ValidationFinding("planning_metadata_error", "old.md", "missing field")

    assert finding.code == "planning_metadata_error"
    assert finding.category == finding.code
    assert finding.severity == "error"


def test_unrelated_completed_metadata_is_warning() -> None:
    assert (
        severity_for(
            "planning_metadata_error",
            status="completed",
            selected=False,
            consumed_by_current_work=False,
        )
        == "warning"
    )


def test_selected_completed_work_remains_blocking() -> None:
    assert (
        severity_for(
            "planning_reference_error",
            status="completed",
            selected=True,
            consumed_by_current_work=True,
        )
        == "error"
    )


def test_warning_only_findings_do_not_block() -> None:
    findings = [ValidationFinding("planning_metadata_error", "old.md", "legacy", "warning")]

    assert not has_blocking_findings(findings)


def test_selected_cosmetic_template_history_stays_warning() -> None:
    assert (
        severity_for(
            "template_selection_missing",
            status="completed",
            selected=True,
            consumed_by_current_work=True,
        )
        == "warning"
    )


def test_safety_codes_remain_blocking_without_message_inspection() -> None:
    assert (
        severity_for(
            "planning_authority_invalid",
            status="completed",
            selected=False,
            consumed_by_current_work=False,
        )
        == "error"
    )
