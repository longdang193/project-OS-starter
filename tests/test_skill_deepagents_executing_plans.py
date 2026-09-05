from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def test_deepagents_mcp_escalation_stays_controller_mediated() -> None:
    skill = (ROOT / ".agents" / "skills" / "skill-deepagents-executing-plans" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    runtime = (ROOT / "docs" / "operating_system" / "runtime" / "runtime-surfaces.md").read_text(
        encoding="utf-8"
    )

    for text in (
        "Classify each required MCP capability as pre-dispatch or mid-task.",
        "DeepAgents may use MCP only when launcher receives explicit `--mcp-select`",
        "return `NEEDS_CONTEXT` with missing capability",
        "retries same plan task.",
        "CoS does not advance the task ledger from `NEEDS_CONTEXT`.",
    ):
        assert text in skill

    assert "MCP escalation is controller-mediated" in runtime
