"""
@meta
name: test_dcode_project
type: test
scope: unit
domain: runtime
covers:
  - User-local DeepAgents launcher materializes role views from canonical templates
  - Local role-model binding selects each delegated tier
tags:
  - fast
  - ci-safe
lifecycle:
  status: active
"""

from __future__ import annotations

import importlib.util
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from project_os_test_paths import add_runtime_import_roots, runtime_script

add_runtime_import_roots()
ROOT = Path(__file__).resolve().parent.parent
LAUNCHER_PATH = runtime_script("dcode_project.py")


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {path.name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


LAUNCHER = load_module("dcode_project", LAUNCHER_PATH)


def write_role(
    root: Path,
    name: str,
    *,
    model_provider: str = "9router",
    model: str | None = None,
    rank: int = 20,
) -> None:
    (root / "agents").mkdir(parents=True, exist_ok=True)
    model = model or f"combo-{name}"
    (root / "agents" / f"{name}.toml").write_text(
        f'name = "{name}"\n'
        f'model_provider = "{model_provider}"\n'
        f'model = "{model}"\n'
        f'rank = {rank}\n'
        'description = "Role description"\n'
        'developer_instructions = "Return ROLE_OK."\n',
        encoding="utf-8",
    )


def runtime_binding(
    codex_config: dict[str, object],
    *,
    model: str = "combo-high",
    base_url: str = "https://provider.example/v1",
    provider_name: str = "9router",
    secret_file: Path | None = None,
    secret_key: str = "API_KEY",
) -> object:
    return LAUNCHER._RuntimeBinding(
        model=model,
        base_url=base_url,
        provider_name=provider_name,
        secret_file=secret_file or Path("missing-secret.env"),
        secret_key=secret_key,
        codex_config=codex_config,
    )


def start_lock_holder(root: Path, *, write_views: bool = False) -> subprocess.Popen[str]:
    script = """
import importlib.util
import pathlib
import sys

launcher_path = pathlib.Path(sys.argv[1])
root = pathlib.Path(sys.argv[2])
spec = importlib.util.spec_from_file_location("lock_holder_launcher", launcher_path)
launcher = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = launcher
spec.loader.exec_module(launcher)
with launcher._role_views_lock(root):
    if sys.argv[3] == "write":
        launcher._write_role_views(root, launcher._load_roles(root, "9router"))
    print("READY", flush=True)
    sys.stdin.readline()
"""
    return subprocess.Popen(
        [sys.executable, "-c", script, str(LAUNCHER_PATH), str(root), "write" if write_views else "hold"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def tura_config(
    tmp_path: Path,
    *,
    default_executor: str = "tura",
) -> dict[str, object]:
    return {
        "delegation": {"default_executor": default_executor},
        "paths": {
            "tura_executable": str(tmp_path / "tura.exe"),
            "tura_provider_config": str(tmp_path / "providers.toml"),
        },
    }


def test_executor_resolution_prefers_explicit_then_configured_default(tmp_path: Path) -> None:
    config = tura_config(tmp_path)

    assert LAUNCHER._resolve_executor(config, "deepagents") == "deepagents"
    assert LAUNCHER._resolve_executor(config, None) == "tura"


@pytest.mark.parametrize(
    ("config", "explicit", "message"),
    [
        ({}, None, "default_executor"),
        ({"delegation": {"default_executor": "codex"}}, None, "executor"),
        ({"delegation": {"default_executor": "tura"}}, "codex", "executor"),
    ],
)
def test_executor_resolution_rejects_missing_or_invalid_values(
    config: dict[str, object],
    explicit: str | None,
    message: str,
) -> None:
    with pytest.raises(RuntimeError, match=message):
        LAUNCHER._resolve_executor(config, explicit)


def test_controller_options_extracts_executor_once() -> None:
    child, selections, handoff, role, executor = LAUNCHER._controller_options(
        ["--executor", "tura", "--role", "normal", "-n", "task"]
    )

    assert child == ["-n", "task"]
    assert selections == []
    assert handoff is None
    assert role == "normal"
    assert executor == "tura"


def test_tura_argv_contains_bounded_worker_contract(tmp_path: Path) -> None:
    argv = LAUNCHER._tura_worker_argv(
        Path("C:/tools/tura.exe"),
        tmp_path,
        "combo-normal",
        "session-a",
        "inspect files",
    )

    assert argv[:2] == [str(Path("C:/tools/tura.exe")), "--quiet"]
    assert "--json" in argv
    assert "--sandbox" in argv
    assert "--session-id" in argv
    assert argv[argv.index("--session-id") + 1] == "session-a"
    assert argv[argv.index("--agent-id") + 1] == "balanced"
    assert argv[argv.index("-C") + 1] == str(tmp_path)
    assert argv[argv.index("-m") + 1] == "openai/combo-normal"
    assert argv[-1] == "inspect files"


def test_tura_task_labels_profile_guidance_and_handoff_once(tmp_path: Path) -> None:
    argv = ["-n", "inspect files"]
    payload = {
        "schema": "codex.mcp.handoff.v1",
        "sources": [{"server": "context7", "tool": "query_docs"}],
        "facts": [{"source": 0, "value": "fact"}],
        "constraints": ["no MCP"],
    }

    task = LAUNCHER._tura_worker_task(
        argv,
        tmp_path,
        "normal",
        "Return ROLE_OK.",
        payload,
    )

    assert task.count("Return ROLE_OK.") == 1
    assert task.count('"schema":"codex.mcp.handoff.v1"') == 1
    assert "Bounded task guidance" in task
    assert task.count("Project guidance:") == 1
    assert "AGENTS.md" in task
    assert ".agents/skills/<name>/SKILL.md" in task
    assert "inspect files" in task
    assert "handoff.json" not in task


def test_tura_environment_owns_provider_and_workspace_values(tmp_path: Path) -> None:
    os.environ["OPENAI_BASE_URL"] = "https://direct-provider.invalid/v1"
    environment = LAUNCHER._tura_worker_environment(
        "secret", tmp_path / "providers.toml", tmp_path
    )

    assert environment["OPENAI_API_KEY"] == "secret"
    assert environment["TURA_PROVIDER_CONFIG"] == str(tmp_path / "providers.toml")
    assert environment["TURA_PROJECT_ROOT"] == str(tmp_path)
    assert "OPENAI_BASE_URL" not in environment
    assert "secret" not in environment.get("TURA_PROVIDER_CONFIG", "")
    os.environ.pop("OPENAI_BASE_URL", None)


def test_tura_worker_propagates_opaque_child_status(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    class FakeProcess:
        pid = 42

        def wait(self, timeout: float | None = None) -> int:
            assert timeout == 3
            return 7

    observed: dict[str, object] = {}

    def fake_popen(argv: list[str], **kwargs: object) -> FakeProcess:
        observed["argv"] = argv
        observed.update(kwargs)
        return FakeProcess()

    monkeypatch.setattr(LAUNCHER.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(LAUNCHER, "_create_windows_job", lambda process: "job")
    monkeypatch.setattr(LAUNCHER, "_close_windows_job", lambda job: None)

    assert LAUNCHER._run_tura_worker(
        ["tura", "task"], {"TURA_PROVIDER_CONFIG": "providers.toml"}, tmp_path, 3
    ) == 7
    assert observed["cwd"] == tmp_path


@pytest.mark.parametrize("handoff_stdin", [None, "handoff"])
def test_bounded_worker_preserves_stdin_and_status(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    handoff_stdin: str | None,
) -> None:
    class FakeProcess:
        returncode = 7

        def communicate(self, input: str, timeout: float | None = None) -> None:
            assert input == handoff_stdin
            assert timeout == 3

        def wait(self, timeout: float | None = None) -> int:
            assert timeout == 3
            return 7

    observed: dict[str, object] = {}

    def fake_popen(argv: list[str], **kwargs: object) -> FakeProcess:
        observed.update(argv=argv, kwargs=kwargs)
        return FakeProcess()

    monkeypatch.setattr(LAUNCHER.os, "name", "posix")
    monkeypatch.setattr(LAUNCHER.subprocess, "Popen", fake_popen)

    assert LAUNCHER._run_bounded_worker(
        ["worker", "task"], {}, tmp_path, handoff_stdin, 3, "worker"
    ) == 7
    assert observed["argv"] == ["worker", "task"]
    assert observed["kwargs"]["stdin"] is (
        subprocess.PIPE if handoff_stdin is not None else None
    )

def test_bounded_worker_terminates_timed_out_posix_process(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    class FakeProcess:
        pid = 42

        def __init__(self) -> None:
            self.killed = False
            self.waits = 0

        def wait(self, timeout: float | None = None) -> int:
            self.waits += 1
            if self.waits == 1:
                raise subprocess.TimeoutExpired(["worker"], timeout)
            return -9

        def kill(self) -> None:
            self.killed = True

    process = FakeProcess()
    monkeypatch.setattr(LAUNCHER.os, "name", "posix")
    monkeypatch.setattr(LAUNCHER.subprocess, "Popen", lambda *args, **kwargs: process)

    with pytest.raises(RuntimeError, match="worker timed out"):
        LAUNCHER._run_bounded_worker(
            ["worker"], {}, tmp_path, None, 3, "worker"
        )

    assert process.killed is True
    assert process.waits == 2

def test_deepagents_worker_reaps_windows_child_tree_after_normal_exit(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    class FakeProcess:
        pid = 42
        returncode = 0

        def communicate(self, input: str, timeout: float | None = None) -> None:
            assert input == "handoff"
            assert timeout == 3

        def wait(self, timeout: float | None = None) -> int:
            assert timeout == 3
            return 0

    observed: list[object] = []

    def fake_popen(argv: list[str], **kwargs: object) -> FakeProcess:
        return FakeProcess()

    def fake_close(job: object | None) -> None:
        observed.append(job)

    monkeypatch.setattr(LAUNCHER.os, "name", "nt")
    monkeypatch.setattr(LAUNCHER.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(LAUNCHER, "_create_windows_job", lambda process: "job")
    monkeypatch.setattr(LAUNCHER, "_close_windows_job", fake_close)

    assert LAUNCHER._run_deepagents_worker(
        ["dcode", "-n", "task"], {}, tmp_path, "handoff", 3
    ) == 0
    assert observed == ["job"]


def test_role_views_lock_rejects_competing_launch_without_mutation(tmp_path: Path) -> None:
    write_role(tmp_path, "normal")
    holder = start_lock_holder(tmp_path, write_views=True)
    assert holder.stdout is not None
    assert holder.stdout.readline().strip() == "READY"

    with pytest.raises(RuntimeError, match="owns role views"):
        with LAUNCHER._role_views_lock(tmp_path):
            pytest.fail("competing launch acquired role-view lock")

    assert (tmp_path / ".deepagents" / "agents" / "normal" / "AGENTS.md").is_file()
    assert holder.stdin is not None
    holder.stdin.write("stop\n")
    holder.stdin.flush()
    assert holder.wait(timeout=5) == 0


def test_role_views_lock_preserves_views_after_launcher_crash(tmp_path: Path) -> None:
    write_role(tmp_path, "normal")
    holder = start_lock_holder(tmp_path, write_views=True)
    assert holder.stdout is not None
    assert holder.stdout.readline().strip() == "READY"

    holder.kill()
    assert holder.wait(timeout=5) is not None
    view = tmp_path / ".deepagents" / "agents" / "normal" / "AGENTS.md"
    assert view.is_file()
    with LAUNCHER._role_views_lock(tmp_path):
        assert view.is_file()


def test_role_views_lock_allows_separate_worktrees(tmp_path: Path) -> None:
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    first_root.mkdir()
    second_root.mkdir()
    first = start_lock_holder(first_root)
    second = start_lock_holder(second_root)
    assert first.stdout is not None
    assert second.stdout is not None
    assert first.stdout.readline().strip() == "READY"
    assert second.stdout.readline().strip() == "READY"

    for process in (first, second):
        assert process.stdin is not None
        process.stdin.write("stop\n")
        process.stdin.flush()
    assert first.wait(timeout=5) == 0
    assert second.wait(timeout=5) == 0


def test_tura_worker_does_not_supply_adapter_cache_key() -> None:
    assert "prompt_cache_key" not in LAUNCHER._tura_worker_argv(
        Path("tura"), Path("repo"), "combo-low", "session-b", "task"
    )


def test_local_role_views_use_canonical_prompt_and_local_model_map(tmp_path: Path) -> None:
    write_role(tmp_path, "normal")

    roles = LAUNCHER._load_roles(tmp_path, "9router")
    agents_root = LAUNCHER._write_role_views(tmp_path, roles)
    rendered = (agents_root / "normal" / "AGENTS.md").read_text(encoding="utf-8")

    assert 'name: "normal"' in rendered
    assert 'model: "openai:combo-normal"' in rendered
    assert rendered.endswith("Return ROLE_OK.\n")
    assert (agents_root / ".dcode-project-owned").exists()


def test_local_role_views_refuse_unowned_directory(tmp_path: Path) -> None:
    write_role(tmp_path, "normal")
    unowned = tmp_path / ".deepagents" / "agents" / "custom"
    unowned.mkdir(parents=True)
    (unowned / "AGENTS.md").write_text("custom\n", encoding="utf-8")

    roles = LAUNCHER._load_roles(tmp_path, "9router")

    with pytest.raises(RuntimeError, match="user-owned"):
        LAUNCHER._write_role_views(tmp_path, roles)


def test_local_role_views_refuse_file_role_root(tmp_path: Path) -> None:
    write_role(tmp_path, "normal")
    agents_root = tmp_path / ".deepagents" / "agents"
    agents_root.parent.mkdir(parents=True)
    agents_root.write_text("stale\n", encoding="utf-8")

    roles = LAUNCHER._load_roles(tmp_path, "9router")

    with pytest.raises(RuntimeError, match="must be a directory"):
        LAUNCHER._write_role_views(tmp_path, roles)


def test_local_role_views_replace_empty_retired_directories(tmp_path: Path) -> None:
    write_role(tmp_path, "normal")
    (tmp_path / ".deepagents" / "agents" / "normal").mkdir(parents=True)

    roles = LAUNCHER._load_roles(tmp_path, "9router")
    agents_root = LAUNCHER._write_role_views(tmp_path, roles)

    assert (agents_root / ".dcode-project-owned").exists()
    assert (agents_root / "normal" / "AGENTS.md").exists()


def test_local_role_view_cleanup_removes_only_owned_files(tmp_path: Path) -> None:
    write_role(tmp_path, "normal")
    roles = LAUNCHER._load_roles(tmp_path, "9router")
    agents_root = LAUNCHER._write_role_views(tmp_path, roles)
    user_file = agents_root / "normal" / "notes.txt"
    user_file.write_text("retain\n", encoding="utf-8")

    LAUNCHER._remove_role_views(tmp_path, roles)

    assert not (agents_root / ".dcode-project-owned").exists()
    assert not (agents_root / "normal" / "AGENTS.md").exists()
    assert user_file.read_text(encoding="utf-8") == "retain\n"


def test_local_role_view_cleanup_keeps_unmarked_matching_view(tmp_path: Path) -> None:
    write_role(tmp_path, "normal")
    roles = LAUNCHER._load_roles(tmp_path, "9router")
    agents_root = tmp_path / ".deepagents" / "agents"
    view = agents_root / "normal" / "AGENTS.md"
    view.parent.mkdir(parents=True)
    view.write_text(LAUNCHER._role_view_content(roles[0]), encoding="utf-8")

    LAUNCHER._remove_role_views(tmp_path, roles)

    assert view.exists()


def test_local_role_views_refuse_user_file_after_owned_generation(tmp_path: Path) -> None:
    write_role(tmp_path, "normal")
    roles = LAUNCHER._load_roles(tmp_path, "9router")
    agents_root = LAUNCHER._write_role_views(tmp_path, roles)
    (agents_root / "custom.txt").write_text("retain\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="user-owned"):
        LAUNCHER._write_role_views(tmp_path, roles)


def test_local_role_view_write_failure_cleans_partial_generated_state(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    write_role(tmp_path, "normal")
    roles = LAUNCHER._load_roles(tmp_path, "9router")
    original_write_text = Path.write_text

    def fail_role_view(self: Path, data: str, *args: object, **kwargs: object) -> int:
        if self.name == "AGENTS.md":
            raise OSError("disk full")
        return original_write_text(self, data, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", fail_role_view)

    with pytest.raises(OSError, match="disk full"):
        LAUNCHER._write_role_views(tmp_path, roles)

    assert not (tmp_path / ".deepagents").exists()


def test_main_cleans_owned_role_views_after_dcode_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    write_role(tmp_path, "normal")
    secret_file = tmp_path / "secret.env"
    secret_file.write_text("API_KEY=secret\n", encoding="utf-8")
    config_path = tmp_path / "dcode-project.toml"
    config_path.write_text(
        '[delegation]\ndefault_executor = "deepagents"\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(LAUNCHER, "_config_path", lambda: config_path)
    monkeypatch.setattr(LAUNCHER, "_repo_root", lambda: tmp_path)
    monkeypatch.setattr(
        LAUNCHER,
        "_runtime_binding",
        lambda config: runtime_binding(
            {"model_providers": {"9router": {"wire_api": "chat"}}},
            secret_file=secret_file,
        ),
    )
    monkeypatch.setattr(
        LAUNCHER,
        "_mcp_capabilities",
        lambda config: {
            "mcp_servers": [],
            "mcp_tools": [],
            "server_tools": {},
            "mcp_capability_digest": "digest",
        },
    )
    monkeypatch.setattr(LAUNCHER, "_reject_conflicting_user_openai_base_url", lambda: None)
    monkeypatch.setattr(LAUNCHER, "_find_dcode", lambda: "dcode")

    def fail_dcode(*args: object, **kwargs: object) -> None:
        assert (tmp_path / ".deepagents" / "agents" / "normal" / "AGENTS.md").is_file()
        raise OSError("dcode unavailable")

    monkeypatch.setattr(LAUNCHER, "_run_deepagents_worker", fail_dcode)

    with pytest.raises(OSError, match="dcode unavailable"):
        LAUNCHER.main(["--role", "normal", "-n", "task"])

    assert not (tmp_path / ".deepagents").exists()


@pytest.mark.parametrize(
    ("argv", "message"),
    [
        (["-n", "task"], "requires `--role"),
        (["--role", "missing", "-n", "task"], "Unknown role `missing`"),
    ],
)
def test_main_rejects_missing_or_unknown_role_before_role_view_write(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    argv: list[str],
    message: str,
) -> None:
    write_role(tmp_path, "normal")
    config_path = tmp_path / "dcode-project.toml"
    config_path.write_text(
        '[delegation]\ndefault_executor = "deepagents"\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(LAUNCHER, "_config_path", lambda: config_path)
    monkeypatch.setattr(LAUNCHER, "_repo_root", lambda: tmp_path)
    monkeypatch.setattr(
        LAUNCHER,
        "_runtime_binding",
        lambda config: runtime_binding(
            {"model_providers": {"9router": {"wire_api": "chat"}}}
        ),
    )
    monkeypatch.setattr(
        LAUNCHER,
        "_mcp_capabilities",
        lambda config: {
            "mcp_servers": [],
            "mcp_tools": [],
            "server_tools": {},
            "mcp_capability_digest": "digest",
        },
    )

    with pytest.raises(RuntimeError, match=message):
        LAUNCHER.main(argv)

    assert not (tmp_path / ".deepagents").exists()


@pytest.mark.parametrize(
    "argument",
    [
        "--agent",
        "--model=combo-normal",
        "-Mcombo-normal",
        "--resume",
        "-rthread-id",
        "--yolo",
        "--mcp-config",
        "--trust-project-mcp",
        "--shell-allow-list",
        "--allow-fs-tools",
        "--interpreter-tools",
        "--sandbox",
        "--startup-cmd",
        "--max-retries",
        "--rubric-model",
        "--default-model",
        "--clear-default-model",
        "mcp",
    ],
)
def test_launcher_rejects_unmanaged_runtime_options(argument: str) -> None:
    with pytest.raises(RuntimeError, match="no Codex permission or MCP projection"):
        LAUNCHER._reject_unmanaged_runtime_options([argument])


def test_launcher_rejects_direct_stdin() -> None:
    with pytest.raises(RuntimeError, match="does not accept direct `--stdin`.*--handoff-file"):
        LAUNCHER._reject_unmanaged_runtime_options(["--stdin"])


def test_launcher_allows_bounded_noninteractive_options() -> None:
    LAUNCHER._reject_unmanaged_runtime_options(
        [
            "--print-config",
            "--role",
            "normal",
            "--json",
            "--max-turns",
            "4",
            "--timeout=120",
            "--rubric",
            "@acceptance.md",
            "--no-mcp",
            "-n",
            "task",
        ]
    )


def test_worker_timeout_defaults_are_executor_specific() -> None:
    assert LAUNCHER._worker_timeout(
        ["-n", "task"], default=None, worker_name="DeepAgents"
    ) is None
    assert LAUNCHER._worker_timeout(
        ["-n", "task"], default=120.0, worker_name="Tura"
    ) == 120.0
    assert LAUNCHER._worker_timeout(
        ["-n", "task", "--timeout=600"], default=None, worker_name="DeepAgents"
    ) == 600.0


@pytest.mark.parametrize(
    ("wire_api", "expected"),
    [("chat", {"use_responses_api": False}), ("responses", {"use_responses_api": True})],
)
def test_deepagents_model_params_follow_provider_wire_api(
    wire_api: str,
    expected: dict[str, bool],
) -> None:
    config = {"model_providers": {"9router": {"wire_api": wire_api}}}

    assert LAUNCHER._deepagents_model_params(config, "9router") == expected


def test_deepagents_model_params_reject_unknown_wire_api() -> None:
    config = {"model_providers": {"9router": {"wire_api": "legacy"}}}

    with pytest.raises(RuntimeError, match="wire_api"):
        LAUNCHER._deepagents_model_params(config, "9router")


def test_runtime_binding_digest_changes_with_wire_api() -> None:
    chat = LAUNCHER._runtime_binding_digest(
        "9router",
        "combo-high",
        "combo-ui",
        "https://provider.example/v1",
        {"use_responses_api": False},
    )
    responses = LAUNCHER._runtime_binding_digest(
        "9router",
        "combo-high",
        "combo-ui",
        "https://provider.example/v1",
        {"use_responses_api": True},
    )

    assert chat != responses


def test_runtime_binding_loads_codex_config_once_without_reading_secret(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    codex_path = tmp_path / "config.toml"
    codex_path.write_text(
        'model_provider = "9router"\n'
        'model = "combo-high"\n'
        '[model_providers."9router"]\n'
        'base_url = "https://provider.example/v1"\n'
        'wire_api = "responses"\n'
        ,
        encoding="utf-8",
    )
    config = {
        "paths": {
            "codex_config": str(codex_path),
            "secret_file": str(tmp_path / "missing.env"),
            "secret_key": "API_KEY",
        }
    }
    monkeypatch.setattr(LAUNCHER, "_read_env_value", lambda *args: pytest.fail("secret read"))

    binding = LAUNCHER._runtime_binding(config)

    assert binding.codex_config["model_providers"]["9router"]["wire_api"] == "responses"
    assert binding.secret_file == tmp_path / "missing.env"


def test_runtime_binding_digest_changes_with_worker_model() -> None:
    normal = LAUNCHER._runtime_binding_digest(
        "9router",
        "combo-high",
        "combo-normal",
        "https://provider.example/v1",
        {"use_responses_api": True},
    )
    high = LAUNCHER._runtime_binding_digest(
        "9router",
        "combo-high",
        "combo-high",
        "https://provider.example/v1",
        {"use_responses_api": True},
    )

    assert normal != high


@pytest.mark.parametrize("argument", ["--timeout", "--rubric"])
def test_launcher_rejects_missing_bounded_option_value(argument: str) -> None:
    with pytest.raises(RuntimeError, match="requires a value"):
        LAUNCHER._reject_unmanaged_runtime_options([argument])


@pytest.mark.parametrize(
    ("role_name", "model", "rank"),
    [
        ("low", "combo-low", 10),
        ("normal", "combo-normal", 20),
        ("high", "combo-high", 30),
        ("xhigh", "combo-xhigh", 40),
    ],
)
def test_main_uses_selected_role_model_and_fixed_local_capabilities(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    role_name: str,
    model: str,
    rank: int,
) -> None:
    for candidate_name, candidate_model, candidate_rank in [
        ("low", "combo-low", 10),
        ("normal", "combo-normal", 20),
        ("high", "combo-high", 30),
        ("xhigh", "combo-xhigh", 40),
    ]:
        write_role(tmp_path, candidate_name, model=candidate_model, rank=candidate_rank)
    secret_file = tmp_path / "secret.env"
    secret_file.write_text("API_KEY=secret\n", encoding="utf-8")
    config_path = tmp_path / "dcode-project.toml"
    config_path.write_text(
        '[delegation]\ndefault_executor = "deepagents"\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(LAUNCHER, "_config_path", lambda: config_path)
    monkeypatch.setattr(LAUNCHER, "_repo_root", lambda: tmp_path)
    monkeypatch.setattr(
        LAUNCHER,
        "_runtime_binding",
        lambda config: runtime_binding(
            {"model_providers": {"9router": {"wire_api": "chat"}}},
            secret_file=secret_file,
        ),
    )
    monkeypatch.setattr(
        LAUNCHER,
        "_mcp_capabilities",
        lambda config: {
            "mcp_servers": [],
            "mcp_tools": [],
            "server_tools": {},
            "mcp_capability_digest": "digest",
        },
    )
    monkeypatch.setattr(LAUNCHER, "_reject_conflicting_user_openai_base_url", lambda: None)
    monkeypatch.setattr(LAUNCHER, "_find_dcode", lambda: "dcode")
    invoked: list[object] = []
    invoked_kwargs: dict[str, object] = {}

    def complete_dcode(
        argv: list[str],
        environment: dict[str, str],
        repo_root: Path,
        handoff_stdin: str | None,
        timeout: float,
    ) -> int:
        invoked.append(argv)
        invoked_kwargs.update(
            environment=environment,
            cwd=repo_root,
            input=handoff_stdin,
            timeout=timeout,
        )
        return 0

    monkeypatch.setattr(LAUNCHER, "_run_deepagents_worker", complete_dcode)

    assert LAUNCHER.main(["--role", role_name, "--json", "--no-mcp", "-n", "task"]) == 0
    file_tool_root = "/" + tmp_path.relative_to(tmp_path.anchor).as_posix()
    assert invoked[0] == [
        "dcode",
        "-M",
        f"openai:{model}",
        "--model-params",
        '{"use_responses_api":false}',
        "--allow-fs-tools",
        "all",
        "--shell-allow-list",
        "git,py",
        "--json",
        "-n",
        (
            "task Host repository root: "
            f"`{tmp_path}`. Native filesystem tool root: "
            f"`{file_tool_root}`. Use host root for Git and shell commands; use tool root "
            "for filesystem tool paths. These roots refer to the same checkout. do not use "
            "`/workspace/...` or Windows drive syntax. "
            "Read only named source, test, "
            "and text files with filesystem tools. Never use filesystem tools on "
            "database, binary, archive, or runtime artifacts; examples: `*.sqlite`, "
            "`*.sqlite3`, `*.db`, `*-wal`, `*-shm`, `*-journal`, `*.zip`, `*.tar`, "
            "`*.gz`, `*.7z`, `*.bin`, `*.exe`, images, or media. For SQLite evidence, "
            "use launcher-authorized `py` from repository root with stdlib `sqlite3` "
            "read-only URI mode: `sqlite3.connect(\"file:<repo-relative-path>?mode=ro\", "
            "uri=True)`. Run `py` directly; do not prefix it with `cd`, shell operators, "
            "or wrappers. For `py -c`, use one expression; never use `;`."
        ),
        "--no-mcp",
    ]
    assert invoked_kwargs["cwd"] == tmp_path
    assert invoked_kwargs["timeout"] is None
    assert not (tmp_path / ".deepagents").exists()


def test_print_config_reports_selected_role_effective_model(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write_role(tmp_path, "normal", model="combo-normal", rank=20)
    secret_file = tmp_path / "secret.env"
    secret_file.write_text("API_KEY=secret\n", encoding="utf-8")
    config_path = tmp_path / "dcode-project.toml"
    config_path.write_text(
        '[delegation]\ndefault_executor = "deepagents"\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(LAUNCHER, "_config_path", lambda: config_path)
    monkeypatch.setattr(LAUNCHER, "_repo_root", lambda: tmp_path)
    monkeypatch.setattr(
        LAUNCHER,
        "_runtime_binding",
        lambda config: runtime_binding(
            {"model_providers": {"9router": {"wire_api": "chat"}}},
            secret_file=secret_file,
        ),
    )
    monkeypatch.setattr(
        LAUNCHER,
        "_mcp_capabilities",
        lambda config: {
            "mcp_servers": [],
            "mcp_tools": [],
            "server_tools": {},
            "mcp_capability_digest": "digest",
        },
    )

    assert LAUNCHER.main(["--role", "normal", "--print-config"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["selected_role"] == "normal"
    assert payload["effective_model"] == "openai:combo-normal"
    assert payload["controller_model"] == "openai:combo-high"
    assert payload["deepagents_model_params"] == {"use_responses_api": False}


def test_print_config_without_role_omits_worker_binding(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write_role(tmp_path, "normal")
    config_path = tmp_path / "dcode-project.toml"
    config_path.write_text(
        '[delegation]\ndefault_executor = "deepagents"\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(LAUNCHER, "_config_path", lambda: config_path)
    monkeypatch.setattr(LAUNCHER, "_repo_root", lambda: tmp_path)
    monkeypatch.setattr(
        LAUNCHER,
        "_runtime_binding",
        lambda config: runtime_binding({"model_providers": {"9router": {"wire_api": "chat"}}}),
    )
    monkeypatch.setattr(
        LAUNCHER,
        "_mcp_capabilities",
        lambda config: {
            "mcp_servers": [],
            "mcp_tools": [],
            "server_tools": {},
            "mcp_capability_digest": "digest",
        },
    )

    assert LAUNCHER.main(["--print-config"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert "selected_role" not in payload
    assert "effective_model" not in payload
    assert "runtime_binding_digest" not in payload


@pytest.mark.parametrize("executor", ["deepagents", "tura"])
def test_runtime_binding_loads_codex_config_once_per_invocation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    executor: str,
) -> None:
    write_role(tmp_path, "normal")
    secret_file = tmp_path / "secret.env"
    secret_file.write_text("API_KEY=secret\n", encoding="utf-8")
    codex_path = tmp_path / "codex.toml"
    codex_path.write_text(
        'model_provider = "9router"\nmodel = "combo-high"\n'
        '[model_providers."9router"]\n'
        'base_url = "https://provider.example/v1"\nwire_api = "chat"\n',
        encoding="utf-8",
    )
    executable = tmp_path / "tura.exe"
    executable.write_bytes(b"tura")
    provider_config = tmp_path / "providers.toml"
    provider_config.write_text("provider = 'test'\n", encoding="utf-8")
    config_path = tmp_path / "dcode-project.toml"
    config_path.write_text(
        f"[delegation]\ndefault_executor = '{executor}'\n[paths]\n"
        f"codex_config = '{codex_path}'\nsecret_file = '{secret_file}'\n"
        f"secret_key = 'API_KEY'\ntura_executable = '{executable}'\n"
        f"tura_provider_config = '{provider_config}'\n",
        encoding="utf-8",
    )
    original_load = LAUNCHER._load_toml
    loads: list[Path] = []

    def counted_load(path: Path, label: str) -> dict[str, object]:
        if path == codex_path:
            loads.append(path)
        return original_load(path, label)

    monkeypatch.setattr(LAUNCHER, "_load_toml", counted_load)
    monkeypatch.setattr(LAUNCHER, "_config_path", lambda: config_path)
    monkeypatch.setattr(LAUNCHER, "_repo_root", lambda: tmp_path)
    monkeypatch.setattr(
        LAUNCHER,
        "_mcp_capabilities",
        lambda config: {
            "mcp_servers": [],
            "mcp_tools": [],
            "server_tools": {},
            "mcp_capability_digest": "digest",
        },
    )
    if executor == "deepagents":
        monkeypatch.setattr(LAUNCHER, "_reject_conflicting_user_openai_base_url", lambda: None)
        monkeypatch.setattr(LAUNCHER, "_find_dcode", lambda: "dcode")
        monkeypatch.setattr(LAUNCHER, "_run_deepagents_worker", lambda *args: 0)
    else:
        monkeypatch.setattr(LAUNCHER, "_run_tura_worker", lambda *args: 0)

    assert LAUNCHER.main(["--role", "normal", "-n", "task"]) == 0
    assert loads == [codex_path]


def test_print_config_reports_tura_executable_hash_without_credentials(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write_role(tmp_path, "normal")
    executable = tmp_path / "tura.exe"
    executable.write_bytes(b"tura-test-binary")
    provider_config = tmp_path / "providers.toml"
    provider_config.write_text('api_key = "do-not-print"\n', encoding="utf-8")
    config_path = tmp_path / "dcode-project.toml"
    config_path.write_text(
        "[delegation]\ndefault_executor = \"tura\"\n"
        f"\n[paths]\ntura_executable = '{executable}'\n"
        f"tura_provider_config = '{provider_config}'\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(LAUNCHER, "_config_path", lambda: config_path)
    monkeypatch.setattr(LAUNCHER, "_repo_root", lambda: tmp_path)
    monkeypatch.setattr(
        LAUNCHER,
        "_runtime_binding",
        lambda config: runtime_binding({}),
    )
    monkeypatch.setattr(
        LAUNCHER,
        "_mcp_capabilities",
        lambda config: {
            "mcp_servers": [],
            "mcp_tools": [],
            "server_tools": {},
            "mcp_capability_digest": "digest",
        },
    )

    assert LAUNCHER.main(["--role", "normal", "--print-config"]) == 0

    output = capsys.readouterr().out
    payload = json.loads(output)
    assert payload["tura_executable"] == str(executable)
    assert payload["tura_executable_sha256"] == hashlib.sha256(
        b"tura-test-binary"
    ).hexdigest()
    assert "do-not-print" not in output


def test_role_model_comes_from_canonical_template(tmp_path: Path) -> None:
    write_role(tmp_path, "normal", model="combo-low")

    roles = LAUNCHER._load_roles(tmp_path, "9router")

    assert roles[0]["model"] == "combo-low"
    assert roles[0]["model_provider"] == "9router"


def test_role_loader_rejects_mismatched_runtime_provider(tmp_path: Path) -> None:
    write_role(tmp_path, "normal", model_provider="other")

    with pytest.raises(RuntimeError, match="does not match runtime provider"):
        LAUNCHER._load_roles(tmp_path, "9router")


def test_deepagents_provider_binding_accepts_responses_wire_api() -> None:
    config = {
        "model_providers": {
            "9router": {
                "wire_api": "responses",
            }
        }
    }

    assert LAUNCHER._deepagents_model_params(config, "9router")


def test_deepagents_provider_binding_accepts_chat_wire_api() -> None:
    config = {
        "model_providers": {
            "9router": {
                "wire_api": "chat",
            }
        }
    }

    assert LAUNCHER._deepagents_model_params(config, "9router")


def test_deepagents_provider_binding_rejects_unknown_wire_api() -> None:
    config = {"model_providers": {"9router": {"wire_api": "legacy"}}}

    with pytest.raises(RuntimeError, match="use `chat` or `responses`"):
        LAUNCHER._deepagents_model_params(config, "9router")


def test_role_loader_rejects_duplicate_ranks(tmp_path: Path) -> None:
    write_role(tmp_path, "low", rank=10)
    write_role(tmp_path, "normal", rank=10)

    with pytest.raises(RuntimeError, match="ranks must be unique"):
        LAUNCHER._load_roles(tmp_path, "9router")


def test_canonical_role_hierarchy_is_source_owned() -> None:
    roles = {
        role["name"]: (
            role["model_provider"],
            role["model"],
            role["rank"],
        )
        for role in LAUNCHER._load_roles(ROOT, "9router")
    }

    source_names = {path.stem for path in (ROOT / "agents").glob("*.toml")}

    assert set(roles) == source_names
    assert roles["ui"] == ("9router", "combo-ui", None)


def test_runtime_environment_reaches_deepagents_server_child(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

    environment = LAUNCHER._runtime_environment("http://127.0.0.1:20128/v1", "test-key")

    assert environment["DEEPAGENTS_CODE_OPENAI_BASE_URL"] == "http://127.0.0.1:20128/v1"
    assert environment["DEEPAGENTS_CODE_OPENAI_API_KEY"] == "test-key"
    assert environment["DEEPAGENTS_CODE_AUTO_UPDATE"] == "0"
    if os.name == "nt":
        assert environment["DEEPAGENTS_CODE_UI_CHARSET_MODE"] == "ascii"
        assert environment["LOG_COLOR"] == "false"
    assert environment["OPENAI_BASE_URL"] == "http://127.0.0.1:20128/v1"
    assert environment["PYTHONUTF8"] == "1"
    assert environment["PYTHONIOENCODING"] == "utf-8"


def test_runtime_environment_makes_child_subprocess_decoding_utf8() -> None:
    environment = LAUNCHER._runtime_environment("http://127.0.0.1:20128/v1", "test-key")
    probe = (
        "import subprocess, sys; "
        "result = subprocess.run([sys.executable, '-c', \"print('\\u2190')\"], "
        "capture_output=True, text=True, check=True); "
        "print(subprocess._text_encoding()); "
        "print(result.stdout, end='')"
    )

    completed = subprocess.run(
        [sys.executable, "-c", probe],
        env=environment,
        capture_output=True,
        check=True,
    )

    assert completed.stdout.decode("utf-8").replace("\r\n", "\n") == "utf-8\n←\n"
    assert environment["OPENAI_API_KEY"] == "test-key"

def test_runtime_environment_overrides_inherited_project_bindings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_BASE_URL", "https://project-env.example/v1")
    monkeypatch.setenv("OPENAI_API_KEY", "project-env-key")

    environment = LAUNCHER._runtime_environment("http://127.0.0.1:20128/v1", "test-key")

    assert environment["OPENAI_BASE_URL"] == "http://127.0.0.1:20128/v1"
    assert environment["OPENAI_API_KEY"] == "test-key"
    assert environment["DEEPAGENTS_CODE_OPENAI_BASE_URL"] == "http://127.0.0.1:20128/v1"
    assert environment["DEEPAGENTS_CODE_OPENAI_API_KEY"] == "test-key"


def test_conflicting_user_config_uses_deepagents_home(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    home = tmp_path / "deepagents-home"
    home.mkdir()
    (home / "config.toml").write_text(
        '[models.providers.openai]\nbase_url = "https://user.example/v1"\n',
        encoding="utf-8",
    )
    monkeypatch.setenv("DEEPAGENTS_HOME", str(home))

    with pytest.raises(RuntimeError, match="Remove conflicting OpenAI base_url"):
        LAUNCHER._reject_conflicting_user_openai_base_url()


def mcp_config() -> dict[str, object]:
    return {
        "mcp_servers": {
            "context7": {"tools": {"resolve_library_id": {}, "query_docs": {}}},
            "serena": {"tools": {"find_symbol": {}}},
        }
    }

def handoff_payload(capabilities: dict[str, object]) -> dict[str, object]:
    return {
        "schema": "codex.mcp.handoff.v1",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "mcp_capability_digest": capabilities["mcp_capability_digest"],
        "sources": [{"server": "context7", "tool": "query_docs"}],
        "facts": [{"source": 0, "value": "DeepAgents supports task-based subagent delegation."}],
        "constraints": ["Do not call MCP tools."],
    }

def test_mcp_capability_projection_omits_runtime_values() -> None:
    capabilities = LAUNCHER._mcp_capabilities(mcp_config())

    assert capabilities["mcp_servers"] == ["context7", "serena"]
    assert capabilities["mcp_tools"] == [
        "context7.query_docs",
        "context7.resolve_library_id",
        "serena.find_symbol",
    ]
    assert "https://" not in json.dumps(capabilities)

def test_mcp_selection_narrows_and_rejects_unknown() -> None:
    capabilities = LAUNCHER._mcp_capabilities(mcp_config())

    assert LAUNCHER._parse_mcp_selection(["context7.query_docs"], capabilities) == [
        "context7.query_docs"
    ]
    with pytest.raises(RuntimeError, match="Unknown MCP tool"):
        LAUNCHER._parse_mcp_selection(["context7.missing"], capabilities)
    with pytest.raises(RuntimeError, match="empty selector"):
        LAUNCHER._parse_mcp_selection(["context7.query_docs,"], capabilities)
    with pytest.raises(RuntimeError, match="Malformed MCP tool"):
        LAUNCHER._parse_mcp_selection(["context7.query_docs.extra"], capabilities)


def test_native_mcp_config_projects_only_selected_servers_and_tools() -> None:
    config = {
        "mcp_servers": {
            "context7": {
                "url": "https://mcp.context7.com/mcp",
                "default_tools_approval_mode": "writes",
                "headers": {"Authorization": "${MCP_AUTH}"},
                "env": {
                    "TOKEN": "${MCP_TOKEN}",
                    "MEMORY_FILE_PATH": "${MEMORY_FILE_PATH}",
                    "SystemRoot": r"C:\Windows",
                },
                "startup_timeout_sec": 30,
                "tools": {"query_docs": {}, "resolve_library_id": {}},
            },
            "serena": {"url": "https://serena.example/mcp", "tools": {"find_symbol": {}}},
        }
    }

    projected = LAUNCHER._native_mcp_config(config, ["context7.query_docs"])

    assert projected == {
        "mcpServers": {
            "context7": {
                "url": "https://mcp.context7.com/mcp",
                "headers": {"Authorization": "${MCP_AUTH}"},
                "env": {
                    "TOKEN": "${MCP_TOKEN}",
                    "MEMORY_FILE_PATH": "${MEMORY_FILE_PATH}",
                    "SystemRoot": r"C:\Windows",
                },
                "startup_timeout_sec": 30,
                    "allowedTools": ["query-docs", "query_docs"],
            }
        }
    }


@pytest.mark.parametrize(
    "field, value",
    [
        ("headers", {"Authorization": "Bearer secret"}),
        ("env", {"TOKEN": "secret"}),
    ],
)
def test_native_mcp_config_rejects_raw_sensitive_values(
    field: str,
    value: dict[str, str],
) -> None:
    config = {
        "mcp_servers": {
            "context7": {
                "url": "https://mcp.context7.com/mcp",
                field: value,
                "tools": {"query_docs": {}},
            }
        }
    }

    with pytest.raises(RuntimeError, match="environment references|sensitive"):
        LAUNCHER._native_mcp_config(config, ["context7.query_docs"])


def test_native_mcp_config_accepts_safe_environment_references() -> None:
    config = {
        "mcp_servers": {
            "context7": {
                "url": "https://mcp.context7.com/mcp/${MCP_PATH}",
                "headers": {"Authorization": "${MCP_AUTH}"},
                "env": {
                    "TOKEN": "${MCP_TOKEN}",
                    "MEMORY_FILE_PATH": "${MEMORY_FILE_PATH}",
                },
                "args": ["--profile", "${MCP_PROFILE}"],
                "startup_timeout_sec": 30,
                "tools": {"query_docs": {}},
            }
        }
    }

    projected = LAUNCHER._native_mcp_config(config, ["context7.query_docs"])

    assert projected["mcpServers"]["context7"]["headers"] == {
        "Authorization": "${MCP_AUTH}"
    }
    assert projected["mcpServers"]["context7"]["env"] == {
        "TOKEN": "${MCP_TOKEN}",
        "MEMORY_FILE_PATH": "${MEMORY_FILE_PATH}",
    }
    assert projected["mcpServers"]["context7"]["startup_timeout_sec"] == 30
    assert "secret" not in json.dumps(projected)


def test_native_mcp_config_rejects_sensitive_environment_values() -> None:
    config = {
        "mcp_servers": {
            "context7": {
                "env": {"MCP_TOKEN": "secret"},
                "tools": {"query_docs": {}},
            }
        }
    }

    with pytest.raises(RuntimeError, match="sensitive"):
        LAUNCHER._native_mcp_config(config, ["context7.query_docs"])


@pytest.mark.parametrize("value", [-1, True, 1.5, "30"])
def test_native_mcp_config_rejects_invalid_startup_timeout(value: object) -> None:
    config = {
        "mcp_servers": {
            "context7": {
                "startup_timeout_sec": value,
                "tools": {"query_docs": {}},
            }
        }
    }

    with pytest.raises(RuntimeError, match="nonnegative integer"):
        LAUNCHER._native_mcp_config(config, ["context7.query_docs"])


def test_native_mcp_config_normalizes_integral_float_startup_timeout() -> None:
    config = {
        "mcp_servers": {
            "serena": {
                "startup_timeout_sec": 120.0,
            }
        }
    }

    projected = LAUNCHER._native_mcp_config(config, ["serena"])

    assert projected["mcpServers"]["serena"]["startup_timeout_sec"] == 120


def _prepare_deepagents_main(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> dict[str, object]:
    write_role(tmp_path, "normal")
    secret_file = tmp_path / "secret.env"
    secret_file.write_text("API_KEY=secret\n", encoding="utf-8")
    config_path = tmp_path / "dcode-project.toml"
    config_path.write_text(
        '[delegation]\ndefault_executor = "deepagents"\n',
        encoding="utf-8",
    )
    codex_config = {
        "model_providers": {"9router": {"wire_api": "chat"}},
        "mcp_servers": {
            "context7": {
                "url": "https://mcp.context7.com/mcp",
                "headers": {"Authorization": "${MCP_AUTH}"},
                "env": {"TOKEN": "${MCP_TOKEN}"},
                "tools": {"query_docs": {}, "resolve_library_id": {}},
            },
            "serena": {
                "url": "https://serena.example/mcp",
                "tools": {"find_symbol": {}},
            },
        }
    }
    monkeypatch.setattr(LAUNCHER, "_config_path", lambda: config_path)
    monkeypatch.setattr(LAUNCHER, "_repo_root", lambda: tmp_path)
    monkeypatch.setattr(
        LAUNCHER,
        "_runtime_binding",
        lambda config: runtime_binding(codex_config, secret_file=secret_file),
    )
    monkeypatch.setattr(LAUNCHER, "_reject_conflicting_user_openai_base_url", lambda: None)
    monkeypatch.setattr(LAUNCHER, "_find_dcode", lambda: "dcode")
    return codex_config


def test_direct_mcp_isolates_user_discovery_and_cleans_config(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _prepare_deepagents_main(monkeypatch, tmp_path)
    user_home = tmp_path / "user-home"
    user_home.mkdir()
    (user_home / ".mcp.json").write_text('{"mcpServers":{"user":{}}}', encoding="utf-8")
    monkeypatch.setenv("DEEPAGENTS_HOME", str(user_home))
    monkeypatch.setenv("DEEPAGENTS_CODE_DANGEROUSLY_ENABLE_PROJECT_MCP_SERVERS", "unrelated")
    captured: dict[str, object] = {}

    def run_worker(argv, environment, repo_root, handoff_stdin, timeout):
        captured.update(argv=list(argv), environment=dict(environment), input=handoff_stdin)
        config_path = Path(argv[argv.index("--mcp-config") + 1])
        captured["config_exists_during_run"] = config_path.is_file()
        captured["config"] = json.loads(config_path.read_text(encoding="utf-8"))
        return 0

    monkeypatch.setattr(LAUNCHER, "_run_deepagents_worker", run_worker)

    assert LAUNCHER.main(["--role", "normal", "--mcp-select", "context7.query_docs", "-n", "task"]) == 0

    argv = captured["argv"]
    assert isinstance(argv, list)
    assert "--no-mcp" not in argv
    assert "secret" not in " ".join(argv)
    assert captured["input"] is None
    assert captured["config_exists_during_run"] is True
    assert captured["config"] == {
        "mcpServers": {
            "context7": {
                "url": "https://mcp.context7.com/mcp",
                "headers": {"Authorization": "${MCP_AUTH}"},
                "env": {"TOKEN": "${MCP_TOKEN}"},
                "allowedTools": ["query-docs", "query_docs"],
            }
        }
    }
    output = capsys.readouterr()
    assert "secret" not in output.out
    assert "secret" not in output.err
    assert not Path(str(argv[argv.index("--mcp-config") + 1])).exists()
    assert captured["environment"]["DEEPAGENTS_HOME"] != str(user_home)
    assert "DEEPAGENTS_CODE_DANGEROUSLY_ENABLE_PROJECT_MCP_SERVERS" not in captured["environment"]


def test_direct_mcp_proceeds_without_mutating_project_configs(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _prepare_deepagents_main(monkeypatch, tmp_path)
    root_config = tmp_path / ".mcp.json"
    nested_config = tmp_path / ".deepagents" / ".mcp.json"
    root_content = '{"mcpServers":{"unrelated":{}}}'
    nested_content = '{"mcpServers":{"nested":{}}}'
    root_config.write_text(root_content, encoding="utf-8")
    nested_config.parent.mkdir()
    nested_config.write_text(nested_content, encoding="utf-8")
    captured: dict[str, object] = {}

    def run_worker(argv, environment, repo_root, handoff_stdin, timeout):
        captured["argv"] = list(argv)
        captured["environment"] = dict(environment)
        return 0

    monkeypatch.setattr(LAUNCHER, "_run_deepagents_worker", run_worker)

    assert LAUNCHER.main(["--role", "normal", "--mcp-select", "context7", "-n", "task"]) == 0

    assert root_config.read_text(encoding="utf-8") == root_content
    assert nested_config.read_text(encoding="utf-8") == nested_content
    assert "--mcp-config" in captured["argv"]
    assert "DEEPAGENTS_CODE_DANGEROUSLY_ENABLE_PROJECT_MCP_SERVERS" not in captured["environment"]
    assert not (tmp_path / ".deepagents" / "agents").exists()


def test_direct_mcp_janitor_removes_only_owned_stale_runtime(tmp_path: Path) -> None:
    parent = tmp_path / "dcode-project-mcp"
    parent.mkdir()
    marker = parent / LAUNCHER._DIRECT_MCP_OWNER_MARKER
    marker.write_text(LAUNCHER._DIRECT_MCP_OWNER_VALUE, encoding="utf-8")

    stale = parent / "runtime-stale"
    stale.mkdir()
    (stale / LAUNCHER._DIRECT_MCP_OWNER_MARKER).write_text(
        LAUNCHER._DIRECT_MCP_OWNER_VALUE,
        encoding="utf-8",
    )
    os.utime(stale, (0, 0))

    foreign = parent / "runtime-foreign"
    foreign.mkdir()
    (foreign / LAUNCHER._DIRECT_MCP_OWNER_MARKER).write_text("other\n", encoding="utf-8")

    fresh = parent / "runtime-fresh"
    fresh.mkdir()
    (fresh / LAUNCHER._DIRECT_MCP_OWNER_MARKER).write_text(
        LAUNCHER._DIRECT_MCP_OWNER_VALUE,
        encoding="utf-8",
    )

    LAUNCHER._cleanup_stale_direct_mcp_runtimes(parent)

    assert not stale.exists()
    assert foreign.exists()
    assert fresh.exists()


def test_direct_mcp_cleans_config_after_worker_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _prepare_deepagents_main(monkeypatch, tmp_path)
    captured: dict[str, object] = {}

    def fail_worker(argv, environment, repo_root, handoff_stdin, timeout):
        captured["config_path"] = argv[argv.index("--mcp-config") + 1]
        assert "secret" not in " ".join(argv)
        config_text = Path(str(captured["config_path"])).read_text(encoding="utf-8")
        assert "secret" not in config_text
        assert "${MCP_AUTH}" in config_text
        raise OSError("worker failed")

    monkeypatch.setattr(LAUNCHER, "_run_deepagents_worker", fail_worker)

    with pytest.raises(OSError, match="worker failed"):
        LAUNCHER.main(["--role", "normal", "--mcp-select", "context7", "-n", "task"])

    assert not Path(str(captured["config_path"])).exists()


def test_default_deepagents_path_keeps_mcp_disabled(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _prepare_deepagents_main(monkeypatch, tmp_path)
    captured: dict[str, object] = {}

    def run_worker(argv, environment, repo_root, handoff_stdin, timeout):
        captured["argv"] = argv
        return 0

    monkeypatch.setattr(LAUNCHER, "_run_deepagents_worker", run_worker)

    assert LAUNCHER.main(["--role", "normal", "-n", "task"]) == 0

    argv = captured["argv"]
    assert argv[-1] == "--no-mcp"
    assert "--mcp-config" not in argv

def test_handoff_validation_accepts_current_selected_facts(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(LAUNCHER, "_handoff_root", lambda: tmp_path)
    capabilities = LAUNCHER._mcp_capabilities(mcp_config())
    path = tmp_path / "handoff.json"
    path.write_text(json.dumps(handoff_payload(capabilities)), encoding="utf-8")

    resolved, payload = LAUNCHER._validate_handoff(
        str(path), capabilities, ["context7.query_docs"]
    )

    assert resolved == path
    assert payload["schema"] == "codex.mcp.handoff.v1"

@pytest.mark.parametrize(
    "mutator, message",
    [
        (lambda payload: payload["facts"][0]["value"] == "Bearer secret", "sensitive"),
        (lambda payload: payload.update({"schema": "bad"}), "Unsupported handoff schema"),
        (lambda payload: payload.update({"mcp_capability_digest": "bad"}), "digest"),
    ],
)
def test_handoff_validation_rejects_unsafe_or_mismatched_payload(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    mutator: object,
    message: str,
) -> None:
    monkeypatch.setattr(LAUNCHER, "_handoff_root", lambda: tmp_path)
    capabilities = LAUNCHER._mcp_capabilities(mcp_config())
    payload = handoff_payload(capabilities)
    if message == "sensitive":
        payload["facts"][0]["value"] = "Bearer secret"
    else:
        mutator(payload)
    path = tmp_path / "handoff.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(RuntimeError, match=message):
        LAUNCHER._validate_handoff(str(path), capabilities, ["context7.query_docs"])

def test_handoff_validation_rejects_symlink(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(LAUNCHER, "_handoff_root", lambda: tmp_path)
    capabilities = LAUNCHER._mcp_capabilities(mcp_config())
    source = tmp_path / "source.json"
    source.write_text(json.dumps(handoff_payload(capabilities)), encoding="utf-8")
    link = tmp_path / "handoff.json"
    try:
        link.symlink_to(source)
    except OSError:
        pytest.skip("Symlink creation unavailable")

    with pytest.raises(RuntimeError, match="symlink"):
        LAUNCHER._validate_handoff(str(link), capabilities, ["context7.query_docs"])

def test_handoff_instruction_moves_validated_payload_to_stdin() -> None:
    argv = ["-n", "caller task", "--no-mcp"]
    payload = {
        "schema": "codex.mcp.handoff.v1",
        "sources": [{"server": "context7", "tool": "resolve_library_id"}],
        "facts": [{"source": 0, "value": {"official_library_id": "/python/cpython"}}],
        "constraints": ["Do not call MCP tools."],
    }

    task = LAUNCHER._handoff_stdin(argv, payload)

    assert argv == ["--stdin", "--no-mcp"]
    assert task.startswith("caller task")
    assert "Use this validated Codex MCP handoff payload" in task
    assert '"official_library_id":"/python/cpython"' in task
    assert "handoff.json" not in task


def test_handoff_instruction_canonicalizes_provenance_order() -> None:
    payload_a = {
        "schema": "codex.mcp.handoff.v1",
        "sources": [
            {"server": "serena", "tool": "find_symbol"},
            {"server": "context7", "tool": "query_docs"},
        ],
        "facts": [
            {"source": 0, "value": "symbol fact"},
            {"source": 1, "value": {"library": "docs"}},
        ],
        "constraints": ["first constraint", "second constraint"],
    }
    payload_b = {
        **payload_a,
        "sources": [payload_a["sources"][1], payload_a["sources"][0]],
        "facts": [
            {"source": 0, "value": {"library": "docs"}},
            {"source": 1, "value": "symbol fact"},
        ],
    }

    task_a = LAUNCHER._handoff_stdin(["-n", "caller task"], payload_a)
    task_b = LAUNCHER._handoff_stdin(["-n", "caller task"], payload_b)

    assert task_a == task_b
    assert '"constraints":["first constraint","second constraint"]' in task_a

def test_handoff_stdin_preserves_binary_file_safety_context(tmp_path: Path) -> None:
    argv = ["-n", "caller task", "--no-mcp"]
    payload = {
        "schema": "codex.mcp.handoff.v1",
        "sources": [],
        "facts": [],
        "constraints": [],
    }

    LAUNCHER._append_bounded_task_context(argv, tmp_path)
    task = LAUNCHER._handoff_stdin(argv, payload)

    assert "Never use filesystem tools on database, binary, archive, or runtime artifacts" in task
    assert '`sqlite3.connect("file:<repo-relative-path>?mode=ro", uri=True)`' in task
    assert "Run `py` directly; do not prefix it with `cd`, shell operators, or wrappers" in task
    assert "For `py -c`, use one expression; never use `;`" in task


def test_bounded_task_context_exposes_host_and_tool_roots(tmp_path: Path) -> None:
    context = LAUNCHER._bounded_task_context(tmp_path)

    assert f"Host repository root: `{tmp_path.resolve()}`" in context
    assert "Native filesystem tool root:" in context


def test_setup_launcher_uses_current_repository_source() -> None:
    setup = runtime_script("setup_deepagents_runtime.ps1").read_text(encoding="utf-8")

    assert "Copy-Item" not in setup
    assert "git rev-parse --show-toplevel" in setup
    assert 'Join-Path $repoRoot "scripts\\dcode_project.py"' in setup
    assert 'Join-Path $HOME ".agents\\project-os\\scripts\\dcode_project.py"' in setup
    assert setup.index('$launcher = Join-Path $repoRoot "scripts\\dcode_project.py"') < setup.index('$launcher = Join-Path $HOME ".agents\\project-os\\scripts\\dcode_project.py"')
    assert 'dcode-project.ps1' in setup
    assert 'project-delegate.ps1' in setup
    assert 'TuraExecutable' in setup
    assert 'TuraProviderConfig' in setup
    assert 'default_executor' in setup
    assert '--sandbox' in setup
    assert 'Tura capability probe failed' in setup
    assert 'selects DeepAgents; do not pass --executor' in setup
    assert 'project-delegate selects Tura; do not pass --executor' in setup
    assert '& py -3 $launcher --executor tura @DelegateArgs' in setup
    assert 'Tura migration:' in setup
    assert "DEEPAGENTS_HOME" in setup
    assert "GetUnresolvedProviderPathFromPSPath" in setup
    assert "Direct DeepAgents MCP config detected" in setup
    assert '$DeepAgentsCodeVersion = "0.1.66"' in setup
    assert 'deepagents-code==$DeepAgentsCodeVersion' in setup
    assert 'langgraph-api==0.13.0' in setup
    assert 'langgraph-runtime-inmem==0.33.3' in setup
    assert 'uvicorn==0.51.0' in setup
    assert '$env:UV_TOOL_DIR = $deepAgentsToolRoot' in setup
    assert '$env:UV_TOOL_BIN_DIR = $deepAgentsBinRoot' in setup
    assert 'dcode-doctor.ps1' in setup
    assert 'DEEPAGENTS_CODE_UI_CHARSET_MODE = "ascii"' in setup
    assert '$env:PYTHONUTF8 = "1"' in setup
    assert '$env:PYTHONIOENCODING = "utf-8"' in setup
    assert setup.index('$env:PYTHONUTF8 = "1"') < setup.index('& $dcodePath doctor')
    assert setup.index('$env:PYTHONIOENCODING = "utf-8"') < setup.index('& $dcodePath doctor')
    assert "Python 3.12 or newer" in setup
    assert "version mismatch" in setup
    assert "patch_deepagents_runtime.py" in setup
    assert "mcp_tools.py" in setup


def test_generated_project_delegate_guard_returns_contract_exit_code(tmp_path: Path) -> None:
    powershell = shutil.which("pwsh") or shutil.which("powershell")
    if powershell is None:
        pytest.skip("PowerShell is required to execute generated wrapper")

    setup = runtime_script("setup_deepagents_runtime.ps1").read_text(encoding="utf-8")
    setup = setup.replace("\r\n", "\n")
    start_marker = "$delegateWrapper = @'\n"
    end_marker = "\n'@\n"
    start = setup.index(start_marker) + len(start_marker)
    end = setup.index(end_marker, start)
    wrapper_path = tmp_path / "project-delegate.ps1"
    wrapper_path.write_text(setup[start:end] + "\n", encoding="utf-8")

    result = subprocess.run(
        [
            powershell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(wrapper_path),
            "--executor",
            "deepagents",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert "project-delegate selects Tura; do not pass --executor" in result.stderr


@pytest.mark.parametrize(
    ("wrapper_name", "executor"),
    [("dcode-project", "deepagents"), ("project-delegate", "tura")],
)
def test_generated_wrappers_prefer_local_launcher_and_fallback_to_shared(
    tmp_path: Path,
    wrapper_name: str,
    executor: str,
) -> None:
    powershell = shutil.which("pwsh") or shutil.which("powershell")
    py_launcher = shutil.which("py")
    if powershell is None or py_launcher is None:
        pytest.skip("PowerShell and the py launcher are required")

    repo = tmp_path / "consumer repo with spaces"
    (repo / "scripts").mkdir(parents=True)
    subprocess.run(["git", "init", "--quiet", str(repo)], check=True)
    fake_home = tmp_path / "home with spaces"
    shared = fake_home / ".agents" / "project-os" / "scripts"
    shared.mkdir(parents=True)
    setup = runtime_script("setup_deepagents_runtime.ps1").read_text(encoding="utf-8").replace("\r\n", "\n")
    variable = "$wrapper" if wrapper_name == "dcode-project" else "$delegateWrapper"
    start = setup.index(f"{variable} = @'\n") + len(f"{variable} = @'\n")
    end = setup.index("\n'@\n", start)
    wrapper_path = tmp_path / f"{wrapper_name}.ps1"
    wrapper_path.write_text(setup[start:end] + "\n", encoding="utf-8")

    (repo / "scripts" / "dcode_project.py").write_text(
        "import sys; print(' '.join(sys.argv[1:])); raise SystemExit(7)\n",
        encoding="utf-8",
    )
    (shared / "dcode_project.py").write_text(
        "import sys; print('shared:' + ' '.join(sys.argv[1:])); raise SystemExit(8)\n",
        encoding="utf-8",
    )
    environment = os.environ.copy()
    environment.update({"HOME": str(fake_home), "USERPROFILE": str(fake_home)})

    def run_wrapper() -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(wrapper_path), "probe"],
            cwd=repo,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

    local_result = run_wrapper()
    assert local_result.returncode == 7
    assert f"--executor {executor} probe" in local_result.stdout

    (repo / "scripts" / "dcode_project.py").unlink()
    shared_result = run_wrapper()
    assert shared_result.returncode == 8
    assert f"shared:--executor {executor} probe" in shared_result.stdout
