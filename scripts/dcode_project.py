"""Launch DeepAgents with local Codex binding and shared project roles."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tomllib


_ROLE_VIEWS_MARKER = ".dcode-project-owned"
_ROLE_VIEWS_SCHEMA = 1
_LEGACY_ROLE_VIEWS_MARKER = "dcode-project owns this directory.\n"
_ALLOWED_RUNTIME_FLAGS = {
    "--print-config",
    "--json",
    "-q",
    "--quiet",
    "--no-stream",
    "--stdin",
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
}


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
    completed = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode:
        raise RuntimeError("Run dcode-project inside a Git repository.")
    return Path(completed.stdout.strip()).resolve()


def _default_role_model(role_name: str, controller_model: str) -> str:
    if role_name == "high":
        return controller_model
    match = re.fullmatch(r"(.+)-high", controller_model)
    if match and role_name in {"normal", "low"}:
        return f"{match.group(1)}-{role_name}"
    raise RuntimeError(
        f"Missing local model binding for role `{role_name}`. Add it under `[roles]` in {_config_path()}."
    )


def _load_roles(
    repo_root: Path,
    role_models: dict[str, object],
    controller_model: str,
) -> list[dict[str, str]]:
    roles_root = repo_root / "agents"
    roles: list[dict[str, str]] = []
    for source in sorted(roles_root.glob("*.toml")):
        values = _load_toml(source, "role template")
        required = {"name", "description", "developer_instructions"}
        if set(values) != required:
            raise RuntimeError(f"Unsupported role template fields: {source}")
        name = _required_string(values, "name", str(source))
        if source.stem != name:
            raise RuntimeError(f"Role filename must match name: {source}")
        model = role_models.get(name)
        if model is None:
            model = _default_role_model(name, controller_model)
        if not isinstance(model, str) or not model.strip():
            raise RuntimeError(f"Invalid local model binding for role `{name}`.")
        roles.append(
            {
                "name": name,
                "description": _required_string(values, "description", str(source)),
                "developer_instructions": _required_string(
                    values, "developer_instructions", str(source)
                ),
                "model": model.strip(),
            }
        )
    if not roles:
        raise RuntimeError(f"No role templates found: {roles_root}")
    return roles


def _role_view_path(agents_root: Path, role_name: str) -> Path:
    return agents_root / role_name / "AGENTS.md"


def _role_view_content(role: dict[str, str]) -> str:
    model = f"openai:{role['model']}"
    return (
        "---\n"
        f"name: {json.dumps(role['name'])}\n"
        f"description: {json.dumps(role['description'])}\n"
        f"model: {json.dumps(model)}\n"
        "---\n\n"
        f"{role['developer_instructions']}\n"
    )


def _owned_views_marker(roles: list[dict[str, str]]) -> str:
    views = {
        role["name"]: _role_view_content(role)
        for role in roles
    }
    return json.dumps(
        {"schema": _ROLE_VIEWS_SCHEMA, "views": views},
        sort_keys=True,
    ) + "\n"


def _read_owned_views(marker: Path, roles: list[dict[str, str]]) -> dict[str, str]:
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


def _remove_role_views(repo_root: Path, roles: list[dict[str, str]]) -> None:
    agents_root = repo_root / ".deepagents" / "agents"
    marker = agents_root / _ROLE_VIEWS_MARKER
    if not marker.exists():
        return
    _remove_owned_views(agents_root, _read_owned_views(marker, roles))
    marker.unlink()
    _remove_empty_parents(agents_root, repo_root)


def _write_role_views(repo_root: Path, roles: list[dict[str, str]]) -> Path:
    agents_root = repo_root / ".deepagents" / "agents"
    marker = agents_root / _ROLE_VIEWS_MARKER
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


def _runtime_binding(config: dict[str, object]) -> tuple[str, str, str, str]:
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
    return model, base_url, _read_env_value(secret_file, secret_key), provider_name


def _find_dcode() -> str | None:
    return shutil.which("dcode") or next(
        (
            str(candidate)
            for candidate in (
                Path.home() / ".local" / "bin" / "dcode.exe",
                Path.home() / ".local" / "bin" / "dcode",
            )
            if candidate.is_file()
        ),
        None,
    )


def _runtime_environment(base_url: str, api_key: str) -> dict[str, str]:
    environment = os.environ.copy()
    environment["DEEPAGENTS_CODE_OPENAI_BASE_URL"] = base_url
    environment["DEEPAGENTS_CODE_OPENAI_API_KEY"] = api_key
    environment["OPENAI_BASE_URL"] = base_url
    environment["OPENAI_API_KEY"] = api_key
    return environment


def _reject_conflicting_user_openai_base_url() -> None:
    config_path = Path.home() / ".deepagents" / "config.toml"
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
    config = _load_toml(_config_path(), "dcode-project config")
    role_models = config.get("roles", {})
    if not isinstance(role_models, dict):
        raise RuntimeError("Invalid local `[roles]` configuration.")
    repo_root = _repo_root()
    model, base_url, api_key, provider_name = _runtime_binding(config)
    roles = _load_roles(repo_root, role_models, model)
    if argv == ["--print-config"]:
        print(
            json.dumps(
                {
                    "controller_model": f"openai:{model}",
                    "provider": provider_name,
                    "role_models": {role["name"]: f"openai:{role['model']}" for role in roles},
                    "roles_path": str(repo_root / ".deepagents" / "agents"),
                },
                sort_keys=True,
            )
        )
        return 0
    _reject_conflicting_user_openai_base_url()
    dcode = _find_dcode()
    if not dcode:
        raise RuntimeError("DeepAgents Code is not installed. Run scripts/setup_deepagents_runtime.ps1.")
    environment = _runtime_environment(base_url, api_key)
    _write_role_views(repo_root, roles)
    try:
        completed = subprocess.run(
            [dcode, "-M", f"openai:{model}", *(arg for arg in argv if arg != "--no-mcp"), "--no-mcp"],
            env=environment,
        )
        return completed.returncode
    finally:
        _remove_role_views(repo_root, roles)


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except RuntimeError as exc:
        print(f"dcode-project: {exc}", file=sys.stderr)
        raise SystemExit(2)
