"""Launch bounded delegated workers with local Codex binding and shared roles."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
import uuid
try:
    import owned_process as _owned_process
except ModuleNotFoundError:
    from scripts import owned_process as _owned_process

run_owned_process = _owned_process.run_owned_process
try:
    from agent_profile_registry import load_agent_profiles
except ModuleNotFoundError:
    from scripts.agent_profile_registry import load_agent_profiles
try:
    from project_root import resolve_repo_root
except ModuleNotFoundError:
    from scripts.project_root import resolve_repo_root
try:
    from mcp_selection import McpSelectionError, load_mcp_capabilities, normalize_mcp_selection
except ModuleNotFoundError:
    from scripts.mcp_selection import (
        McpSelectionError,
        load_mcp_capabilities,
        normalize_mcp_selection,
    )
try:
    from deepagents_result_contract import RESULT_MAX_BYTES, RESULT_SCHEMA, encode_result_receipt
except ModuleNotFoundError:
    from scripts.deepagents_result_contract import RESULT_MAX_BYTES, RESULT_SCHEMA, encode_result_receipt
try:
    from herdr_attempt_contract import (
        AttemptContractError,
        derive_lifecycle_state,
        same_attempt_binding,
    )
except ModuleNotFoundError:
    from scripts.herdr_attempt_contract import (
        AttemptContractError,
        derive_lifecycle_state,
        same_attempt_binding,
    )



_ROLE_VIEWS_MARKER = ".dcode-project-owned"
_ROLE_VIEWS_SCHEMA = 1
_LEGACY_ROLE_VIEWS_MARKER = "dcode-project owns this directory.\n"
_HANDOFF_SCHEMA = "codex.mcp.handoff.v1"
_HANDOFF_MAX_BYTES = 262_144
_HANDOFF_MAX_SOURCES = 64
_HANDOFF_MAX_FACTS = 256
_HANDOFF_MAX_STRING = 4_096
_HANDOFF_MAX_DEPTH = 16
_HANDOFF_MAX_AGE = timedelta(hours=24)
_HANDOFF_ROOT_PARTS = (".local", "share", "dcode-project", "handoffs")
_SENSITIVE_NAME = re.compile(
    r"(?:api[_-]?key|authorization|cookie|credential|password|secret|token|raw[_-]?(?:body|header|network))",
    re.IGNORECASE,
)
_SENSITIVE_VALUE = re.compile(
    r"(?:bearer\s+\S+|sk-[A-Za-z0-9_-]{8,}|api[_-]?key\s*[:=]\s*\S+)",
    re.IGNORECASE,
)
_NATIVE_MCP_FIELDS = {
    "allowedTools",
    "args",
    "command",
    "disabledTools",
    "env",
    "headers",
    "startup_timeout_sec",
    "url",
}
_IGNORED_CODEX_MCP_FIELDS = {"default_tools_approval_mode"}
_NATIVE_ENV_REFERENCE = re.compile(r"\$\{[A-Za-z_][A-Za-z0-9_]*\}")
_DIRECT_MCP_RUNTIME_PARENT = "dcode-project-mcp"
_DIRECT_MCP_RUNTIME_PREFIX = "runtime-"
_DIRECT_MCP_OWNER_MARKER = ".owner"
_DIRECT_MCP_OWNER_VALUE = "dcode-project-mcp-runtime.v1\n"
_DIRECT_MCP_STALE_AGE = timedelta(hours=24)
_ROLE_VIEWS_LOCK_PARENT = "dcode-project-role-locks"
_ATTEMPT_GUARD_PARENT = "attempts"
_ATTEMPT_GUARD_SCHEMA = "dcode-project.attempt.v1"
_ATTEMPT_GUARD_MAX_BYTES = 16 * 1024
_RESULT_SCHEMA = RESULT_SCHEMA
_RESULT_MAX_BYTES = RESULT_MAX_BYTES
_ALLOWED_RUNTIME_FLAGS = {
    "--print-config",
    "--json",
    "-q",
    "--quiet",
    "--no-stream",
    "--no-mcp",
}
_ALLOWED_RUNTIME_VALUE_OPTIONS = {
    "-n",
    "--non-interactive",
    "--max-turns",
    "--timeout",
    "--goal",
    "--rubric",
    "--rubric-max-iterations",
    "--recursion-limit",
    "--mcp-select",
    "--handoff-file",
    "--role",
    "--executor",
    "--result-file",
    "--attempt-id",
    "--assignment-id",
    "--repository-identity",
    "--task-sha256",
    "--grant-digest",
    "--prior-attempt-known",
    "--local-capability",
}
_FIXED_LOCAL_CAPABILITY_OPTIONS = (
    "--allow-fs-tools",
    "all",
)
_LOCAL_CAPABILITY_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._+-]*$")
_DEEPAGENTS_DEFAULT_TIMEOUT = 420.0
_PROJECT_GUIDANCE_INSTRUCTION = (
    "Project guidance: read repository root `AGENTS.md` before acting. "
    "Before modifying any file, read every applicable ancestor `AGENTS.md`. "
    "Read only explicitly named canonical project skills at "
    "`~/.agents/skills/<name>/SKILL.md`; do not scan or copy unrelated skills."
)


def _config_path() -> Path:
    override = os.environ.get("DCODE_PROJECT_CONFIG")
    if override:
        return Path(override).expanduser().resolve()
    return Path.home() / ".local" / "share" / "dcode-project" / "config.toml"


def _reject_unmanaged_runtime_options(argv: list[str]) -> None:
    index = 0
    while index < len(argv):
        argument = argv[index]
        option = argument.split("=", 1)[0]
        if option == "--stdin":
            raise RuntimeError(
                "dcode-project does not accept direct `--stdin`; pass a validated "
                "`--handoff-file <absolute-path>` with `-n <task>`."
            )
        if option in _ALLOWED_RUNTIME_FLAGS:
            index += 1
            continue
        if option in _ALLOWED_RUNTIME_VALUE_OPTIONS:
            if "=" not in argument:
                if index + 1 >= len(argv) or argv[index + 1].startswith("-"):
                    raise RuntimeError(f"dcode-project requires a value for `{option}`.")
                index += 2
                continue
            index += 1
            continue
        raise RuntimeError(
            f"dcode-project does not permit `{option}`. Current launcher has no Codex "
            "permission or MCP projection; use its fixed local binding and no-MCP path."
        )


def _load_toml(path: Path, label: str) -> dict[str, object]:
    try:
        with path.open("rb") as handle:
            payload = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise RuntimeError(f"Cannot read {label}: {path}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"Invalid {label}: {path}")
    return payload


def _required_string(values: dict[str, object], key: str, label: str) -> str:
    value = values.get(key)
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(f"Missing {label} `{key}`.")
    return value.strip()


def _read_env_value(path: Path, key: str) -> str:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise RuntimeError(f"Cannot read secret file: {path}") from exc
    for line in lines:
        candidate = line.strip()
        if not candidate or candidate.startswith("#"):
            continue
        if candidate.startswith("export "):
            candidate = candidate[7:].lstrip()
        name, separator, value = candidate.partition("=")
        if separator and name.strip() == key:
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
                value = value[1:-1]
            if value:
                return value
    raise RuntimeError(f"Secret key `{key}` is absent or empty in {path}.")


def _repo_root() -> Path:
    return resolve_repo_root()


def _load_roles(
    repo_root: Path,
    runtime_provider: str,
) -> list[dict[str, object]]:
    try:
        profiles = load_agent_profiles(repo_root / "agents", runtime_provider=runtime_provider)
    except ValueError as exc:
        raise RuntimeError(str(exc)) from exc
    return [
        {
            "name": profile.name,
            "model_provider": profile.model_provider,
            "model": profile.model,
            "rank": profile.rank,
            "description": profile.description,
            "developer_instructions": profile.developer_instructions,
        }
        for profile in profiles.values()
    ]

def _role_view_path(agents_root: Path, role_name: str) -> Path:
    return agents_root / role_name / "AGENTS.md"


def _role_view_content(role: dict[str, object]) -> str:
    model = f"openai:{role['model']}"
    return (
        "---\n"
        f"name: {json.dumps(role['name'])}\n"
        f"description: {json.dumps(role['description'])}\n"
        f"model: {json.dumps(model)}\n"
        "---\n\n"
        f"{role['developer_instructions']}\n"
    )


def _owned_views_marker(roles: list[dict[str, object]]) -> str:
    views = {
        role["name"]: _role_view_content(role)
        for role in roles
    }
    return json.dumps(
        {"schema": _ROLE_VIEWS_SCHEMA, "views": views},
        sort_keys=True,
    ) + "\n"


def _read_owned_views(marker: Path, roles: list[dict[str, object]]) -> dict[str, str]:
    if marker.is_symlink() or not marker.is_file():
        raise RuntimeError(f"Cannot verify owned DeepAgents role views: {marker}")
    try:
        marker_content = marker.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"Cannot verify owned DeepAgents role views: {marker}") from exc
    if marker_content == _LEGACY_ROLE_VIEWS_MARKER:
        return {role["name"]: _role_view_content(role) for role in roles}
    try:
        payload = json.loads(marker_content)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Cannot verify owned DeepAgents role views: {marker}") from exc
    if not isinstance(payload, dict) or payload.get("schema") != _ROLE_VIEWS_SCHEMA:
        raise RuntimeError(f"Cannot verify owned DeepAgents role views: {marker}")
    views = payload.get("views")
    if not isinstance(views, dict) or not all(
        isinstance(name, str)
        and name
        and Path(name).name == name
        and isinstance(content, str)
        for name, content in views.items()
    ):
        raise RuntimeError(f"Cannot verify owned DeepAgents role views: {marker}")
    return views


def _unlink_if_exact(path: Path, expected: str) -> None:
    if path.is_symlink() or not path.is_file():
        return
    try:
        current = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return
    if current == expected:
        path.unlink()


def _remove_empty_parents(path: Path, stop_at: Path) -> None:
    current = path
    while current != stop_at:
        try:
            current.rmdir()
        except OSError:
            return
        current = current.parent


def _remove_owned_views(agents_root: Path, views: dict[str, str]) -> None:
    for role_name, content in views.items():
        destination = _role_view_path(agents_root, role_name)
        _unlink_if_exact(destination, content)
        _remove_empty_parents(destination.parent, agents_root)


def _has_unowned_role_content(agents_root: Path, marker: Path, views: dict[str, str]) -> bool:
    for path in agents_root.rglob("*"):
        if path == marker or (not path.is_file() and not path.is_symlink()):
            continue
        expected = next(
            (
                content
                for role_name, content in views.items()
                if path == _role_view_path(agents_root, role_name)
            ),
            None,
        )
        if expected is None or path.is_symlink():
            return True
        try:
            if path.read_text(encoding="utf-8") != expected:
                return True
        except (OSError, UnicodeDecodeError):
            return True
    return False


def _remove_role_views(repo_root: Path, roles: list[dict[str, str]]) -> dict[str, object]:
    agents_root = repo_root / ".deepagents" / "agents"
    marker = agents_root / _ROLE_VIEWS_MARKER
    if not marker.exists():
        remaining_paths = sorted(
            str(_role_view_path(agents_root, role["name"]).relative_to(repo_root))
            for role in roles
            if _role_view_path(agents_root, role["name"]).exists()
            or _role_view_path(agents_root, role["name"]).is_symlink()
        )
        return {
            "state": "unverified",
            "remaining_paths": remaining_paths,
            "marker_state": "absent",
        }
    views = _read_owned_views(marker, roles)
    _remove_owned_views(agents_root, views)
    remaining_paths = sorted(
        str(_role_view_path(agents_root, role_name).relative_to(repo_root))
        for role_name in views
        if _role_view_path(agents_root, role_name).exists()
        or _role_view_path(agents_root, role_name).is_symlink()
    )
    if remaining_paths:
        return {
            "state": "preserved",
            "remaining_paths": remaining_paths,
            "marker_state": "retained",
        }
    try:
        marker.unlink()
    except OSError:
        return {
            "state": "unverified",
            "remaining_paths": [],
            "marker_state": "retained",
        }
    _remove_empty_parents(agents_root, repo_root)
    return {"state": "removed", "remaining_paths": [], "marker_state": "absent"}


def _result_file_path(raw_path: str) -> Path:
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        raise RuntimeError("dcode-project requires an absolute `--result-file` path.")
    return path.resolve()


def _publish_result_receipt(
    result_file: Path,
    *,
    attempt_id: str,
    worker_state: str,
    worker_exit_code: int | None,
    descendant_state: str,
    role_views_state: str,
    recovery_required: bool,
    shell_capabilities: dict[str, object] | None = None,
    cleanup_details: dict[str, object] | None = None,
) -> None:
    payload = {
        "schema": _RESULT_SCHEMA,
        "attempt_id": attempt_id,
        "worker": {
            "state": worker_state,
            "exit_code": worker_exit_code,
            "descendant_state": descendant_state,
        },
        "cleanup": {
            "state": role_views_state,
            "role_views_state": role_views_state,
            **(cleanup_details or {}),
        },
        "recovery_required": recovery_required,
    }
    if shell_capabilities is not None:
        payload["shell_capabilities"] = shell_capabilities
        payload["capabilities"] = {
            "requested": list(shell_capabilities.get("requested", [])),
            "passed_to_worker": list(
                shell_capabilities.get(
                    "passed_to_worker", shell_capabilities.get("effective", [])
                )
            ),
            "validated_available": list(
                shell_capabilities.get(
                    "validated_available", shell_capabilities.get("effective", [])
                )
            ),
            "digest": _sha256_json(
                shell_capabilities.get(
                    "validated_available", shell_capabilities.get("effective", [])
                )
            ),
            "validation_error": None,
        }
    encoded = encode_result_receipt(payload)
    temporary = result_file.with_name(f".{result_file.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("xb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, result_file)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _role_views_lock_path(repo_root: Path) -> Path:
    identity = str(repo_root.resolve())
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()
    return Path(tempfile.gettempdir()) / _ROLE_VIEWS_LOCK_PARENT / f"{digest}.lock"


def _lock_file(fd: int) -> None:
    if os.name == "nt":
        import msvcrt

        os.lseek(fd, 0, os.SEEK_SET)
        try:
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        except OSError as exc:
            raise BlockingIOError from exc
        return
    import fcntl

    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as exc:
        raise BlockingIOError from exc


def _unlock_file(fd: int) -> None:
    if os.name == "nt":
        import msvcrt

        os.lseek(fd, 0, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        return
    import fcntl

    fcntl.flock(fd, fcntl.LOCK_UN)


@contextmanager
def _role_views_lock(repo_root: Path):
    lock_path = _role_views_lock_path(repo_root)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
    os.set_inheritable(fd, False)
    acquired = False
    try:
        try:
            _lock_file(fd)
        except BlockingIOError as exc:
            raise RuntimeError(
                f"Another DeepAgents launch owns role views for worktree: {repo_root.resolve()}"
            ) from exc
        acquired = True
        yield
    finally:
        try:
            if acquired:
                _unlock_file(fd)
        finally:
            os.close(fd)


def _attempt_guard_root() -> Path:
    return Path.home() / ".local" / "share" / "dcode-project" / _ATTEMPT_GUARD_PARENT


def _attempt_guard_path(assignment_id: str) -> Path:
    if not isinstance(assignment_id, str) or not assignment_id.strip():
        raise RuntimeError("dcode-project requires a non-empty `--assignment-id`.")
    digest = hashlib.sha256(assignment_id.strip().encode("utf-8")).hexdigest()
    return _attempt_guard_root() / f"{digest}.json"


def _read_attempt_guard(path: Path) -> dict[str, object] | None:
    try:
        if not path.exists():
            return None
        if not path.is_file() or path.stat().st_size > _ATTEMPT_GUARD_MAX_BYTES:
            raise RuntimeError("dcode-project attempt guard is malformed or oversized.")
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("dcode-project attempt guard is unreadable.") from exc
    if not isinstance(payload, dict) or payload.get("schema") != _ATTEMPT_GUARD_SCHEMA:
        raise RuntimeError("dcode-project attempt guard schema mismatch.")
    return payload


def _write_attempt_guard(path: Path, payload: dict[str, object]) -> None:
    encoded = (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )
    if len(encoded) > _ATTEMPT_GUARD_MAX_BYTES:
        raise RuntimeError("dcode-project attempt guard exceeds size limit.")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("xb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _claim_attempt(
    *,
    assignment_id: str,
    attempt_id: str,
    executor: str,
    repository_identity: str,
    task_sha256: str,
    grant_digest: str,
    repo_root: Path,
    result_file: Path | None,
    task_result_file: Path | None = None,
    prior_attempt_known: bool = False,
) -> dict[str, object]:
    path = _attempt_guard_path(assignment_id)
    existing = _read_attempt_guard(path)
    candidate = {
        "schema": _ATTEMPT_GUARD_SCHEMA,
        "state": "active",
        "assignment_id": assignment_id,
        "attempt_id": attempt_id,
        "executor": executor,
        "repository_identity": repository_identity,
        "task_sha256": task_sha256,
        "grant_digest": grant_digest,
        "worktree": str(repo_root.resolve()),
        "receipt_path": str(result_file) if result_file is not None else None,
        "task_result_path": str(task_result_file) if task_result_file is not None else None,
        "claimed_at": datetime.now(timezone.utc).isoformat(),
    }
    if existing is None:
        if prior_attempt_known:
            return {"state": "RECOVERY_REQUIRED", "action": "RECONCILE"}
        _write_attempt_guard(path, candidate)
        return {"state": "ACTIVE", "action": "BLOCKED", "claimed": True, "record": candidate}
    if same_attempt_binding(existing, candidate):
        state = str(existing.get("state", "")).upper()
        if state not in {"ACTIVE", "SETTLED"}:
            return {"state": "RECOVERY_REQUIRED", "action": "RECONCILE"}
        return {"state": state, "action": "BLOCKED" if state == "ACTIVE" else "ELIGIBLE", "idempotent": True, "record": existing}
    existing_state = str(existing.get("state", "")).lower()
    if existing_state == "settled":
        _write_attempt_guard(path, candidate)
        return {"state": "ACTIVE", "action": "BLOCKED", "claimed": True, "replaced_settled": True, "record": candidate}
    state = "ACTIVE" if existing_state == "active" else "RECOVERY_REQUIRED"
    action = "BLOCKED" if state == "ACTIVE" else "RECONCILE"
    return {"state": state, "action": action, "record": existing}


def _settle_attempt(
    *,
    assignment_id: str,
    binding: dict[str, object],
    settlement_proven: bool,
) -> dict[str, object]:
    path = _attempt_guard_path(assignment_id)
    existing = _read_attempt_guard(path)
    if existing is None or not same_attempt_binding(existing, binding):
        raise RuntimeError("dcode-project attempt guard binding mismatch during settlement.")
    if not settlement_proven:
        return existing
    settled = dict(existing)
    settled.update(
        {
            "state": "settled",
            "settlement_proven": True,
            "settled_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    _write_attempt_guard(path, settled)
    return settled


def _write_role_views(repo_root: Path, roles: list[dict[str, object]]) -> Path:
    agents_root = repo_root / ".deepagents" / "agents"
    marker = agents_root / _ROLE_VIEWS_MARKER
    if agents_root.exists() and not agents_root.is_dir():
        raise RuntimeError(
            f"Refusing to replace user-owned DeepAgents role root: {agents_root} "
            "must be a directory."
        )
    if not agents_root.exists():
        agents_root.mkdir(parents=True)
    previous_views = _read_owned_views(marker, roles) if marker.exists() else {}
    if _has_unowned_role_content(agents_root, marker, previous_views):
        raise RuntimeError(f"Refusing to replace user-owned DeepAgents roles: {agents_root}")
    if marker.exists():
        _remove_owned_views(agents_root, previous_views)
    for role in roles:
        destination = _role_view_path(agents_root, role["name"])
        if destination.exists() or destination.is_symlink():
            raise RuntimeError(f"Refusing to replace user-owned DeepAgents role view: {destination}")
    marker.write_text(_owned_views_marker(roles), encoding="utf-8")
    try:
        for role in roles:
            destination = _role_view_path(agents_root, role["name"])
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(_role_view_content(role), encoding="utf-8")
    except OSError:
        _remove_role_views(repo_root, roles)
        raise
    return agents_root


@dataclass(frozen=True)
class _RuntimeBinding:
    model: str
    base_url: str
    provider_name: str
    secret_file: Path
    secret_key: str
    codex_config: dict[str, object]

    def read_api_key(self) -> str:
        return _read_env_value(self.secret_file, self.secret_key)


@dataclass(frozen=True)
class _WorkerLifecycleFacts:
    worker_state: str
    exit_code: int | None
    descendant_state: str
    termination_proven: bool


class _WorkerLifecycleError(RuntimeError):
    def __init__(self, message: str, facts: _WorkerLifecycleFacts) -> None:
        super().__init__(message)
        self.facts = facts


class _WorkerRecoveryBlocked(_WorkerLifecycleError):
    pass


def _runtime_binding(config: dict[str, object]) -> _RuntimeBinding:
    paths = config.get("paths")
    if not isinstance(paths, dict):
        raise RuntimeError("Missing local `[paths]` configuration.")
    codex_config = Path(_required_string(paths, "codex_config", "local paths")).expanduser()
    secret_file = Path(_required_string(paths, "secret_file", "local paths")).expanduser()
    secret_key = _required_string(paths, "secret_key", "local paths")
    codex = _load_toml(codex_config, "Codex config")
    provider_name = _required_string(codex, "model_provider", "Codex config")
    model = _required_string(codex, "model", "Codex config")
    providers = codex.get("model_providers")
    if not isinstance(providers, dict):
        raise RuntimeError("Missing Codex `model_providers` configuration.")
    provider = providers.get(provider_name)
    if not isinstance(provider, dict):
        raise RuntimeError(f"Active Codex provider is unavailable: {provider_name}")
    base_url = _required_string(provider, "base_url", "active Codex provider")
    return _RuntimeBinding(
        model=model,
        base_url=base_url,
        provider_name=provider_name,
        secret_file=secret_file,
        secret_key=secret_key,
        codex_config=codex,
    )


def _deepagents_model_params(
    codex_config: dict[str, object],
    provider_name: str,
) -> dict[str, bool]:
    providers = codex_config.get("model_providers")
    if not isinstance(providers, dict):
        raise RuntimeError("Missing Codex `model_providers` configuration for DeepAgents.")
    provider = providers.get(provider_name)
    if not isinstance(provider, dict):
        raise RuntimeError(f"Active Codex provider is unavailable: {provider_name}")
    wire_api = provider.get("wire_api")
    if not isinstance(wire_api, str) or not wire_api.strip():
        raise RuntimeError(
            f"Active Codex provider `{provider_name}` must declare `wire_api` for DeepAgents."
        )
    normalized = wire_api.strip().lower()
    if normalized not in {"chat", "responses"}:
        raise RuntimeError(
            f"DeepAgents does not support active Codex provider `{provider_name}` "
            f"with `wire_api = \"{wire_api}\"`; use `chat` or `responses`."
        )
    return {"use_responses_api": normalized == "responses"}


def _mcp_capabilities(codex_config: dict[str, object]) -> dict[str, object]:
    try:
        normalized = {
            name: list(tools)
            for name, tools in load_mcp_capabilities(codex_config).items()
        }
    except McpSelectionError as exc:
        raise RuntimeError(str(exc)) from exc
    server_ids = sorted(normalized)
    tool_ids = sorted(
        f"{server}.{tool}"
        for server, tools in normalized.items()
        for tool in tools
    )
    runtime = {
        "mcp_servers": normalized,
    }
    capability_digest = _sha256_json(runtime)
    return {
        "mcp_servers": server_ids,
        "mcp_tools": tool_ids,
        "server_tools": normalized,
        "mcp_capability_digest": capability_digest,
    }

def _sha256_json(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()

def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def _runtime_binding_digest(
    provider_name: str,
    controller_model: str,
    worker_model: str | None,
    base_url: str,
    deepagents_model_params: dict[str, bool] | None = None,
) -> str:
    return _sha256_json(
        {
            "base_url": base_url,
            "deepagents_model_params": deepagents_model_params,
            "controller_model": controller_model,
            "provider": provider_name,
            "worker_model": worker_model,
        }
    )

def _normalized_mcp_selection(
    values: list[str], capabilities: dict[str, object]
) -> dict[str, tuple[str, ...]]:
    if not values:
        return {"requested": (), "effective_servers": (), "effective_tools": ()}
    server_tools = capabilities["server_tools"]
    if not isinstance(server_tools, dict):
        raise RuntimeError("Invalid MCP capability projection.")
    try:
        selection = normalize_mcp_selection(values, server_tools, allow_tools=True)
    except McpSelectionError as exc:
        raise RuntimeError(str(exc)) from exc
    return selection


def _parse_mcp_selection(values: list[str], capabilities: dict[str, object]) -> list[str]:
    return list(_normalized_mcp_selection(values, capabilities)["requested"])


def _mcp_selection_state(
    values: list[str], capabilities: dict[str, object]
) -> dict[str, object]:
    selection = _normalized_mcp_selection(values, capabilities)
    requested = list(selection["requested"])
    if not requested:
        return {
            "available_mcp": sorted(
                list(capabilities["mcp_servers"]) + list(capabilities["mcp_tools"])
            ),
            "requested_mcp": [],
            "effective_mcp": [],
            "mcp_mode": "disabled",
        }
    effective = sorted(
        set(selection["effective_servers"]) | set(selection["effective_tools"])
    )
    return {
        "available_mcp": sorted(
            list(capabilities["mcp_servers"]) + list(capabilities["mcp_tools"])
        ),
        "requested_mcp": requested,
        "effective_mcp": effective,
        "mcp_mode": "direct",
    }


def _native_mcp_config(
    codex_config: dict[str, object],
    selected: list[str],
) -> dict[str, object]:
    servers = codex_config.get("mcp_servers")
    if not isinstance(servers, dict):
        raise RuntimeError("Invalid Codex `[mcp_servers]` configuration.")
    projected: dict[str, object] = {}
    selected_servers = {value for value in selected if "." not in value}
    selected_tools: dict[str, set[str]] = {}
    for value in selected:
        server, separator, tool = value.partition(".")
        if separator:
            selected_tools.setdefault(server, set()).add(tool)
    for server in sorted(selected_servers | set(selected_tools)):
        server_config = servers.get(server)
        if not isinstance(server_config, dict):
            raise RuntimeError(f"Invalid Codex MCP server configuration: {server}")
        definition: dict[str, object] = {}
        for key, value in server_config.items():
            if key == "tools":
                continue
            if key in _IGNORED_CODEX_MCP_FIELDS:
                continue
            if key not in _NATIVE_MCP_FIELDS:
                raise RuntimeError(f"Unsupported Codex MCP server field: {key}")
            if key == "startup_timeout_sec":
                if (
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or value < 0
                    or (isinstance(value, float) and not value.is_integer())
                ):
                    raise RuntimeError(
                        "Native MCP `startup_timeout_sec` must be a nonnegative integer."
                    )
                definition[key] = int(value)
                continue
            if key in {"env", "headers"}:
                if not isinstance(value, dict):
                    raise RuntimeError(f"Invalid native MCP `{key}` configuration.")
                safe_values: dict[str, str] = {}
                for name, raw_value in value.items():
                    if not isinstance(name, str) or not name.strip():
                        raise RuntimeError(f"Invalid native MCP `{key}` name.")
                    if not isinstance(raw_value, str):
                        raise RuntimeError(f"Invalid native MCP `{key}` value.")
                    _reject_sensitive_value(raw_value)
                    if key == "env" and not _NATIVE_ENV_REFERENCE.fullmatch(raw_value):
                        _reject_sensitive_value({name: raw_value})
                    if key == "headers" and not _NATIVE_ENV_REFERENCE.fullmatch(raw_value):
                        raise RuntimeError(
                            "Native MCP `headers` values must be environment references."
                        )
                    safe_values[name] = raw_value
                definition[key] = safe_values
                continue
            if key in {"allowedTools", "args", "disabledTools"}:
                if not isinstance(value, list) or any(
                    not isinstance(item, str) for item in value
                ):
                    raise RuntimeError(f"Invalid native MCP `{key}` configuration.")
                for item in value:
                    _reject_sensitive_value(item)
                definition[key] = list(value)
                continue
            if not isinstance(value, str):
                raise RuntimeError(f"Invalid native MCP `{key}` configuration.")
            _reject_sensitive_value(value)
            definition[key] = value
        if server not in selected_servers and selected_tools.get(server):
            definition.pop("disabledTools", None)
            definition["allowedTools"] = sorted(
                {
                    tool_name
                    for tool_name in selected_tools[server]
                    for tool_name in (tool_name, tool_name.replace("_", "-"))
                }
            )
        projected[server] = definition
    return {"mcpServers": projected}


def _direct_mcp_runtime_parent() -> Path:
    return Path(tempfile.gettempdir()) / _DIRECT_MCP_RUNTIME_PARENT


def _ensure_direct_mcp_runtime_parent() -> Path:
    parent = _direct_mcp_runtime_parent()
    if parent.is_symlink() or (parent.exists() and not parent.is_dir()):
        raise RuntimeError("Direct MCP runtime parent is not a safe directory.")
    if not parent.exists():
        try:
            parent.mkdir()
            (parent / _DIRECT_MCP_OWNER_MARKER).write_text(
                _DIRECT_MCP_OWNER_VALUE,
                encoding="utf-8",
            )
        except OSError as exc:
            raise RuntimeError("Cannot initialize direct MCP runtime directory.") from exc
        return parent
    marker = parent / _DIRECT_MCP_OWNER_MARKER
    try:
        owned = marker.is_file() and not marker.is_symlink() and marker.read_text(
            encoding="utf-8"
        ) == _DIRECT_MCP_OWNER_VALUE
    except OSError as exc:
        raise RuntimeError("Cannot verify direct MCP runtime ownership.") from exc
    if not owned:
        raise RuntimeError("Direct MCP runtime parent ownership is invalid.")
    return parent


def _cleanup_stale_direct_mcp_runtimes(parent: Path) -> None:
    cutoff = datetime.now(timezone.utc).timestamp() - _DIRECT_MCP_STALE_AGE.total_seconds()
    try:
        entries = tuple(parent.iterdir())
    except OSError:
        return
    for entry in entries:
        if (
            not entry.name.startswith(_DIRECT_MCP_RUNTIME_PREFIX)
            or entry.is_symlink()
            or not entry.is_dir()
        ):
            continue
        marker = entry / _DIRECT_MCP_OWNER_MARKER
        try:
            if (
                not marker.is_file()
                or marker.is_symlink()
                or marker.read_text(encoding="utf-8") != _DIRECT_MCP_OWNER_VALUE
                or entry.stat().st_mtime > cutoff
            ):
                continue
            shutil.rmtree(entry)
        except OSError:
            continue


@contextmanager
def _direct_mcp_runtime(
    repo_root: Path,
    codex_config: dict[str, object],
    selected: list[str],
    environment: dict[str, str],
):
    previous_home = environment.get("DEEPAGENTS_HOME")
    previous_project_allowlist = environment.get(
        "DEEPAGENTS_CODE_DANGEROUSLY_ENABLE_PROJECT_MCP_SERVERS"
    )
    runtime_root: Path | None = None
    try:
        runtime_parent = _ensure_direct_mcp_runtime_parent()
        runtime_root = Path(
            tempfile.mkdtemp(prefix=_DIRECT_MCP_RUNTIME_PREFIX, dir=runtime_parent)
        )
        (runtime_root / _DIRECT_MCP_OWNER_MARKER).write_text(
            _DIRECT_MCP_OWNER_VALUE,
            encoding="utf-8",
        )
        config_path = runtime_root / "mcp.json"
        isolated_home = runtime_root / "home"
        config_path.write_text(
            json.dumps(_native_mcp_config(codex_config, selected), sort_keys=True),
            encoding="utf-8",
        )
        isolated_home.mkdir()
        environment["DEEPAGENTS_HOME"] = str(isolated_home)
        environment.pop("DEEPAGENTS_CODE_DANGEROUSLY_ENABLE_PROJECT_MCP_SERVERS", None)
        yield config_path
    finally:
        if previous_home is None:
            environment.pop("DEEPAGENTS_HOME", None)
        else:
            environment["DEEPAGENTS_HOME"] = previous_home
        if previous_project_allowlist is None:
            environment.pop("DEEPAGENTS_CODE_DANGEROUSLY_ENABLE_PROJECT_MCP_SERVERS", None)
        else:
            environment[
                "DEEPAGENTS_CODE_DANGEROUSLY_ENABLE_PROJECT_MCP_SERVERS"
            ] = previous_project_allowlist
        if runtime_root is not None:
            shutil.rmtree(runtime_root, ignore_errors=True)

def _controller_options(
    argv: list[str],
) -> tuple[
    list[str],
    list[str],
    str | None,
    str | None,
    str | None,
    str | None,
    str | None,
    str | None,
    str | None,
    str | None,
    str | None,
    bool,
]:
    child: list[str] = []
    selections: list[str] = []
    handoff_file: str | None = None
    role_name: str | None = None
    executor: str | None = None
    result_file: str | None = None
    attempt_id: str | None = None
    assignment_id_value: str | None = None
    repository_identity: str | None = None
    task_sha256: str | None = None
    grant_digest_value: str | None = None
    prior_attempt_known = False
    index = 0
    while index < len(argv):
        argument = argv[index]
        option, separator, inline_value = argument.partition("=")
        if option in {
            "--mcp-select",
            "--handoff-file",
            "--role",
            "--executor",
            "--result-file",
            "--attempt-id",
            "--assignment-id",
            "--repository-identity",
            "--task-sha256",
            "--grant-digest",
            "--prior-attempt-known",
        }:
            if separator:
                value = inline_value
            elif index + 1 < len(argv):
                value = argv[index + 1]
                index += 1
            else:
                raise RuntimeError(f"dcode-project requires a value for `{option}`.")
            if not value:
                raise RuntimeError(f"dcode-project requires a value for `{option}`.")
            if option == "--mcp-select":
                selections.append(value)
            elif option == "--role":
                if role_name is not None:
                    raise RuntimeError("dcode-project accepts only one `--role`.")
                role_name = value
            elif option == "--handoff-file":
                if handoff_file is not None:
                    raise RuntimeError("dcode-project accepts only one `--handoff-file`.")
                handoff_file = value
            elif option == "--result-file":
                if result_file is not None:
                    raise RuntimeError("dcode-project accepts only one `--result-file`.")
                result_file = value
            elif option == "--attempt-id":
                if attempt_id is not None:
                    raise RuntimeError("dcode-project accepts only one `--attempt-id`.")
                attempt_id = value
            elif option == "--assignment-id":
                if assignment_id_value is not None:
                    raise RuntimeError("dcode-project accepts only one `--assignment-id`.")
                assignment_id_value = value
            elif option == "--repository-identity":
                if repository_identity is not None:
                    raise RuntimeError("dcode-project accepts only one `--repository-identity`.")
                repository_identity = value
            elif option == "--task-sha256":
                if task_sha256 is not None:
                    raise RuntimeError("dcode-project accepts only one `--task-sha256`.")
                task_sha256 = value
            elif option == "--grant-digest":
                if grant_digest_value is not None:
                    raise RuntimeError("dcode-project accepts only one `--grant-digest`.")
                grant_digest_value = value
            elif option == "--prior-attempt-known":
                if value.casefold() not in {"true", "false"}:
                    raise RuntimeError("dcode-project requires `--prior-attempt-known` to be true or false.")
                prior_attempt_known = value.casefold() == "true"
            elif executor is not None:
                raise RuntimeError("dcode-project accepts only one `--executor`.")
            else:
                executor = value
        else:
            child.append(argument)
        index += 1
    return (
        child,
        selections,
        handoff_file,
        role_name,
        executor,
        result_file,
        attempt_id,
        assignment_id_value,
        repository_identity,
        task_sha256,
        grant_digest_value,
        prior_attempt_known,
    )


def _extract_local_capabilities(argv: list[str]) -> tuple[list[str], list[str]]:
    child: list[str] = []
    values: list[str] = []
    index = 0
    while index < len(argv):
        option, separator, inline_value = argv[index].partition("=")
        if option != "--local-capability":
            child.append(argv[index])
            index += 1
            continue
        if separator:
            value = inline_value
        elif index + 1 < len(argv):
            value = argv[index + 1]
            index += 1
        else:
            raise RuntimeError("dcode-project requires a value for `--local-capability`.")
        if not value:
            raise RuntimeError("dcode-project requires a value for `--local-capability`.")
        values.append(value)
        index += 1
    normalized = [value.lower() for value in values]
    if any(not _LOCAL_CAPABILITY_PATTERN.fullmatch(value) or ".." in value for value in normalized):
        raise RuntimeError("local_capabilities must contain safe command basenames.")
    if len(normalized) != len(set(normalized)):
        raise RuntimeError("local_capabilities cannot contain duplicates.")
    return child, normalized


def _resolve_worker_shell_capabilities(
    requested: list[str], environment: dict[str, str]
) -> dict[str, list[str]]:
    requested_values = list(requested)
    effective = requested_values or ["git", "py"]
    path = environment.get("PATH")
    unavailable = [value for value in effective if shutil.which(value, path=path) is None]
    if unavailable:
        raise RuntimeError("Unavailable local capabilities: " + ", ".join(unavailable))
    return {
        "requested": requested_values,
        "available": list(effective),
        "effective": list(effective),
        "passed_to_worker": list(effective),
        "validated_available": list(effective),
    }


def _resolve_executor(config: dict[str, object], explicit: str | None) -> str:
    if explicit is not None:
        selected = explicit.strip().lower()
    else:
        delegation = config.get("delegation")
        if not isinstance(delegation, dict):
            raise RuntimeError("Missing `[delegation].default_executor` configuration.")
        value = delegation.get("default_executor")
        if not isinstance(value, str) or not value.strip():
            raise RuntimeError("Missing `[delegation].default_executor` configuration.")
        selected = value.strip().lower()
    if selected not in {"tura", "deepagents"}:
        raise RuntimeError(f"Unsupported executor `{selected}`; use `tura` or `deepagents`.")
    return selected


def _tura_worker_paths(config: dict[str, object]) -> tuple[Path, Path]:
    paths = config.get("paths")
    if not isinstance(paths, dict):
        raise RuntimeError("Missing local `[paths]` configuration.")
    executable = Path(_required_string(paths, "tura_executable", "local paths")).expanduser()
    provider_config = Path(
        _required_string(paths, "tura_provider_config", "local paths")
    ).expanduser()
    if not executable.is_file():
        raise RuntimeError(f"Tura executable is missing: {executable}")
    if not provider_config.is_file():
        raise RuntimeError(f"Tura provider config is missing: {provider_config}")
    return executable.resolve(), provider_config.resolve()

def _handoff_root() -> Path:
    return Path.home().joinpath(*_HANDOFF_ROOT_PARTS)

def _safe_handoff_path(raw_path: str) -> Path:
    candidate = Path(raw_path).expanduser()
    if not candidate.is_absolute():
        raise RuntimeError("Handoff path must be absolute.")
    root = _handoff_root().resolve()
    try:
        relative = candidate.relative_to(root)
    except ValueError as exc:
        raise RuntimeError(f"Handoff path must stay under `{root}`.") from exc
    current = root
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            raise RuntimeError("Handoff path cannot contain symlinks.")
    if not candidate.is_file() or candidate.is_symlink():
        raise RuntimeError(f"Handoff file is missing or not a regular file: {candidate}")
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, ValueError) as exc:
        raise RuntimeError("Handoff path resolves outside approved root.") from exc
    return candidate

def _parse_timestamp(value: object) -> datetime:
    if not isinstance(value, str) or len(value) > 64:
        raise RuntimeError("Handoff `generated_at` must be RFC3339 text.")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RuntimeError("Handoff `generated_at` must be RFC3339 text.") from exc
    if parsed.tzinfo is None:
        raise RuntimeError("Handoff `generated_at` must include timezone.")
    return parsed.astimezone(timezone.utc)

def _reject_sensitive_value(value: object, depth: int = 0) -> None:
    if depth > _HANDOFF_MAX_DEPTH:
        raise RuntimeError("Handoff value nesting is too deep.")
    if isinstance(value, str):
        if len(value) > _HANDOFF_MAX_STRING or _SENSITIVE_VALUE.search(value):
            raise RuntimeError("Handoff contains sensitive or oversized text.")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str) or len(key) > _HANDOFF_MAX_STRING:
                raise RuntimeError("Handoff object keys are invalid.")
            if _SENSITIVE_NAME.search(key):
                raise RuntimeError("Handoff contains sensitive field names.")
            _reject_sensitive_value(item, depth + 1)
        return
    if isinstance(value, list):
        for item in value:
            _reject_sensitive_value(item, depth + 1)
        return
    if value is not None and not isinstance(value, (bool, int, float)):
        raise RuntimeError("Handoff contains unsupported value type.")

def _validate_handoff(
    raw_path: str,
    capabilities: dict[str, object],
    selected: list[str],
) -> tuple[Path, dict[str, object]]:
    path = _safe_handoff_path(raw_path)
    if path.stat().st_size > _HANDOFF_MAX_BYTES:
        raise RuntimeError("Handoff file exceeds size limit.")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("Handoff file is not valid UTF-8 JSON.") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("Handoff root must be an object.")
    required = {"schema", "generated_at", "mcp_capability_digest", "sources", "facts"}
    allowed = required | {"constraints"}
    if set(payload) - allowed or not required <= set(payload):
        raise RuntimeError("Handoff fields do not match codex.mcp.handoff.v1.")
    if payload["schema"] != _HANDOFF_SCHEMA:
        raise RuntimeError("Unsupported handoff schema.")
    generated_at = _parse_timestamp(payload["generated_at"])
    now = datetime.now(timezone.utc)
    if generated_at > now + timedelta(minutes=5) or now - generated_at > _HANDOFF_MAX_AGE:
        raise RuntimeError("Handoff is stale or from the future.")
    if payload["mcp_capability_digest"] != capabilities["mcp_capability_digest"]:
        raise RuntimeError("Handoff MCP capability digest does not match current Codex config.")
    sources = payload["sources"]
    facts = payload["facts"]
    if not isinstance(sources, list) or len(sources) > _HANDOFF_MAX_SOURCES:
        raise RuntimeError("Handoff sources are invalid or exceed limit.")
    if not isinstance(facts, list) or len(facts) > _HANDOFF_MAX_FACTS:
        raise RuntimeError("Handoff facts are invalid or exceed limit.")
    selected_set = set(selected)
    source_keys: list[str] = []
    server_tools = capabilities["server_tools"]
    for source in sources:
        if not isinstance(source, dict) or set(source) - {"server", "tool"} or "server" not in source:
            raise RuntimeError("Handoff source shape is invalid.")
        server = source["server"]
        tool = source.get("tool")
        if not isinstance(server, str) or not server or len(server) > _HANDOFF_MAX_STRING:
            raise RuntimeError("Handoff source server is invalid.")
        if server not in server_tools:
            raise RuntimeError(f"Handoff source server is unknown: {server}")
        if tool is not None and (not isinstance(tool, str) or not tool or len(tool) > _HANDOFF_MAX_STRING):
            raise RuntimeError("Handoff source tool is invalid.")
        if tool is not None and tool not in server_tools[server]:
            raise RuntimeError(f"Handoff source tool is unknown: {server}.{tool}")
        source_key = f"{server}.{tool}" if tool is not None else server
        if source_key in source_keys:
            raise RuntimeError("Handoff sources must be unique.")
        if selected and source_key not in selected_set:
            raise RuntimeError(f"Handoff source was not selected: {source_key}")
        source_keys.append(source_key)
    for fact in facts:
        if not isinstance(fact, dict) or set(fact) != {"source", "value"}:
            raise RuntimeError("Handoff fact shape is invalid.")
        source_index = fact["source"]
        if not isinstance(source_index, int) or isinstance(source_index, bool) or not 0 <= source_index < len(sources):
            raise RuntimeError("Handoff fact source index is invalid.")
        _reject_sensitive_value(fact["value"])
    constraints = payload.get("constraints", [])
    if not isinstance(constraints, list) or len(constraints) > 32 or any(
        not isinstance(item, str) or len(item) > _HANDOFF_MAX_STRING for item in constraints
    ):
        raise RuntimeError("Handoff constraints are invalid.")
    return path, payload

def _canonicalize_handoff_for_prompt(payload: dict[str, object]) -> dict[str, object]:
    sources = payload["sources"]
    facts = payload["facts"]
    if not isinstance(sources, list) or not isinstance(facts, list):
        return payload
    if any(
        not isinstance(fact, dict) or not isinstance(fact.get("source"), int)
        for fact in facts
    ):
        return payload

    source_order = sorted(range(len(sources)), key=lambda index: _sha256_json(sources[index]))
    source_indexes = {old: new for new, old in enumerate(source_order)}
    canonical_facts = [
        {
            **fact,
            "source": source_indexes[fact["source"]],
        }
        for fact in facts
    ]
    canonical_facts.sort(key=_sha256_json)
    return {
        **payload,
        "sources": [sources[index] for index in source_order],
        "facts": canonical_facts,
    }

def _handoff_stdin(argv: list[str], payload: dict[str, object]) -> str:
    canonical_payload = _canonicalize_handoff_for_prompt(payload)
    delegated_payload = {
        "schema": canonical_payload["schema"],
        "sources": canonical_payload["sources"],
        "facts": canonical_payload["facts"],
        "constraints": canonical_payload.get("constraints", []),
    }
    instruction = (
        " Use this validated Codex MCP handoff payload: "
        f"{json.dumps(delegated_payload, separators=(',', ':'), sort_keys=True)}. "
        "Use only its facts; do not call MCP tools."
    )
    for index, argument in enumerate(argv):
        if argument in {"-n", "--non-interactive"}:
            if index + 1 >= len(argv) or argv[index + 1].startswith("-"):
                raise RuntimeError("Handoff task text is missing.")
            task = argv[index + 1] + instruction
            argv[index : index + 2] = ["--stdin"]
            return task
        for option in ("-n=", "--non-interactive="):
            if argument.startswith(option):
                task = argument[len(option) :] + instruction
                argv[index] = "--stdin"
                return task
    raise RuntimeError("`--handoff-file` requires non-interactive task text via `-n`.")


def _native_file_tool_root(repo_root: Path) -> str:
    resolved_root = repo_root.resolve()
    if resolved_root.drive:
        return "/" + resolved_root.relative_to(Path(resolved_root.anchor)).as_posix()
    return resolved_root.as_posix()


def _bounded_task_context(repo_root: Path) -> str:
    host_root = repo_root.resolve()
    tool_root = _native_file_tool_root(repo_root)
    return (
        f" Host repository root: `{host_root}`. Native filesystem tool root: `{tool_root}`. "
        "Use host root for Git and shell commands; use tool root for filesystem tool paths. "
        "These roots refer to the same checkout. "
        "do not use `/workspace/...` or Windows drive syntax. Read only named source, test, "
        "and text files with filesystem tools. Never use filesystem tools on database, binary, "
        "archive, or runtime artifacts; examples: `*.sqlite`, `*.sqlite3`, `*.db`, `*-wal`, "
        "`*-shm`, `*-journal`, `*.zip`, `*.tar`, `*.gz`, `*.7z`, `*.bin`, `*.exe`, images, "
        "or media. For SQLite evidence, use launcher-authorized `py` from repository root with "
        "stdlib `sqlite3` read-only URI mode: "
        '`sqlite3.connect("file:<repo-relative-path>?mode=ro", uri=True)`. Run `py` directly; '
        "do not prefix it with `cd`, shell operators, or wrappers. For `py -c`, use one "
        "expression; never use `;`."
    )


def _append_bounded_task_context(argv: list[str], repo_root: Path) -> None:
    context = _bounded_task_context(repo_root)
    for index, argument in enumerate(argv):
        if argument in {"-n", "--non-interactive"}:
            if index + 1 >= len(argv) or argv[index + 1].startswith("-"):
                raise RuntimeError("DeepAgents task text is missing.")
            argv[index + 1] += context
            return
        for option in ("-n=", "--non-interactive="):
            if argument.startswith(option):
                argv[index] += context
                return


def _task_argument(argv: list[str]) -> str:
    for index, argument in enumerate(argv):
        if argument in {"-n", "--non-interactive"}:
            if index + 1 >= len(argv) or argv[index + 1].startswith("-"):
                raise RuntimeError("Tura task text is missing.")
            return argv[index + 1]
        for option in ("-n=", "--non-interactive="):
            if argument.startswith(option):
                task = argument[len(option) :]
                if not task:
                    raise RuntimeError("Tura task text is missing.")
                return task
    raise RuntimeError("Tura worker requires non-interactive task text via `-n`.")


def _tura_worker_task(
    argv: list[str],
    repo_root: Path,
    role_name: str,
    developer_instructions: str,
    payload: dict[str, object],
) -> str:
    canonical_payload = _canonicalize_handoff_for_prompt(payload)
    delegated_payload = {
        "schema": canonical_payload["schema"],
        "sources": canonical_payload["sources"],
        "facts": canonical_payload["facts"],
        "constraints": canonical_payload.get("constraints", []),
    }
    return (
        "Bounded task guidance for profile `"
        + role_name
        + "` (task guidance, not a Tura system/developer message):\n"
        + developer_instructions.strip()
        + "\n"
        + _PROJECT_GUIDANCE_INSTRUCTION
        + "\n"
        + _bounded_task_context(repo_root)
        + "\nCaller task:\n"
        + _task_argument(argv)
        + "\nValidated Codex MCP handoff facts (use only these facts; do not call MCP tools):\n"
        + json.dumps(delegated_payload, separators=(",", ":"), sort_keys=True)
    )


def _tura_worker_argv(
    executable: Path,
    repo_root: Path,
    model: str,
    session_id: str,
    task: str,
) -> list[str]:
    return [
        str(executable),
        "--quiet",
        "--json",
        "--sandbox",
        "--session-id",
        session_id,
        "--agent-id",
        "balanced",
        "-C",
        str(repo_root.resolve()),
        "-m",
        f"openai/{model}",
        task,
    ]


def _tura_worker_environment(
    api_key: str,
    provider_config: Path,
    repo_root: Path,
) -> dict[str, str]:
    environment = os.environ.copy()
    for key in ("OPENAI_BASE_URL", "OPENAI_API_BASE", "TURA_PROVIDER_CONFIG", "TURA_PROJECT_ROOT"):
        environment.pop(key, None)
    environment["OPENAI_API_KEY"] = api_key
    environment["TURA_PROVIDER_CONFIG"] = str(provider_config.resolve())
    environment["TURA_PROJECT_ROOT"] = str(repo_root.resolve())
    environment["PYTHONUTF8"] = "1"
    environment["PYTHONIOENCODING"] = "utf-8"
    return environment


def _worker_timeout(
    argv: list[str],
    *,
    default: float | None,
    worker_name: str,
) -> float | None:
    for index, argument in enumerate(argv):
        if argument == "--timeout":
            if index + 1 >= len(argv):
                raise RuntimeError(f"{worker_name} worker requires a value for `--timeout`.")
            value = argv[index + 1]
        elif argument.startswith("--timeout="):
            value = argument.split("=", 1)[1]
        else:
            continue
        try:
            timeout = float(value)
        except ValueError as exc:
            raise RuntimeError(
                f"{worker_name} worker timeout must be a positive number."
            ) from exc
        if timeout <= 0:
            raise RuntimeError(f"{worker_name} worker timeout must be a positive number.")
        return timeout
    return default

def _create_windows_job(process: subprocess.Popen[object]) -> object | None:
    return _owned_process._create_windows_job(process) if os.name == "nt" else None

def _close_windows_job(job: object | None) -> bool:
    return _owned_process._close_windows_job(job)

def _kill_windows_process_tree(pid: int) -> bool:
    return _owned_process._kill_windows_process_tree(pid)


def _run_bounded_worker(
    argv: list[str],
    environment: dict[str, str],
    repo_root: Path,
    handoff_stdin: str | None,
    timeout: float | None,
    worker_name: str,
) -> int:
    if timeout is None or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError(f"{worker_name} worker requires a finite timeout greater than zero.")
    result = run_owned_process(
        argv,
        cwd=repo_root,
        env=environment,
        timeout=timeout,
        input_data=handoff_stdin,
        capture_output=False,
        popen_factory=subprocess.Popen,
        platform_name=os.name,
        create_job=_create_windows_job,
        close_job=_close_windows_job,
        kill_tree=_kill_windows_process_tree,
    )
    if result.status == "success":
        return result.returncode or 0
    facts = _WorkerLifecycleFacts(
        "failed",
        result.returncode,
        "unknown" if not result.cleanup_confirmed else "terminated",
        result.cleanup_confirmed,
    )
    if result.status == "BLOCKED":
        message = (
            f"{worker_name} worker timed out; child process tree cleanup is unconfirmed."
            if result.reason == "timeout"
            else f"{worker_name} worker {result.reason or 'process cleanup'} is unconfirmed;"
        )
        raise _WorkerLifecycleError(
            message + " generated role views preserved for recovery.",
            facts,
        )
    if result.returncode is not None:
        return result.returncode
    if result.error is not None:
        raise _WorkerLifecycleError(
            f"{worker_name} worker failed after process creation.",
            facts,
        ) from result.error
    raise _WorkerLifecycleError(
        f"{worker_name} worker {result.status.replace('_', ' ')}; child process tree terminated.",
        facts,
    )

def _run_tura_worker(
    argv: list[str],
    environment: dict[str, str],
    repo_root: Path,
    timeout: float,
) -> int:
    return _run_bounded_worker(argv, environment, repo_root, None, timeout, "Tura")

def _run_deepagents_worker(
    argv: list[str],
    environment: dict[str, str],
    repo_root: Path,
    handoff_stdin: str | None,
    timeout: float,
) -> int:
    return _run_bounded_worker(
        argv,
        environment,
        repo_root,
        handoff_stdin,
        timeout,
        "DeepAgents",
    )


def _find_dcode() -> str | None:
    return next(
        (
            str(candidate)
            for candidate in (
                Path.home() / ".local" / "share" / "dcode-project" / "bin" / "dcode.exe",
                Path.home() / ".local" / "bin" / "dcode.exe",
                Path.home() / ".local" / "bin" / "dcode",
            )
            if candidate.is_file()
        ),
        None,
    ) or shutil.which("dcode")


def _runtime_environment(base_url: str, api_key: str) -> dict[str, str]:
    environment = os.environ.copy()
    environment["PYTHONUTF8"] = "1"
    environment["PYTHONIOENCODING"] = "utf-8"
    environment["DEEPAGENTS_CODE_AUTO_UPDATE"] = "0"
    if os.name == "nt":
        environment["DEEPAGENTS_CODE_UI_CHARSET_MODE"] = "ascii"
        environment["LOG_COLOR"] = "false"
    environment["DEEPAGENTS_CODE_OPENAI_BASE_URL"] = base_url
    environment["DEEPAGENTS_CODE_OPENAI_API_KEY"] = api_key
    environment["OPENAI_BASE_URL"] = base_url
    environment["OPENAI_API_KEY"] = api_key
    return environment


def _deepagents_home() -> Path:
    configured = os.environ.get("DEEPAGENTS_HOME")
    if configured:
        return Path(os.path.expandvars(configured)).expanduser().resolve()
    return Path.home() / ".deepagents"


def _reject_conflicting_user_openai_base_url() -> None:
    config_path = _deepagents_home() / "config.toml"
    if not config_path.exists():
        return
    values = _load_toml(config_path, "DeepAgents user config")
    models = values.get("models")
    providers = models.get("providers") if isinstance(models, dict) else None
    openai = providers.get("openai") if isinstance(providers, dict) else None
    if isinstance(openai, dict) and isinstance(openai.get("base_url"), str) and openai["base_url"].strip():
        raise RuntimeError(
            f"Remove conflicting OpenAI base_url from user config: {config_path}"
        )


def main(argv: list[str]) -> int:
    _reject_unmanaged_runtime_options(argv)
    (
        child_argv,
        selection_values,
        handoff_file,
        role_name,
        explicit_executor,
        result_file_value,
        attempt_id,
        assignment_id_value,
        repository_identity,
        task_sha256,
        grant_digest_value,
        prior_attempt_known,
    ) = _controller_options(argv)
    child_argv, local_capabilities = _extract_local_capabilities(child_argv)
    config = _load_toml(_config_path(), "dcode-project config")
    repo_root = _repo_root()
    executor = _resolve_executor(config, explicit_executor)
    result_file = _result_file_path(result_file_value) if result_file_value is not None else None
    if result_file is not None and attempt_id is None:
        raise RuntimeError("dcode-project requires `--attempt-id` with `--result-file`.")
    if result_file is not None and executor != "deepagents":
        raise RuntimeError("`--result-file` is supported only for DeepAgents task execution.")
    if assignment_id_value is not None and executor != "deepagents":
        raise RuntimeError("`--assignment-id` is supported only for DeepAgents task execution.")
    if assignment_id_value is not None:
        if attempt_id is None or repository_identity is None or task_sha256 is None or grant_digest_value is None:
            raise RuntimeError(
                "dcode-project requires attempt, repository, task, and grant bindings with `--assignment-id`."
            )
    binding = _runtime_binding(config)
    model = binding.model
    base_url = binding.base_url
    provider_name = binding.provider_name
    codex_config = binding.codex_config
    deepagents_model_params = (
        _deepagents_model_params(codex_config, provider_name)
        if executor == "deepagents"
        else None
    )
    needs_mcp_capabilities = bool(
        selection_values or handoff_file or ("--print-config" in child_argv)
    )
    capabilities = (
        _mcp_capabilities(codex_config)
        if needs_mcp_capabilities
        else {
            "mcp_servers": [],
            "mcp_tools": [],
            "server_tools": {},
            "mcp_capability_digest": _sha256_json({"mcp_servers": {}}),
        }
    )
    mcp_selection = _mcp_selection_state(selection_values, capabilities)
    selected = list(mcp_selection["effective_mcp"])
    roles = _load_roles(repo_root, provider_name)
    role_by_name = {str(role["name"]): role for role in roles}
    selected_role = role_by_name.get(role_name) if role_name is not None else None
    if role_name is not None and selected_role is None:
        raise RuntimeError(f"Unknown role `{role_name}`.")
    if "--print-config" in child_argv and len(child_argv) == 1:
        payload: dict[str, object] = {
            "controller_model": f"openai:{model}",
            "provider": provider_name,
            "role_models": {str(role["name"]): f"openai:{role['model']}" for role in roles},
            "mcp_servers": capabilities["mcp_servers"],
            "mcp_tools": capabilities["mcp_tools"],
            **mcp_selection,
            "selected_mcp": mcp_selection["effective_mcp"],
            "default_executor": config.get("delegation", {}).get("default_executor")
            if isinstance(config.get("delegation"), dict)
            else None,
            "selected_executor": executor,
            "deepagents_model_params": deepagents_model_params,
            "mcp_capability_digest": capabilities["mcp_capability_digest"],
            "roles_path": str(repo_root / ".deepagents" / "agents"),
        }
        paths = config.get("paths")
        if isinstance(paths, dict):
            for key in ("tura_executable", "tura_provider_config"):
                value = paths.get(key)
                if isinstance(value, str) and value.strip():
                    path = Path(value).expanduser()
                    payload[key] = str(path)
                    if key == "tura_executable" and path.is_file():
                        payload["tura_executable_sha256"] = _sha256_file(path)
        if selected_role is not None:
            payload["selected_role"] = selected_role["name"]
            payload["effective_model"] = f"openai:{selected_role['model']}"
            payload["runtime_binding_digest"] = _runtime_binding_digest(
                provider_name,
                model,
                str(selected_role["model"]),
                base_url,
                deepagents_model_params,
            )
        print(
            json.dumps(payload, sort_keys=True)
        )
        return 0
    if selected_role is None:
        names = "|".join(sorted(role_by_name))
        raise RuntimeError(f"dcode-project requires `--role <{names}>` for task execution.")
    if executor == "tura":
        executable, provider_config = _tura_worker_paths(config)
        if handoff_file is None:
            handoff_payload: dict[str, object] = {
                "schema": _HANDOFF_SCHEMA,
                "sources": [],
                "facts": [],
                "constraints": [],
            }
        else:
            _, handoff_payload = _validate_handoff(handoff_file, capabilities, selected)
        task = _tura_worker_task(
            child_argv,
            repo_root,
            str(selected_role["name"]),
            str(selected_role["developer_instructions"]),
            handoff_payload,
        )
        session_id = f"dcode-project-{uuid.uuid4().hex}"
        tura_argv = _tura_worker_argv(
            executable,
            repo_root,
            str(selected_role["model"]),
            session_id,
            task,
        )
        return _run_tura_worker(
            tura_argv,
            _tura_worker_environment(
                binding.read_api_key(),
                provider_config,
                repo_root,
            ),
            repo_root,
            _worker_timeout(child_argv, default=120.0, worker_name="Tura"),
        )
    _append_bounded_task_context(child_argv, repo_root)
    handoff_stdin: str | None = None
    if handoff_file is not None:
        _, payload = _validate_handoff(handoff_file, capabilities, selected)
        handoff_stdin = _handoff_stdin(child_argv, payload)
    _reject_conflicting_user_openai_base_url()
    dcode = _find_dcode()
    if not dcode:
        raise RuntimeError("DeepAgents Code is not installed. Run scripts/setup_deepagents_runtime.ps1.")
    environment = _runtime_environment(base_url, binding.read_api_key())
    shell_capabilities = _resolve_worker_shell_capabilities(local_capabilities, environment)
    attempt_guard_binding = None
    if assignment_id_value is not None:
        attempt_guard_binding = {
            "assignment_id": assignment_id_value,
            "attempt_id": str(attempt_id),
            "executor": executor,
            "repository_identity": str(repository_identity),
            "task_sha256": str(task_sha256),
            "grant_digest": str(grant_digest_value),
        }
    with _role_views_lock(repo_root):
        attempt_claim = None
        if attempt_guard_binding is not None:
            attempt_claim = _claim_attempt(
                **attempt_guard_binding,
                repo_root=repo_root,
                result_file=result_file,
                prior_attempt_known=prior_attempt_known,
            )
            if attempt_claim.get("action") == "RECONCILE":
                raise RuntimeError("DeepAgents assignment requires explicit reconciliation before launch.")
            if attempt_claim.get("idempotent"):
                raise RuntimeError("DeepAgents attempt already has an active or settled claim; no launch performed.")
        _write_role_views(repo_root, roles)
        cleanup_allowed = True
        worker_state = "not_started"
        worker_exit_code: int | None = None
        descendant_state = "not_started"
        role_views_state = "unknown"
        cleanup_details: dict[str, object] = {}
        recovery_required = False
        cleanup_error: Exception | None = None
        try:
            dcode_argv = [
                dcode,
                "-M",
                f"openai:{selected_role['model']}",
                "--model-params",
                json.dumps(deepagents_model_params, separators=(",", ":"), sort_keys=True),
                *_FIXED_LOCAL_CAPABILITY_OPTIONS,
                "--shell-allow-list",
                ",".join(shell_capabilities["effective"]),
                *(arg for arg in child_argv if arg != "--no-mcp"),
            ]
            if selection_values:
                with _direct_mcp_runtime(
                    repo_root,
                    codex_config,
                    selected,
                    environment,
                ) as mcp_config_path:
                    worker_exit_code = _run_deepagents_worker(
                        [*dcode_argv, "--mcp-config", str(mcp_config_path)],
                        environment,
                        repo_root,
                        handoff_stdin,
                        _worker_timeout(
                            child_argv,
                            default=_DEEPAGENTS_DEFAULT_TIMEOUT,
                            worker_name="DeepAgents",
                        ),
                    )
            else:
                worker_exit_code = _run_deepagents_worker(
                    [*dcode_argv, "--no-mcp"],
                    environment,
                    repo_root,
                    handoff_stdin,
                    _worker_timeout(
                        child_argv,
                        default=_DEEPAGENTS_DEFAULT_TIMEOUT,
                        worker_name="DeepAgents",
                    ),
                )
            worker_state = "exited"
            descendant_state = "terminated"
        except _WorkerRecoveryBlocked as exc:
            cleanup_allowed = exc.facts.termination_proven
            worker_state = exc.facts.worker_state
            worker_exit_code = exc.facts.exit_code
            descendant_state = exc.facts.descendant_state
            recovery_required = True
            raise
        except _WorkerLifecycleError as exc:
            cleanup_allowed = exc.facts.termination_proven
            worker_state = exc.facts.worker_state
            worker_exit_code = exc.facts.exit_code
            descendant_state = exc.facts.descendant_state
            recovery_required = not exc.facts.termination_proven
            raise
        except OSError:
            worker_state = "start_failed"
            descendant_state = "not_started"
            raise
        except Exception:
            worker_state = "failed"
            descendant_state = "unknown"
            raise
        finally:
            if cleanup_allowed:
                try:
                    cleanup_details = _remove_role_views(repo_root, roles)
                except Exception as exc:
                    role_views_state = "unverified"
                    recovery_required = True
                    cleanup_details = {
                        "remaining_paths": [],
                        "marker_state": "unknown",
                    }
                    cleanup_error = exc
                else:
                    role_views_state = str(cleanup_details.get("state", "unverified"))
                    recovery_required = recovery_required or role_views_state != "removed"
            else:
                role_views_state = "preserved"
                cleanup_details = {
                    "remaining_paths": sorted(
                        str(_role_view_path(repo_root / ".deepagents" / "agents", role["name"]).relative_to(repo_root))
                        for role in roles
                        if _role_view_path(repo_root / ".deepagents" / "agents", role["name"]).exists()
                        or _role_view_path(repo_root / ".deepagents" / "agents", role["name"]).is_symlink()
                    ),
                    "marker_state": "retained",
                }
            if result_file is not None:
                _publish_result_receipt(
                    result_file,
                    attempt_id=str(attempt_id),
                    worker_state=worker_state,
                    worker_exit_code=worker_exit_code,
                    descendant_state=descendant_state,
                    role_views_state=role_views_state,
                    recovery_required=recovery_required,
                    shell_capabilities=shell_capabilities,
                    cleanup_details=cleanup_details,
                )
            if attempt_guard_binding is not None:
                _settle_attempt(
                    assignment_id=str(attempt_guard_binding["assignment_id"]),
                    binding=attempt_guard_binding,
                    settlement_proven=(
                        worker_state in {"exited", "failed", "start_failed"}
                        and descendant_state in {"terminated", "not_started"}
                        and role_views_state == "removed"
                        and not recovery_required
                    ),
                )
            if cleanup_error is not None:
                raise cleanup_error
        return int(worker_exit_code) if worker_exit_code is not None else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except RuntimeError as exc:
        print(f"dcode-project: {exc}", file=sys.stderr)
        raise SystemExit(2)
