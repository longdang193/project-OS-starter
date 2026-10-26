"""Shared MCP capability and selection normalization."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
import json
import re
from typing import Any


class McpSelectionError(ValueError):
    """Raised when MCP configuration or selection is invalid."""


_ENVIRONMENT_REFERENCE_PATTERN = re.compile(
    r"\$\{[A-Za-z_][A-Za-z0-9_]*(?::-[^}]*)?\}"
)
_ENVIRONMENT_DEPENDENT_KEYS = {
    "env_http_headers",
    "env_vars",
    "bearer_token_env_var",
    "oauth_client_id_env_var",
    "oauth_client_secret_env_var",
}


def _key_has_environment_dependency(key: object, value: object) -> bool:
    if not isinstance(key, str) or not key.strip():
        return False
    normalized = key.strip().casefold().replace("-", "_")
    if normalized.endswith("_env_var") or normalized in _ENVIRONMENT_DEPENDENT_KEYS:
        if isinstance(value, str):
            return bool(value.strip())
        if isinstance(value, Mapping):
            return bool(value)
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            return bool(value)
        return value is not None
    return False


def _effective_mcp_server_configurations(
    *configs: Mapping[str, Any],
) -> dict[str, Mapping[str, Any]]:
    effective_servers: dict[str, Mapping[str, Any]] = {}
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
                effective_servers.pop(name, None)
            else:
                effective_servers[name] = dict(raw_server)
    return effective_servers


def _contains_environment_dependency(value: object) -> bool:
    if isinstance(value, str):
        return bool(_ENVIRONMENT_REFERENCE_PATTERN.search(value))
    if isinstance(value, Mapping):
        for child_key, child_value in value.items():
            if _key_has_environment_dependency(child_key, child_value):
                return True
            if _contains_environment_dependency(child_value):
                return True
        return False
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_environment_dependency(item) for item in value)
    return False


def mcp_server_configuration_is_complete(
    *configs: Mapping[str, Any],
    selected_server_names: tuple[str, ...] | list[str] | None = None,
) -> bool:
    return not mcp_server_configuration_environment_dependencies(
        *configs,
        selected_server_names=selected_server_names,
    )


def mcp_server_configuration_environment_dependencies(
    *configs: Mapping[str, Any],
    selected_server_names: tuple[str, ...] | list[str] | None = None,
) -> tuple[str, ...]:
    selected = set(selected_server_names) if selected_server_names is not None else None
    effective_servers = _effective_mcp_server_configurations(*configs)
    return tuple(
        sorted(
            name
            for name, server in effective_servers.items()
            if (selected is None or name in selected)
            and _contains_environment_dependency(server)
        )
    )


def mcp_server_configuration_digest(
    *configs: Mapping[str, Any],
    selected_server_names: tuple[str, ...] | list[str] | None = None,
) -> str:
    selected = set(selected_server_names) if selected_server_names is not None else None
    effective_servers = _effective_mcp_server_configurations(*configs)
    payload = {
        "mcp_servers": {
            name: effective_servers[name]
            for name in sorted(effective_servers)
            if selected is None or name in selected
        }
    }
    return hashlib.sha256(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    ).hexdigest()


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
