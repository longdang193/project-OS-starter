from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "scripts" / "validate_template_required_sections.py"
VALIDATOR_SPEC = importlib.util.spec_from_file_location("template_validator", VALIDATOR_PATH)
assert VALIDATOR_SPEC and VALIDATOR_SPEC.loader
VALIDATOR = importlib.util.module_from_spec(VALIDATOR_SPEC)
sys.modules[VALIDATOR_SPEC.name] = VALIDATOR
VALIDATOR_SPEC.loader.exec_module(VALIDATOR)


SKILL_PATH = ROOT / ".agents" / "skills" / "skill-wayfinding" / "SKILL.md"
TEMPLATE_PATH = ROOT / "docs" / "operating_system" / "templates" / "wayfinding-map-template.md"
DISPATCH_PATH = ROOT / "docs" / "operating_system" / "planning" / "planning-dispatch.md"
GOVERNANCE_PATH = ROOT / "docs" / "operating_system" / "governance" / "repo-governance.md"


def test_wayfinding_skill_defines_narrow_manual_gate_and_boundaries() -> None:
    assert SKILL_PATH.exists(), "skill-wayfinding must exist"
    content = SKILL_PATH.read_text(encoding="utf-8")

    assert content.startswith("---\nname: skill-wayfinding\n")
    assert "Use only when the user explicitly invokes wayfinding" in content
    for phrase in (
        "known destination",
        "materially unresolved dependent decisions",
        "multi-session",
        "one named lead controller",
        "questions, not build tasks",
        "never writes code",
        "canonical truth",
        "skill-spec-drafting",
        "skill-writing-plans",
        "superseded",
    ):
        assert phrase in content, phrase


def test_wayfinding_map_template_is_discoverable() -> None:
    assert TEMPLATE_PATH.exists(), "wayfinding map template must exist"
    rules, findings = VALIDATOR.discover_template_rules(ROOT)

    assert findings == []
    rule = next(rule for rule in rules if rule.template_id == "wayfinding-map")
    assert "docs/superpowers/plans/wayfinding/*/map.md" in rule.target_globs
    assert set(rule.required_sections) == {
        "Destination",
        "Entry Gate Evidence",
        "Write Control",
        "Decision Frontier",
        "Decisions Settled",
        "Not Yet Specified",
        "Out of Scope",
        "Canonical Promotion And Handoff",
        "Closure And Supersession",
    }


def test_complete_wayfinding_map_passes_and_missing_closure_fails(tmp_path: Path) -> None:
    assert TEMPLATE_PATH.exists(), "wayfinding map template must exist"
    rules, findings = VALIDATOR.discover_template_rules(ROOT)
    assert findings == []
    rule = next(rule for rule in rules if rule.template_id == "wayfinding-map")

    map_path = tmp_path / "docs" / "superpowers" / "plans" / "wayfinding" / "demo" / "map.md"
    map_path.parent.mkdir(parents=True)
    map_path.write_text(
        """---
template_id: wayfinding-map
---
# Wayfinding Map

## Destination
Starter-kit publication flow.

## Entry Gate Evidence
User invoked wayfinding; destination is known; dependent decisions span sessions.

## Write Control
One named lead controller writes this map; other sessions return read-only findings.

## Decision Frontier
| ID | Question | Dependencies | State | Decision-work owner |
|---|---|---|---|---|
| D1 | Which source is canonical? | none | open | lead controller |

## Decisions Settled
None yet.

## Not Yet Specified
No approved behavior is canonical here.

## Out of Scope
Code, build tasks, estimates, and implementation tickets.

## Canonical Promotion And Handoff
Promote approved decisions once through skill-spec-drafting, then hand to skill-writing-plans.

## Closure And Supersession
Close only after frontier is empty; supersede old maps with one linked successor.
""",
        encoding="utf-8",
    )
    issues = VALIDATOR.validate_documents(tmp_path, [rule], require_template_selection=True)
    assert issues == []

    incomplete = map_path.read_text(encoding="utf-8").replace(
        "## Closure And Supersession\nClose only after frontier is empty; supersede old maps with one linked successor.\n",
        "",
    )
    map_path.write_text(incomplete, encoding="utf-8")
    issues = VALIDATOR.validate_documents(tmp_path, [rule], require_template_selection=True)
    assert any(issue.category == "template_section_missing" for issue in issues)


def test_wayfinding_has_one_dispatch_route_and_one_ownership_statement() -> None:
    dispatch = DISPATCH_PATH.read_text(encoding="utf-8")
    governance = GOVERNANCE_PATH.read_text(encoding="utf-8")

    assert "skill-wayfinding" in dispatch
    assert "Wayfinding maps own only provisional decision frontiers" in governance
