from pathlib import Path


SKILL_PATH = Path(__file__).resolve().parent.parent / ".agents" / "skills" / "skill-using-superpowers" / "SKILL.md"
CODEX_TOOLS_PATH = SKILL_PATH.parent / "references" / "codex-tools.md"


def test_harness_packet_keeps_skill_selection_with_controller() -> None:
    skill = SKILL_PATH.read_text(encoding="utf-8")

    assert "use only its selected skills" in skill
    assert "requires controller reroute and packet regeneration" in skill


def test_codex_tool_map_covers_optional_code_intelligence_tools() -> None:
    tool_map = CODEX_TOOLS_PATH.read_text(encoding="utf-8")

    assert "Semble MCP `search`" in tool_map
    assert "`sg` (ast-grep)" in tool_map
    assert "docs/operating_system/tooling/code-intelligence-tools.md" in tool_map
