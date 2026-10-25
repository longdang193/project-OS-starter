from __future__ import annotations

import pytest

from project_os_test_paths import add_runtime_import_roots

add_runtime_import_roots()

from scripts.mcp_selection import (
    McpSelectionError,
    load_mcp_capabilities,
    mcp_server_configuration_digest,
    normalize_mcp_selection,
)


def test_load_mcp_capabilities_merges_global_project_and_runtime_sources() -> None:
    capabilities = load_mcp_capabilities(
        {
            "mcp_servers": {
                "global": {"tools": {"read": {}}},
                "overridden": {"tools": {"old": {}}},
                "disabled": {"enabled": False},
            }
        },
        {
            "mcp_servers": {
                "project": {"tools": {"inspect": {}}},
                "overridden": {"tools": {"new": {}}},
            }
        },
        {"mcp_servers": {"runtime": {"tools": {"probe": {}}}}},
    )

    assert capabilities == {
        "global": ("read",),
        "overridden": ("new",),
        "project": ("inspect",),
        "runtime": ("probe",),
    }


def test_mcp_server_configuration_digest_changes_when_command_changes() -> None:
    first = mcp_server_configuration_digest(
        {"mcp_servers": {"context7": {"command": "context7"}}}
    )
    second = mcp_server_configuration_digest(
        {"mcp_servers": {"context7": {"command": "context7-v2"}}}
    )

    assert first != second


def test_no_selection_enables_no_servers() -> None:
    capabilities = {"context7": ("query_docs",), "serena": ()}

    assert normalize_mcp_selection([], capabilities, allow_tools=False) == {
        "requested": (),
        "effective_servers": (),
        "effective_tools": (),
    }


def test_server_selection_enables_only_selected_server() -> None:
    capabilities = {"context7": ("query_docs",), "serena": ()}

    assert normalize_mcp_selection(["serena"], capabilities, allow_tools=False) == {
        "requested": ("serena",),
        "effective_servers": ("serena",),
        "effective_tools": (),
    }


def test_tool_selection_is_rejected_when_executor_cannot_narrow_tools() -> None:
    with pytest.raises(McpSelectionError, match="tool-level MCP selection"):
        normalize_mcp_selection(
            ["context7.query_docs"],
            {"context7": ("query_docs",)},
            allow_tools=False,
        )


@pytest.mark.parametrize("selector", ["missing", "context7.missing", "context7."])
def test_unknown_or_malformed_selection_is_rejected(selector: str) -> None:
    with pytest.raises(McpSelectionError):
        normalize_mcp_selection(
            [selector],
            {"context7": ("query_docs",)},
            allow_tools=True,
        )
