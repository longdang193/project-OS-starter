"""Shared MCP capability and selection normalization."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class McpSelectionError(ValueError):
    """Raised when MCP configuration or selection is invalid."""


def load_mcp_capabilities(*configs: Mapping[str, Any]) -> dict[str, tuple[str, ...]]:
    servers: dict[str, tuple[str, ...]] = {}
    for config in configs:
        raw_servers = config.get("mcp_servers", {})
        if not isinstance(raw_servers, Mapping):
            raise McpSelectionError("Invalid Codex `[mcp_servers]` configuration.")
        for name, raw_server in raw_servers.items():
            if not isinstance(name, str) or not name.strip():
                raise McpSelectionError("MCP server names must be non-empty strings.")
            if not isinstance(raw_server, Mapping):
                raise McpSelectionError(f"Invalid MCP server configuration: {name}")
            if raw_server.get("enabled") is False:
                servers.pop(name, None)
                continue
            raw_tools = raw_server.get("tools", {})
            if not isinstance(raw_tools, Mapping):
                raw_tools = {}
            servers[name] = tuple(
                sorted(
                    tool
                    for tool in raw_tools
                    if isinstance(tool, str) and tool.strip()
                )
            )
    return dict(sorted(servers.items()))


def normalize_mcp_selection(
    values: list[str],
    capabilities: Mapping[str, tuple[str, ...]],
    *,
    allow_tools: bool,
) -> dict[str, tuple[str, ...]]:
    requested: list[str] = []
    for value in values:
        for selector in value.split(","):
            selector = selector.strip()
            if not selector:
                raise McpSelectionError("MCP selection contains an empty selector.")
            requested.append(selector)

    effective_servers: set[str] = set()
    effective_tools: set[str] = set()
    for selector in requested:
        server, separator, tool = selector.partition(".")
        if server not in capabilities:
            raise McpSelectionError(f"Unknown MCP server selection `{server}`.")
        if not separator:
            effective_servers.add(server)
            continue
        if not tool or "." in tool:
            raise McpSelectionError(f"Malformed MCP tool selection `{selector}`.")
        if not allow_tools:
            raise McpSelectionError(
                "Executor cannot enforce tool-level MCP selection."
            )
        if tool not in capabilities[server]:
            raise McpSelectionError(f"Unknown MCP tool selection `{selector}`.")
        effective_tools.add(selector)

    effective_tools.difference_update(
        f"{server}.{tool}"
        for server in effective_servers
        for tool in capabilities[server]
    )
    return {
        "requested": tuple(sorted(set(requested))),
        "effective_servers": tuple(sorted(effective_servers)),
        "effective_tools": tuple(sorted(effective_tools)),
    }
