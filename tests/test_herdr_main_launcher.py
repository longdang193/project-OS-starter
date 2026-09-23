from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import subprocess

import pytest

from project_os_test_paths import add_runtime_import_roots, runtime_script

add_runtime_import_roots()
ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "herdr_main_launcher", runtime_script("herdr_main_launcher.py")
)
assert SPEC is not None and SPEC.loader is not None
LAUNCHER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(LAUNCHER)
_MANAGED_DEEPAGENTS_RESOLVER = LAUNCHER._managed_deepagents_executable


def fake_profile(tmp_path: Path, name: str, rank: int | None) -> None:
    agents = tmp_path / "agents"
    agents.mkdir(exist_ok=True)
    rank_line = "" if rank is None else f"rank = {rank}\n"
    (agents / f"{name}.toml").write_text(
        f'name = "{name}"\n'
        'model_provider = "9router"\n'
        f'model = "combo-{name}"\n'
        f"{rank_line}"
        'description = "test"\n'
        'developer_instructions = "do not modify files"\n',
        encoding="utf-8",
    )


def _confirmed_success_receipt() -> dict[str, object]:
    return {
        "state": "confirmed",
        "worker_state": "exited",
        "worker_exit_code": 0,
        "descendant_state": "terminated",
        "cleanup_state": "removed",
        "role_views_state": "removed",
        "recovery_required": False,
    }


def _confirmed_task_result(status: str = "completed") -> dict[str, object]:
    return {"state": "confirmed", "status": status}


def test_deepagents_classification_ignores_pane_failure_after_structured_success() -> None:
    result = LAUNCHER._classify_deepagents_outcome(
        delivery={"state": "delivered"},
        observation={
            "state": "failed",
            "report_present": True,
            "observation_error": None,
        },
        receipt=_confirmed_success_receipt(),
        fallback_failure_kind=None,
        task_result_evidence={
            "state": "confirmed",
            "status": "completed",
        },
    )

    assert result["status"] == "completed"
    assert result["failure_kind"] is None
    assert result["task_result"]["state"] == "reported_completed"
    assert result["launcher_exit_code"] == 0


def test_deepagents_classification_keeps_structured_failure_authoritative() -> None:
    result = LAUNCHER._classify_deepagents_outcome(
        delivery={"state": "delivered"},
        observation={
            "state": "completed",
            "report_present": True,
            "observation_error": None,
        },
        receipt=_confirmed_success_receipt(),
        fallback_failure_kind=None,
        task_result_evidence={
            "state": "confirmed",
            "status": "failed",
        },
    )

    assert result["status"] == "failed"
    assert result["failure_kind"] == "task_report_failed"
    assert result["task_result"]["state"] == "reported_failed"
    assert result["launcher_exit_code"] == 2


def test_deepagents_completion_observation_returns_confirmed_receipt_without_pane_read(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    receipt = _confirmed_success_receipt()
    monkeypatch.setattr(LAUNCHER, "_read_deepagents_receipt", lambda path, attempt: receipt)
    monkeypatch.setattr(
        LAUNCHER,
        "_deepagents_completion_snapshot",
        lambda *args, **kwargs: pytest.fail("confirmed receipt must not read pane"),
    )

    evidence = LAUNCHER._deepagents_completion_evidence(
        "herdr",
        "session",
        "pane",
        env={},
        expected_marker=None,
        receipt_file=tmp_path / "result.json",
        attempt_id="attempt",
        completion_wait_seconds=0,
    )

    assert evidence["lifecycle_receipt"] == receipt
    assert evidence["receipt_authoritative"] is True


def test_resolve_launch_rejects_explicit_over_limit_agent_name_before_start(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile = LAUNCHER.AgentProfile(
        Path("normal.toml"),
        "normal",
        "9router",
        "combo-normal",
        20,
        "test",
        "do not modify files",
    )
    monkeypatch.setattr(LAUNCHER, "_profile", lambda *args: profile)
    monkeypatch.setattr(LAUNCHER, "_executable", lambda name: f"{name}.exe")
    monkeypatch.setattr(LAUNCHER, "_version", lambda *args, **kwargs: "test")
    monkeypatch.setattr(LAUNCHER, "_git_identity", lambda *args: {"head": "head"})
    pane_calls: list[object] = []

    def fake_herdr_pane(*args: object, **kwargs: object) -> dict[str, object]:
        pane_calls.append((args, kwargs))
        return {"pane": {"cwd": str(ROOT)}, "process_info": {}}

    monkeypatch.setattr(
        LAUNCHER,
        "_herdr_pane",
        fake_herdr_pane,
    )

    with pytest.raises(LAUNCHER.LaunchBlocked, match="32"):
        LAUNCHER.resolve_launch(
            profile_name="normal",
            session="deepagents-probe",
            pane="w1:p1",
            cwd=ROOT,
            expected_base="HEAD",
            executor="deepagents",
            name="a" * 33,
            task="assign lane",
        )
    assert pane_calls == []


def test_unique_agent_names_are_bounded_and_unique(monkeypatch: pytest.MonkeyPatch) -> None:
    values = iter(("a" * 32, "b" * 32))
    monkeypatch.setattr(LAUNCHER.uuid, "uuid4", lambda: type("UUID", (), {"hex": next(values)})())

    first = LAUNCHER._unique_agent_name("normal-profile-name-that-exceeds-herdr-limit")
    second = LAUNCHER._unique_agent_name("normal-profile-name-that-exceeds-herdr-limit")

    assert len(first) <= 32
    assert len(second) <= 32
    assert first != second


def test_codex_arguments_project_complete_contract(tmp_path: Path) -> None:
    fake_profile(tmp_path, "review", None)
    profile = LAUNCHER._profile(tmp_path / "agents", "review")

    arguments = LAUNCHER._codex_arguments(profile, tmp_path)

    assert arguments[:2] == ["-C", str(tmp_path)]
    assert 'model_provider="9router"' in arguments
    assert 'model="combo-review"' in arguments
    assert 'developer_instructions="do not modify files"' in arguments
    assert "--dangerously-bypass-hook-trust" in arguments
    assert "check_for_update_on_startup=false" in arguments


def test_codex_arguments_disable_heavy_browser_mcps_for_workers(tmp_path: Path) -> None:
    fake_profile(tmp_path, "review", None)
    profile = LAUNCHER._profile(tmp_path / "agents", "review")

    arguments = LAUNCHER._codex_arguments(
        profile,
        tmp_path,
        mcp_server_names=("chrome-devtools", "playwright", "open-design"),
    )

    assert "mcp_servers.chrome-devtools.enabled=false" in arguments
    assert "mcp_servers.playwright.enabled=false" in arguments
    assert "mcp_servers.open-design.enabled=false" in arguments


def test_codex_arguments_disable_runtime_only_mcp_with_valid_transport(
    tmp_path: Path,
) -> None:
    fake_profile(tmp_path, "review", None)
    profile = LAUNCHER._profile(tmp_path / "agents", "review")

    arguments = LAUNCHER._codex_arguments(
        profile,
        tmp_path,
        mcp_server_names=("cua_repl",),
        runtime_only_mcp_servers=("cua_repl",),
    )

    assert 'mcp_servers.cua_repl.command="cmd"' in arguments
    assert "mcp_servers.cua_repl.args=[]" in arguments
    assert "mcp_servers.cua_repl.enabled=false" in arguments


def test_codex_arguments_preserve_selected_runtime_only_mcp_transport(
    tmp_path: Path,
) -> None:
    fake_profile(tmp_path, "review", None)
    profile = LAUNCHER._profile(tmp_path / "agents", "review")

    arguments = LAUNCHER._codex_arguments(
        profile,
        tmp_path,
        mcp_server_names=("cua_repl",),
        selected_mcp_servers=("cua_repl",),
        runtime_only_mcp_servers=("cua_repl",),
    )

    assert 'mcp_servers.cua_repl.command="cmd"' not in arguments
    assert "mcp_servers.cua_repl.args=[]" not in arguments
    assert arguments.count("mcp_servers.cua_repl.enabled=false") == 1
    assert arguments.count("mcp_servers.cua_repl.enabled=true") == 1


def test_codex_arguments_enable_only_selected_server(tmp_path: Path) -> None:
    fake_profile(tmp_path, "review", None)
    profile = LAUNCHER._profile(tmp_path / "agents", "review")

    arguments = LAUNCHER._codex_arguments(
        profile,
        tmp_path,
        mcp_server_names=("context7", "open-design"),
        selected_mcp_servers=("context7",),
    )

    assert "mcp_servers.context7.enabled=false" in arguments
    assert "mcp_servers.context7.enabled=true" in arguments
    assert "mcp_servers.open-design.enabled=false" in arguments


def test_codex_mcp_selection_reads_global_and_project_config(tmp_path: Path) -> None:
    codex_home = tmp_path / "codex-home"
    codex_home.mkdir()
    (codex_home / "config.toml").write_text(
        '[mcp_servers.global]\ncommand = "global"\n\n'
        '[mcp_servers.overridden]\ncommand = "global"\n',
        encoding="utf-8",
    )
    project_codex = tmp_path / ".codex"
    project_codex.mkdir()
    (project_codex / "config.toml").write_text(
        '[mcp_servers.project]\ncommand = "project"\n\n'
        '[mcp_servers.overridden]\ncommand = "project"\n',
        encoding="utf-8",
    )

    selection = LAUNCHER._codex_mcp_selection(tmp_path, codex_home, [])

    assert selection["effective_servers"] == ()
    assert selection["server_names"] == ("global", "overridden", "project")


def test_codex_mcp_selection_includes_runtime_servers(tmp_path: Path) -> None:
    codex_home = tmp_path / "codex-home"
    codex_home.mkdir()
    (codex_home / "config.toml").write_text(
        '[mcp_servers.context7]\ncommand = "context7"\n',
        encoding="utf-8",
    )

    selection = LAUNCHER._codex_mcp_selection(
        tmp_path,
        codex_home,
        [],
        runtime_servers={"cua_repl": True},
    )

    assert selection["server_names"] == ("context7", "cua_repl")
    assert selection["runtime_only_servers"] == ("cua_repl",)
    assert selection["effective_servers"] == ()


def test_codex_runtime_mcp_servers_reads_codex_listing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    result = subprocess.CompletedProcess(
        ["codex", "mcp", "list", "--json"],
        0,
        stdout=json.dumps([
            {"name": "cua_repl", "enabled": True},
            {"name": "disabled", "enabled": False},
        ]),
        stderr="",
    )
    monkeypatch.setattr(LAUNCHER, "_run", lambda *args, **kwargs: result)

    assert LAUNCHER._codex_runtime_mcp_servers("codex", tmp_path, env={}) == {
        "cua_repl": True,
        "disabled": False,
    }


def test_codex_mcp_selection_rejects_tool_selector(tmp_path: Path) -> None:
    codex_home = tmp_path / "codex-home"
    codex_home.mkdir()
    (codex_home / "config.toml").write_text(
        '[mcp_servers.context7]\ncommand = "context7"\n'
        'tools = { query_docs = {} }\n',
        encoding="utf-8",
    )

    with pytest.raises(LAUNCHER.LaunchBlocked, match="tool-level MCP selection"):
        LAUNCHER._codex_mcp_selection(tmp_path, codex_home, ["context7.query_docs"])


def test_failed_codex_start_reconciliation_blocks_uncertain_process(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_json_command(command, **kwargs):
        if command[-2:] == ["pane", "list"]:
            return {"result": {"panes": [{"pane_id": "w1:p1", "agent": None}]}}
        return {"result": {"process_info": {"foreground_processes": [{"pid": 42, "name": "codex.exe", "children": []}]}}}

    monkeypatch.setattr(LAUNCHER, "_json_command", fake_json_command)

    result = LAUNCHER._reconcile_failed_codex_start(
        "herdr.exe",
        "session",
        "w1:p1",
        "normal-main",
        env={},
    )

    assert result["state"] == "uncertain"
    assert result["cleanup"] is None


def test_failed_codex_start_reconciliation_requires_new_owned_process(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def fake_json_command(command, **kwargs):
        if command[-2:] == ["pane", "list"]:
            return {"result": {"panes": [{"pane_id": "w1:p1", "agent": "normal-main"}]}}
        return {"result": {"process_info": {"foreground_processes": [{
            "pid": 42,
            "name": "codex.exe",
            "argv0": "C:/bin/codex.exe",
            "cwd": str(tmp_path),
            "children": [],
        }]}}}

    monkeypatch.setattr(LAUNCHER, "_json_command", fake_json_command)
    monkeypatch.setattr(
        LAUNCHER,
        "_terminate_codex_lane",
        lambda *args, **kwargs: {"verified": True, "action": "pane-close"},
    )

    result = LAUNCHER._reconcile_failed_codex_start(
        "herdr.exe",
        "session",
        "w1:p1",
        "normal-main",
        env={},
        before_process_ids={41},
        expected_codex_executable="C:/bin/codex.exe",
        expected_cwd=tmp_path,
    )

    assert result["state"] == "retired"
    assert result["cleanup"]["verified"] is True


def test_failed_codex_start_reconciliation_rejects_preexisting_process(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        LAUNCHER,
        "_json_command",
        lambda command, **kwargs: (
            {"result": {"panes": [{"pane_id": "w1:p1", "agent": "normal-main"}]}}
            if command[-2:] == ["pane", "list"]
            else {"result": {"process_info": {"foreground_processes": [{"pid": 42, "name": "codex.exe", "children": []}]}}}
        ),
    )
    terminated: list[tuple[object, ...]] = []
    monkeypatch.setattr(
        LAUNCHER,
        "_terminate_codex_lane",
        lambda *args, **kwargs: terminated.append(args),
    )

    result = LAUNCHER._reconcile_failed_codex_start(
        "herdr.exe", "session", "w1:p1", "normal-main", env={},
        before_process_ids={42},
    )

    assert result["state"] == "uncertain"
    assert terminated == []


def test_redaction_hides_developer_instructions() -> None:
    arguments = ["-c", 'model="combo-xhigh"', "-c", 'developer_instructions="secret"']

    assert LAUNCHER._redacted_arguments(arguments) == [
        "-c",
        'model="combo-xhigh"',
        "-c",
        "developer_instructions=<sha256>",
    ]


def test_redaction_hides_deepagents_task() -> None:
    redacted = LAUNCHER._redacted_arguments(["-n", "private task"])

    assert redacted == [
        "-n",
        f"task=<sha256:{LAUNCHER._sha256_text('private task')}>",
    ]


def test_redaction_hides_codex_assignment_task() -> None:
    redacted = LAUNCHER._redacted_arguments(
        ["agent", "prompt", "xhigh-main", "private task", "--wait"],
    )

    assert redacted == [
        "agent",
        "prompt",
        "xhigh-main",
        f"task=<sha256:{LAUNCHER._sha256_text('private task')}>",
        "--wait",
    ]


def test_codex_assignment_command_prompts_started_agent() -> None:
    command = LAUNCHER._codex_assignment_command(
        "herdr.exe", "session", "xhigh-main", "assign lane",
    )

    assert command == [
        "herdr.exe",
        "--session",
        "session",
        "agent",
        "prompt",
        "xhigh-main",
        "assign lane",
    ]


def test_codex_completion_snapshot_reads_status_and_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[str]] = []

    def fake_run(command, **kwargs):
        calls.append(command)
        if command[3:5] == ["agent", "get"]:
            return subprocess.CompletedProcess(
                command,
                0,
                '{"result":{"agent":{"agent_status":"working","state_change_seq":7}}}',
                "",
            )
        return subprocess.CompletedProcess(command, 0, '{"result":"work output"}', "")

    monkeypatch.setattr(LAUNCHER, "_run", fake_run)

    snapshot = LAUNCHER._codex_completion_snapshot(
        "herdr.exe", "session", "xhigh-main", env={},
    )

    assert snapshot["state"] == "working"
    assert snapshot["state_change_seq"] == 7
    assert snapshot["output_chars"] == len("work output")
    assert snapshot["observation_error"] is None
    assert calls == [
        ["herdr.exe", "--session", "session", "agent", "get", "xhigh-main"],
        [
            "herdr.exe", "--session", "session", "agent", "read", "xhigh-main",
            "--source", "recent-unwrapped", "--lines", "200", "--format", "text",
        ],
    ]


def test_codex_observation_timeout_preserves_unknown_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def fake_run(command, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise LAUNCHER.CommandTransportTimeout("agent get timed out")
        return subprocess.CompletedProcess(command, 0, '{"result":"stale output"}', "")

    monkeypatch.setattr(LAUNCHER, "_run", fake_run)

    snapshot = LAUNCHER._codex_completion_snapshot(
        "herdr.exe", "session", "xhigh-main", env={}, timeout_seconds=0.01,
    )

    assert snapshot["state"] == "unknown"
    assert snapshot["observation_error"] == "agent get transport timeout"
    assert snapshot["output_chars"] == len("stale output")


def test_codex_dispatch_returns_before_completion_observation(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    evidence = {
        "registry_launcher": {
            "assignment_task_sha256": LAUNCHER._sha256_text("assign lane"),
            "runtime_grant": {"delegation": {"child_agents": "allow"}},
        },
        "codex": {"codex_home": str(Path.cwd())},
        "herdr": {
            "executable": "herdr.exe",
            "agent_name": "xhigh-main",
            "session": "session",
            "pane": "pane",
        },
    }
    calls: list[list[str]] = []
    monkeypatch.setattr(LAUNCHER, "resolve_launch", lambda **kwargs: (["herdr"], evidence))

    def fake_run(command, **kwargs):
        calls.append(command)
        if command[3:5] == ["agent", "get"]:
            return subprocess.CompletedProcess(
                command,
                0,
                '{"result":{"agent":{"agent_status":"working","state_change_seq":8}}}',
                "",
            )
        if command[3:5] == ["agent", "read"]:
            return subprocess.CompletedProcess(command, 0, '{"result":"still working"}', "")
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(LAUNCHER, "_run", fake_run)
    assert LAUNCHER.main([
        "--profile", "xhigh", "--session", "session", "--pane", "pane",
        "--cwd", str(ROOT), "--expected-base", "HEAD", "--task", "assign lane",
    ]) == 0

    result = json.loads(capsys.readouterr().out.splitlines()[-1])["assignment"]
    assert result["delivery_state"] == "delivered"
    assert result["delivery_certainty"] == "confirmed"
    assert result["prompt_accepted"] is True
    assert result["execution"] == {
        "state": "unknown",
        "observation_error": "not_observed",
        "observed_at": None,
    }
    assert result["completion_observed"] is False
    assert all(command[3:5] != ["agent", "get"] for command in calls)
    assert all(command[3:5] != ["agent", "read"] for command in calls)


def test_codex_prompt_result_keeps_ambiguous_timeout_unknown() -> None:
    result = subprocess.CompletedProcess(
        ["herdr", "agent", "prompt"],
        1,
        '{"error":{"code":"timeout","message":"wait expired"}}',
        "",
    )

    assert LAUNCHER._classify_codex_prompt_result(result) == {
        "submission": "unknown",
        "prompt_accepted": None,
        "failure_kind": "timeout",
        "reconciliation_required": True,
    }


def test_codex_prompt_result_marks_explicit_rejection_false() -> None:
    result = subprocess.CompletedProcess(
        ["herdr", "agent", "prompt"],
        1,
        "",
        '{"error":{"code":"agent_blocked","message":"blocked"}}',
    )

    assert LAUNCHER._classify_codex_prompt_result(result) == {
        "submission": "rejected",
        "prompt_accepted": False,
        "failure_kind": "agent_blocked",
        "reconciliation_required": False,
    }


def test_codex_prompt_result_marks_agent_not_running_false() -> None:
    result = subprocess.CompletedProcess(
        ["herdr", "agent", "prompt"],
        1,
        '{"error":{"code":"agent_not_running","message":"Codex exited"}}',
        "",
    )

    assert LAUNCHER._classify_codex_prompt_result(result) == {
        "submission": "rejected",
        "prompt_accepted": False,
        "failure_kind": "agent_not_running",
        "reconciliation_required": False,
    }


def test_codex_prompt_result_marks_success_acknowledged() -> None:
    result = subprocess.CompletedProcess(["herdr", "agent", "prompt"], 0, "{}", "")

    assert LAUNCHER._classify_codex_prompt_result(result) == {
        "submission": "acknowledged",
        "prompt_accepted": True,
        "failure_kind": None,
        "reconciliation_required": False,
    }


def test_powershell_literal_escapes_apostrophes() -> None:
    assert LAUNCHER._powershell_literal("worker's task") == "'worker''s task'"


def test_run_converts_timeout_to_launch_blocked(monkeypatch: pytest.MonkeyPatch) -> None:
    def timeout_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], kwargs["timeout"])

    monkeypatch.setattr(LAUNCHER.subprocess, "run", timeout_run)

    with pytest.raises(LAUNCHER.CommandTransportTimeout, match="timed out after 2s"):
        LAUNCHER._run(["herdr", "api", "snapshot"], timeout=2.0)


def test_run_decodes_subprocess_output_as_utf8(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(*args, **kwargs):
        assert kwargs["encoding"] == "utf-8"
        return subprocess.CompletedProcess(args[0], 0, stdout="✓", stderr="")

    monkeypatch.setattr(LAUNCHER.subprocess, "run", fake_run)

    result = LAUNCHER._run(["herdr", "api", "snapshot"])

    assert result.stdout == "✓"


def test_runtime_output_reconfigures_windows_stream_for_utf8() -> None:
    class LegacyStream:
        encoding = "cp1252"

        def __init__(self) -> None:
            self.writes: list[str] = []

        def write(self, value: str) -> None:
            if self.encoding == "cp1252" and "✓" in value:
                raise UnicodeEncodeError("cp1252", value, 0, 1, "unrepresentable")
            self.writes.append(value)

        def reconfigure(self, **kwargs: str) -> None:
            self.encoding = kwargs["encoding"]

    stream = LegacyStream()

    LAUNCHER._write_runtime_output(stream, "✓")

    assert stream.encoding == "utf-8"
    assert stream.writes == ["✓"]


def test_resolve_launch_builds_deepagents_pane_command(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile = LAUNCHER.AgentProfile(
        Path("normal.toml"),
        "normal",
        "9router",
        "combo-normal",
        20,
        "test",
        "do not modify files",
    )
    monkeypatch.setattr(LAUNCHER, "_profile", lambda *args: profile)
    monkeypatch.setattr(LAUNCHER, "_executable", lambda name: f"{name}.exe")
    monkeypatch.setattr(LAUNCHER, "_managed_deepagents_executable", lambda: "dcode-project.exe")
    monkeypatch.setattr(LAUNCHER, "_version", lambda *args, **kwargs: "test")
    monkeypatch.setattr(LAUNCHER, "_git_identity", lambda *args: {"head": "head"})
    monkeypatch.setattr(
        LAUNCHER,
        "_herdr_pane",
        lambda cwd, session, pane, herdr, **kwargs: {
            "pane": {"cwd": str(cwd)},
            "process_info": {},
        },
    )

    command, evidence = LAUNCHER.resolve_launch(
        profile_name="normal",
        session="deepagents-probe",
        pane="w1:p1",
        cwd=ROOT,
        expected_base="HEAD",
        executor="deepagents",
        task="Return exactly DEEPAGENTS_ADAPTER_OK",
    )

    assert command[:-1] == [
        "herdr.exe",
        "--session",
        "deepagents-probe",
        "pane",
        "run",
        "w1:p1",
        "&",
        "'dcode-project.exe'",
        "--role",
        "normal",
        "--json",
        "--timeout",
        "420",
        "--no-mcp",
        "-n",
    ]
    assert command[-1].startswith(
        "'Return exactly DEEPAGENTS_ADAPTER_OK [Runtime Grant: delegation.child_agents = deny]"
    )
    completion_marker = evidence["registry_launcher"]["completion_marker"]
    assert completion_marker is None
    assert "DEEPAGENTS_COMPLETED_" not in command[-1]
    assert "\n" not in command[-1]

    assert evidence["registry_launcher"]["executor"] == "deepagents"
    assert "--executor" not in command
    assert evidence["registry_launcher"]["redacted_runtime_argv"][-1].startswith(
        "task=<sha256:"
    )
    assert evidence["observation"] == {
        "agent_name": "normal-main",
        "executor": "deepagents",
        "pane": "w1:p1",
        "read_commands": ["pane process-info", "pane read"],
        "session": "deepagents-probe",
        "source": "herdr.pane_process",
        "state": "unknown",
        "task_sha256": LAUNCHER._sha256_text("Return exactly DEEPAGENTS_ADAPTER_OK"),
            "delivery_task_sha256": LAUNCHER._sha256_text(command[-1][1:-1]),
        "grant_digest": evidence["registry_launcher"]["grant_digest"],
    }
    assert LAUNCHER._DEEPAGENTS_RUN_TIMEOUT == 1800.0
    performance = evidence["performance"]
    assert set(performance["phase_durations_ms"]) == {
        "preflight",
        "target_discovery",
        "launch_preparation",
        "worker_initialization",
        "delivery",
        "observation",
        "retirement",
    }
    assert all(
        value["status"] == (
            "measured"
            if phase in {"preflight", "target_discovery", "launch_preparation"}
            else "unavailable"
            if phase == "worker_initialization"
            else "not_attempted"
        )
        for phase, value in performance["phase_durations_ms"].items()
    )
    assert performance["phase_durations_ms"]["worker_initialization"]["status"] == "unavailable"
    assert performance["subprocess_counts"]["total"] == 0

def test_local_capabilities_normalize_and_reject_unsafe_values() -> None:
    assert LAUNCHER._normalize_local_capabilities(["Node", "npm-bin"]) == ["node", "npm-bin"]
    for value in ["node/npm", "node npm", "node,npm", "node*", "..", "PATH=node"]:
        with pytest.raises(LAUNCHER.LaunchBlocked):
            LAUNCHER._normalize_local_capabilities([value])
    with pytest.raises(LAUNCHER.LaunchBlocked):
        LAUNCHER._normalize_local_capabilities(["node", "NODE"])


def test_launcher_has_no_controller_capability_availability_owner() -> None:
    assert not hasattr(LAUNCHER, "_verify_local_capabilities")


def test_resolve_launch_enables_direct_mcp_only_for_explicit_selection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile = LAUNCHER.AgentProfile(
        Path("normal.toml"),
        "normal",
        "9router",
        "combo-normal",
        20,
        "test",
        "do not modify files",
    )
    monkeypatch.setattr(LAUNCHER, "_profile", lambda *args: profile)
    monkeypatch.setattr(LAUNCHER, "_executable", lambda name: f"{name}.exe")
    monkeypatch.setattr(LAUNCHER, "_managed_deepagents_executable", lambda: "dcode-project.exe")
    monkeypatch.setattr(LAUNCHER, "_version", lambda *args, **kwargs: "test")
    monkeypatch.setattr(LAUNCHER, "_git_identity", lambda *args: {"head": "head"})
    monkeypatch.setattr(
        LAUNCHER,
        "_herdr_pane",
        lambda cwd, session, pane, herdr, **kwargs: {
            "pane": {"cwd": str(cwd)},
            "process_info": {},
        },
    )

    command, evidence = LAUNCHER.resolve_launch(
        profile_name="normal",
        session="deepagents-probe",
        pane="w1:p1",
        cwd=ROOT,
        expected_base="HEAD",
        executor="deepagents",
        mcp_select=["context7.query_docs"],
        task="Return exactly DIRECT_MCP_OK",
    )

    assert "--no-mcp" not in command
    assert command[command.index("--mcp-select") + 1] == "'context7.query_docs'"
    assert evidence["deepagents"]["mcp_mode"] == "direct"
    assert evidence["deepagents"]["mcp_selection"] == ["context7.query_docs"]


def test_shared_grant_rejects_unsupported_codex_turn_limit() -> None:
    with pytest.raises(LAUNCHER.AttemptContractError, match="turn budget"):
        LAUNCHER.normalize_runtime_grant(
            executor="codex",
            grant_turns="8",
            grant_wall_clock_seconds="native",
            mcp_select=[],
        )


@pytest.mark.parametrize("child_agents", ["allow", "deny", None])
def test_shared_grant_projects_child_agent_authority(child_agents: str | None) -> None:
    grant = LAUNCHER.normalize_runtime_grant(
        executor="codex",
        grant_turns="native",
        grant_wall_clock_seconds="native",
        mcp_select=[],
        grant_child_agents=child_agents,
    )

    assert grant["delegation"]["child_agents"] == (child_agents or "deny")


def test_shared_grant_rejects_invalid_child_agent_authority() -> None:
    with pytest.raises(LAUNCHER.AttemptContractError, match="child_agents"):
        LAUNCHER.normalize_runtime_grant(
            executor="codex",
            grant_turns="native",
            grant_wall_clock_seconds="native",
            mcp_select=[],
            grant_child_agents="maybe",
        )


def test_shared_grant_rejects_unsupported_codex_wall_clock_watchdog() -> None:
    with pytest.raises(LAUNCHER.AttemptContractError, match="numeric wall-clock budget"):
        LAUNCHER.normalize_runtime_grant(
            executor="codex",
            grant_turns="native",
            grant_wall_clock_seconds="600",
            mcp_select=[],
        )


def test_codex_wall_clock_rejection_happens_before_runtime_side_effects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        LAUNCHER,
        "_executable",
        lambda name: (_ for _ in ()).throw(AssertionError(name)),
    )

    with pytest.raises(LAUNCHER.LaunchBlocked, match="wall-clock enforcement"):
        LAUNCHER.resolve_launch(
            profile_name="xhigh",
            session="session",
            pane="pane",
            cwd=ROOT,
            expected_base="HEAD",
            executor="codex",
            grant_wall_clock_seconds="600",
            task="assign lane",
        )


def test_shared_grant_rejects_wall_clock_above_watchdog() -> None:
    with pytest.raises(LAUNCHER.AttemptContractError, match="1800"):
        LAUNCHER.normalize_runtime_grant(
            executor="deepagents",
            grant_turns="native",
            grant_wall_clock_seconds="1801",
            mcp_select=[],
        )


def test_resolve_launch_projects_deepagents_runtime_grant(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile = LAUNCHER.AgentProfile(
        Path("normal.toml"),
        "normal",
        "9router",
        "combo-normal",
        20,
        "test",
        "do not modify files",
    )
    monkeypatch.setattr(LAUNCHER, "_profile", lambda *args: profile)
    monkeypatch.setattr(LAUNCHER, "_executable", lambda name: f"{name}.exe")
    monkeypatch.setattr(LAUNCHER, "_managed_deepagents_executable", lambda: "dcode-project.exe")
    monkeypatch.setattr(LAUNCHER, "_version", lambda *args, **kwargs: "test")
    monkeypatch.setattr(LAUNCHER, "_git_identity", lambda *args: {"head": "head"})
    monkeypatch.setattr(
        LAUNCHER,
        "_herdr_pane",
        lambda cwd, session, pane, herdr, **kwargs: {
            "pane": {"cwd": str(cwd)},
            "process_info": {},
        },
    )

    command, evidence = LAUNCHER.resolve_launch(
        profile_name="normal",
        session="deepagents-probe",
        pane="w1:p1",
        cwd=ROOT,
        expected_base="HEAD",
        executor="deepagents",
        grant_turns="8",
        grant_wall_clock_seconds="600",
        grant_child_agents="allow",
        task="Return exactly GRANT_OK",
    )

    assert "--max-turns" in command
    assert command[command.index("--max-turns") + 1] == "8"
    assert "--timeout" in command
    assert command[command.index("--timeout") + 1] == "600"
    assert evidence["registry_launcher"]["runtime_grant"] == {
        "turns": {"requested": 8, "effective": 8, "enforcement": "runtime"},
        "wall_clock_seconds": {
            "requested": 600,
            "effective": 600,
            "enforcement": "runtime",
        },
        "outer_watchdog_seconds": 1800,
        "mcp_select": [],
        "delegation": {"child_agents": "allow"},
    }
    assert len(evidence["registry_launcher"]["grant_digest"]) == 64
    assert command[-1].startswith(
        "'Return exactly GRANT_OK [Runtime Grant: delegation.child_agents = allow]"
    )
    assert evidence["registry_launcher"]["completion_marker"] is None


def test_resolve_launch_uses_contained_effective_worker_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile = LAUNCHER.AgentProfile(
        Path("normal.toml"), "normal", "9router", "combo-normal", 20, "test", "test"
    )
    monkeypatch.setattr(LAUNCHER, "_profile", lambda *args: profile)
    monkeypatch.setattr(LAUNCHER, "_executable", lambda name: f"{name}.exe")
    monkeypatch.setattr(LAUNCHER, "_managed_deepagents_executable", lambda: "dcode-project.exe")
    monkeypatch.setattr(LAUNCHER, "_version", lambda *args, **kwargs: "test")
    monkeypatch.setattr(LAUNCHER, "_git_identity", lambda *args: {"head": "head"})
    monkeypatch.setattr(
        LAUNCHER,
        "_herdr_pane",
        lambda *args, **kwargs: {"pane": {"cwd": str(ROOT)}, "process_info": {}},
    )

    command, evidence = LAUNCHER.resolve_launch(
        profile_name="normal",
        session="session",
        pane="pane",
        cwd=ROOT,
        expected_base="HEAD",
        executor="deepagents",
        grant_wall_clock_seconds="600",
        remaining_authorized_task_allowance=1000,
        task="task",
    )

    assert command[command.index("--timeout") + 1] == "600"
    assert evidence["registry_launcher"]["runtime_grant"]["wall_clock_seconds"] == {
        "requested": 600,
        "effective": 600,
        "enforcement": "runtime",
    }


def test_resolve_launch_rejects_budget_before_runtime_side_effects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        LAUNCHER,
        "_executable",
        lambda name: (_ for _ in ()).throw(AssertionError(name)),
    )

    with pytest.raises(LAUNCHER.LaunchBlocked, match="does not fit"):
        LAUNCHER.resolve_launch(
            profile_name="normal",
            session="session",
            pane="pane",
            cwd=ROOT,
            expected_base="HEAD",
            executor="deepagents",
            grant_wall_clock_seconds="600",
            remaining_authorized_task_allowance=500,
            task="task",
        )


def test_resolve_launch_rejects_coordinated_launch_without_remaining_authority(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        LAUNCHER,
        "_executable",
        lambda name: (_ for _ in ()).throw(AssertionError(name)),
    )

    grant = LAUNCHER.normalize_runtime_grant(executor="deepagents")
    with pytest.raises(LAUNCHER.LaunchBlocked, match="remaining authorized task allowance"):
        LAUNCHER.resolve_launch(
            profile_name="normal",
            session="session",
            pane="pane",
            cwd=ROOT,
            expected_base="HEAD",
            executor="deepagents",
            task="task",
            assignment_id="assignment-1",
            repository_identity="repo-1",
            plan_identity="plan-1",
            task_sha256=LAUNCHER._sha256_text("task"),
            grant_digest_value=LAUNCHER.grant_digest("deepagents", grant),
        )


def test_resolve_launch_binds_codex_prompt_evidence_to_delivery_task(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    codex_home = tmp_path / "codex-home"
    codex_home.mkdir()
    profile = LAUNCHER.AgentProfile(
        Path("normal.toml"),
        "normal",
        "9router",
        "combo-normal",
        20,
        "test",
        "do not modify files",
    )
    monkeypatch.setattr(LAUNCHER, "_profile", lambda *args: profile)
    monkeypatch.setattr(LAUNCHER, "_executable", lambda name: f"{name}.exe")
    monkeypatch.setattr(LAUNCHER, "_version", lambda *args, **kwargs: "test")
    monkeypatch.setattr(
        LAUNCHER,
        "_codex_runtime",
        lambda *args, **kwargs: {"codex_home": str(codex_home), "stop_hook_scopes": []},
    )
    monkeypatch.setattr(LAUNCHER, "_codex_runtime_mcp_servers", lambda *args, **kwargs: {})
    monkeypatch.setattr(LAUNCHER, "_git_identity", lambda *args: {"head": "head"})
    monkeypatch.setattr(
        LAUNCHER,
        "_herdr_pane",
        lambda cwd, session, pane, herdr, **kwargs: {
            "pane": {"cwd": str(cwd)},
            "process_info": {"foreground_processes": []},
        },
    )

    command, evidence = LAUNCHER.resolve_launch(
        profile_name="normal",
        session="codex-probe",
        pane="w1:p1",
        cwd=ROOT,
        expected_base="HEAD",
        executor="codex",
        grant_child_agents="allow",
        task="original task",
    )

    assert command[command.index("--timeout") + 1] == LAUNCHER._CODEX_START_TIMEOUT_MS
    delivery_task = "original task [Runtime Grant: delegation.child_agents = allow]"
    prompt_argv = evidence["assignment_request"]["redacted_prompt_argv"]
    assert f"task=<sha256:{LAUNCHER._sha256_text(delivery_task)}>" in prompt_argv
    assert evidence["registry_launcher"]["assignment_task_sha256"] == LAUNCHER._sha256_text(
        "original task"
    )
    assert evidence["registry_launcher"]["delivery_task_sha256"] == LAUNCHER._sha256_text(
        delivery_task
    )


def test_resolve_launch_projects_selected_codex_mcp_server(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    codex_home = tmp_path / "codex-home"
    codex_home.mkdir()
    (codex_home / "config.toml").write_text(
        '[mcp_servers.context7]\ncommand = "context7"\n\n'
        '[mcp_servers.open-design]\ncommand = "open-design"\n',
        encoding="utf-8",
    )
    profile = LAUNCHER.AgentProfile(
        Path("normal.toml"),
        "normal",
        "9router",
        "combo-normal",
        20,
        "test",
        "do not modify files",
    )
    monkeypatch.setattr(LAUNCHER, "_profile", lambda *args: profile)
    monkeypatch.setattr(LAUNCHER, "_executable", lambda name: f"{name}.exe")
    monkeypatch.setattr(LAUNCHER, "_version", lambda *args, **kwargs: "test")
    monkeypatch.setattr(
        LAUNCHER,
        "_codex_runtime",
        lambda *args, **kwargs: {"codex_home": str(codex_home), "stop_hook_scopes": []},
    )
    monkeypatch.setattr(
        LAUNCHER,
        "_codex_runtime_mcp_servers",
        lambda *args, **kwargs: {"context7": True, "open-design": True},
    )
    monkeypatch.setattr(LAUNCHER, "_git_identity", lambda *args: {"head": "head"})
    monkeypatch.setattr(
        LAUNCHER,
        "_herdr_pane",
        lambda cwd, session, pane, herdr, **kwargs: {
            "pane": {"cwd": str(cwd)},
            "process_info": {"foreground_processes": []},
        },
    )

    command, evidence = LAUNCHER.resolve_launch(
        profile_name="normal",
        session="codex-probe",
        pane="w1:p1",
        cwd=ROOT,
        expected_base="HEAD",
        executor="codex",
        mcp_select=["context7"],
        task="task",
    )

    assert "mcp_servers.context7.enabled=false" in command
    assert "mcp_servers.context7.enabled=true" in command
    assert "mcp_servers.open-design.enabled=false" in command
    assert evidence["codex"]["mcp_selection"]["effective_servers"] == ("context7",)


def test_resolve_launch_quotes_mcp_selectors_for_powershell(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile = LAUNCHER.AgentProfile(
        Path("normal.toml"),
        "normal",
        "9router",
        "combo-normal",
        20,
        "test",
        "do not modify files",
    )
    monkeypatch.setattr(LAUNCHER, "_profile", lambda *args: profile)
    monkeypatch.setattr(LAUNCHER, "_executable", lambda name: f"{name}.exe")
    monkeypatch.setattr(LAUNCHER, "_managed_deepagents_executable", lambda: "dcode-project.exe")
    monkeypatch.setattr(LAUNCHER, "_version", lambda *args, **kwargs: "test")
    monkeypatch.setattr(LAUNCHER, "_git_identity", lambda *args: {"head": "head"})
    monkeypatch.setattr(
        LAUNCHER,
        "_herdr_pane",
        lambda cwd, session, pane, herdr, **kwargs: {
            "pane": {"cwd": str(cwd)},
            "process_info": {},
        },
    )

    command, _ = LAUNCHER.resolve_launch(
        profile_name="normal",
        session="deepagents-probe",
        pane="w1:p1",
        cwd=ROOT,
        expected_base="HEAD",
        executor="deepagents",
        mcp_select=["context7'; Write-Output hacked"],
        task="task",
    )

    assert "'context7''; Write-Output hacked'" in command


def test_deepagents_profile_binding_uses_lane_worktree(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    lane_root = tmp_path / "lane"
    lane_root.mkdir()
    lead_profile = LAUNCHER.AgentProfile(
        ROOT / "agents" / "normal.toml",
        "normal",
        "9router",
        "model-A",
        20,
        "lead",
        "lead instructions",
    )
    lane_profile = LAUNCHER.AgentProfile(
        lane_root / "agents" / "normal.toml",
        "normal",
        "9router",
        "model-B",
        20,
        "lane",
        "lane instructions",
    )
    seen_roots: list[Path] = []

    def select_profile(agents_root: Path, name: str) -> LAUNCHER.AgentProfile:
        seen_roots.append(agents_root)
        return lane_profile if agents_root == lane_root / "agents" else lead_profile

    monkeypatch.setattr(LAUNCHER, "_profile", select_profile)
    monkeypatch.setattr(LAUNCHER, "_executable", lambda name: f"{name}.exe")
    monkeypatch.setattr(LAUNCHER, "_managed_deepagents_executable", lambda: "dcode-project.exe")
    monkeypatch.setattr(LAUNCHER, "_version", lambda *args, **kwargs: "test")
    monkeypatch.setattr(LAUNCHER, "_git_identity", lambda *args: {"head": "head"})
    monkeypatch.setattr(
        LAUNCHER,
        "_herdr_pane",
        lambda cwd, session, pane, herdr, **kwargs: {
            "pane": {"cwd": str(cwd)},
            "process_info": {},
        },
    )

    command, evidence = LAUNCHER.resolve_launch(
        profile_name="normal",
        session="deepagents-probe",
        pane="w1:p1",
        cwd=lane_root,
        expected_base="HEAD",
        executor="deepagents",
        task="lane task",
    )

    assert seen_roots == [lane_root / "agents"]
    assert evidence["registry_launcher"]["model"] == "model-B"
    assert evidence["registry_launcher"]["profile_source"] == str(lane_profile.source)
    assert command[6] == "&"
    assert command[7] == "'dcode-project.exe'"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"task": None},
        {"task": " "},
        {"task": "x" * (LAUNCHER._MAX_TASK_LENGTH + 1)},
    ],
)
def test_deepagents_task_is_required_and_bounded(
    monkeypatch: pytest.MonkeyPatch,
    kwargs: dict[str, str | None],
) -> None:
    with pytest.raises(LAUNCHER.LaunchBlocked, match="text"):
        LAUNCHER.resolve_launch(
            profile_name="normal",
            session="session",
            pane="pane",
            cwd=ROOT,
            expected_base="HEAD",
            executor="deepagents",
            **kwargs,
        )


@pytest.mark.parametrize("task", [None, " ", "x" * (LAUNCHER._MAX_TASK_LENGTH + 1), "line1\nline2"])
def test_codex_task_is_required_and_bounded(
    monkeypatch: pytest.MonkeyPatch,
    task: str | None,
) -> None:
    with pytest.raises(LAUNCHER.LaunchBlocked, match="(?i)text"):
        LAUNCHER.resolve_launch(
            profile_name="normal",
            session="session",
            pane="pane",
            cwd=ROOT,
            expected_base="HEAD",
            executor="codex",
            task=task,
        )


def test_codex_home_rejects_duplicate_stop_hook_scopes(tmp_path: Path) -> None:
    codex_home = tmp_path / "codex-home"
    codex_home.mkdir()
    project = tmp_path / "project"
    (project / ".codex").mkdir(parents=True)
    hooks = {"hooks": {"Stop": [{"hooks": [{"type": "command", "command": "probe"}]}]}}
    (codex_home / "hooks.json").write_text(json.dumps(hooks), encoding="utf-8")
    (project / ".codex" / "hooks.json").write_text(json.dumps(hooks), encoding="utf-8")

    with pytest.raises(LAUNCHER.LaunchBlocked, match="duplicate Stop-hook scopes"):
        LAUNCHER._codex_runtime(project, codex_home)


def test_main_starts_with_selected_codex_home(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    codex_home = tmp_path / "codex-home"
    codex_home.mkdir()
    evidence = {
        "registry_launcher": {
            "assignment_task_sha256": LAUNCHER._sha256_text("assign lane"),
            "runtime_grant": {"delegation": {"child_agents": "allow"}},
        },
        "codex": {"codex_home": str(codex_home)},
        "herdr": {
            "executable": "herdr.exe",
            "agent_name": "xhigh-main",
            "session": "codex-probe",
            "pane": "w1:p5",
        },
    }
    captured: dict[str, object] = {}
    commands: list[list[str]] = []

    monkeypatch.setattr(LAUNCHER, "resolve_launch", lambda **kwargs: (["herdr"], evidence))

    def fake_run(command, **kwargs):
        commands.append(command)
        captured.update(kwargs)
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(LAUNCHER, "_run", fake_run)

    assert LAUNCHER.main(
        [
            "--profile",
            "xhigh",
            "--session",
            "codex-probe",
            "--pane",
            "w1:p5",
            "--cwd",
            str(ROOT),
            "--expected-base",
            "HEAD",
            "--task",
            "assign lane",
        ]
    ) == 0
    assert captured["env"]["CODEX_HOME"] == str(codex_home.resolve())
    assert commands[:2] == [
        ["herdr"],
        [
            "herdr.exe",
            "--session",
            "codex-probe",
            "agent",
            "prompt",
            "xhigh-main",
            "assign lane [Runtime Grant: delegation.child_agents = allow]",
        ],
    ]
    assert len(commands) == 2
    output = capsys.readouterr().out.splitlines()
    result = json.loads(output[-1])["assignment"]
    assert result["delivery_state"] == "delivered"
    assert result["delivery_certainty"] == "confirmed"
    assert result["prompt_accepted"] is True
    assert result["status"] == "submitted"
    assert result["completion_observed"] is False


def test_main_blocks_codex_prompt_when_started_process_is_gone(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    codex_home = tmp_path / "codex-home"
    codex_home.mkdir()
    evidence = {
        "registry_launcher": {
            "assignment_task_sha256": LAUNCHER._sha256_text("assign lane"),
        },
        "codex": {"codex_home": str(codex_home)},
        "herdr": {
            "executable": "herdr.exe",
            "agent_name": "xhigh-main",
            "session": "codex-probe",
            "pane": "w1:p5",
        },
    }
    start_command = [
        "herdr.exe",
        "--session",
        "codex-probe",
        "agent",
        "start",
        "xhigh-main",
        "--kind",
        "codex",
        "--pane",
        "w1:p5",
    ]
    commands: list[list[str]] = []

    monkeypatch.setattr(LAUNCHER, "resolve_launch", lambda **kwargs: (start_command, evidence))

    def fake_run(command, **kwargs):
        commands.append(command)
        if command[3:5] == ["agent", "get"]:
            return subprocess.CompletedProcess(
                command,
                0,
                json.dumps({"result": {"agent": {"agent_status": "idle"}}}),
                "",
            )
        if command[3:5] == ["pane", "process-info"]:
            return subprocess.CompletedProcess(
                command,
                0,
                json.dumps({
                    "result": {
                        "process_info": {
                            "foreground_processes": [
                                {"pid": 7, "name": "powershell.exe", "children": []}
                            ]
                        }
                    }
                }),
                "",
            )
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(LAUNCHER, "_run", fake_run)

    assert LAUNCHER.main(
        [
            "--profile", "xhigh", "--session", "codex-probe", "--pane", "w1:p5",
            "--cwd", str(ROOT), "--expected-base", "HEAD", "--task", "assign lane",
        ]
    ) == 2
    assert not any(command[3:5] == ["agent", "prompt"] for command in commands)
    output = capsys.readouterr().out.splitlines()
    initial = json.loads(output[0])["registry_launcher"]["attempt_id"]
    result = json.loads(output[-1])["assignment"]
    assert result["status"] == "blocked"
    assert result["delivery_state"] == "not_attempted"
    assert result["failure_kind"] == "Codex process is not running before prompt delivery."
    assert result["attempt_id"] == initial
    assert result["agent_name"] == "xhigh-main"
    assert result["execution"]["state"] == "unknown"
    assert result["task_result"] == {"state": "unverified", "accepted": None}
    assert result["reconciliation_required"] is True


def test_main_times_out_codex_and_verifies_termination(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    codex_home = tmp_path / "codex-home"
    codex_home.mkdir()
    evidence = {
        "registry_launcher": {
            "assignment_task_sha256": LAUNCHER._sha256_text("assign lane"),
            "runtime_grant": {
                "wall_clock_seconds": {
                    "requested": 8,
                    "effective": 8,
                    "enforcement": "outer-watchdog",
                }
            },
        },
        "codex": {"codex_home": str(codex_home)},
        "herdr": {
            "executable": "herdr.exe",
            "agent_name": "xhigh-main",
            "session": "codex-probe",
            "pane": "w1:p5",
        },
    }
    calls = 0
    cleanup = {
        "requested": True,
        "action": "pane-close",
        "verified": True,
        "state": "pane-closed",
    }

    monkeypatch.setattr(LAUNCHER, "resolve_launch", lambda **kwargs: (["herdr"], evidence))
    terminated: list[tuple[object, ...]] = []

    def fake_terminate(*args, **kwargs):
        terminated.append(args)
        return cleanup

    monkeypatch.setattr(LAUNCHER, "_terminate_codex_lane", fake_terminate)

    def fake_run(command, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            return subprocess.CompletedProcess(command, 0, "", "")
        raise LAUNCHER.CommandTransportTimeout("Command timed out after 13s: herdr.exe")

    monkeypatch.setattr(LAUNCHER, "_run", fake_run)
    times = iter([0.0, 1.0, 9.0, 9.0, 9.0, 9.0])
    monkeypatch.setattr(LAUNCHER.time, "monotonic", lambda: next(times))

    assert LAUNCHER.main(
        [
            "--profile", "xhigh", "--session", "auto", "--pane", "auto",
            "--cwd", str(ROOT), "--expected-base", "HEAD", "--task", "assign lane",
            "--grant-wall-clock-seconds", "8",
        ]
    ) == 2
    output = capsys.readouterr().out.splitlines()
    result = json.loads(output[-1])["assignment"]
    assert result["delivery_state"] == "delivery_uncertain"
    assert result["delivery_certainty"] == "unknown"
    assert result["failure_kind"] == "transport_timeout"
    assert result["reconciliation_required"] is True
    assert terminated == []


def test_main_re_resolves_target_after_verified_codex_retry(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    codex_home = tmp_path / "codex-home"
    codex_home.mkdir()
    evidence = {
        "registry_launcher": {
            "assignment_task_sha256": LAUNCHER._sha256_text("assign lane"),
            "runtime_grant": {"delegation": {"child_agents": "deny"}},
        },
        "codex": {"codex_home": str(codex_home)},
        "herdr": {
            "executable": "herdr.exe",
            "codex_executable": "codex.exe",
            "agent_name": "xhigh-main",
            "session": "old-session",
            "pane": "old-pane",
            "pane_cwd": str(ROOT),
            "start_process_ids": [41],
        },
        "assignment_request": {
            "redacted_prompt_argv": ["herdr", "agent", "prompt", "xhigh-main"],
        },
        "observation": {"agent_name": "xhigh-main"},
        "target_resolution": {"status": "selected", "mode": "auto"},
    }
    monkeypatch.setattr(LAUNCHER, "resolve_launch", lambda **kwargs: ([
        "herdr.exe", "--session", "old-session", "agent", "start", "xhigh-main",
        "--pane", "old-pane", "--", "codex",
    ], evidence))
    monkeypatch.setattr(
        LAUNCHER,
        "_reconcile_failed_codex_start",
        lambda *args, **kwargs: {"state": "retired", "cleanup": {"verified": True}},
    )
    monkeypatch.setattr(
        LAUNCHER,
        "_herdr_pane",
        lambda *args, **kwargs: {
            "pane": {"cwd": str(ROOT)},
            "process_info": {"foreground_processes": [{"pid": 7, "name": "powershell.exe", "children": []}]},
        },
    )
    resolutions = iter([
        ("new-session", "new-pane", {"status": "selected", "mode": "auto"}),
    ])
    monkeypatch.setattr(LAUNCHER, "_resolve_target_selector", lambda *args, **kwargs: next(resolutions))
    calls: list[list[str]] = []

    def fake_run(command, **kwargs):
        calls.append(command)
        if len(calls) == 1:
            return subprocess.CompletedProcess(
                command,
                1,
                json.dumps({"error": {"code": "agent_name_taken"}}),
                "",
            )
        if len(calls) == 2:
            return subprocess.CompletedProcess(command, 0, "", "")
        if command[3:5] == ["agent", "prompt"]:
            return subprocess.CompletedProcess(command, 0, "", "")
        if command[3:5] == ["agent", "get"]:
            return subprocess.CompletedProcess(
                command,
                0,
                json.dumps({"result": {"agent": {"agent_status": "idle"}}}),
                "",
            )
        if command[3:5] == ["pane", "process-info"]:
            return subprocess.CompletedProcess(
                command,
                0,
                json.dumps({
                    "result": {
                        "process_info": {
                            "foreground_processes": [
                                    {"pid": 42, "name": "codex.exe", "argv0": "codex.exe", "cwd": str(ROOT), "children": []}
                            ]
                        }
                    }
                }),
                "",
            )
        return subprocess.CompletedProcess(command, 0, json.dumps({"result": ""}), "")

    monkeypatch.setattr(LAUNCHER, "_run", fake_run)

    assert LAUNCHER.main(
        [
            "--profile", "xhigh", "--session", "auto", "--pane", "auto",
            "--cwd", str(ROOT), "--expected-base", "HEAD", "--task", "assign lane",
        ]
    ) == 0

    retry_start = calls[1]
    assert retry_start[retry_start.index("--session") + 1] == "new-session"
    assert retry_start[retry_start.index("--pane") + 1] == "new-pane"
    result = json.loads(capsys.readouterr().out.splitlines()[-1])["assignment"]
    assert result["session"] == "new-session"

def test_main_transport_timeout_marks_delivery_uncertain_without_termination(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    codex_home = tmp_path / "codex-home"
    codex_home.mkdir()
    evidence = {
        "registry_launcher": {
            "assignment_task_sha256": LAUNCHER._sha256_text("assign lane"),
            "delivery_task_sha256": LAUNCHER._sha256_text(
                "assign lane [Runtime Grant: delegation.child_agents = deny]"
            ),
            "grant_digest": "grant-digest",
            "runtime_grant": {"delegation": {"child_agents": "deny"}},
        },
        "codex": {"codex_home": str(codex_home)},
        "herdr": {
            "executable": "herdr.exe",
            "agent_name": "xhigh-main",
            "session": "codex-probe",
            "pane": "w1:p5",
        },
    }
    calls = 0
    timeouts: list[float] = []
    terminated: list[tuple[object, ...]] = []

    monkeypatch.setattr(LAUNCHER, "resolve_launch", lambda **kwargs: (["herdr"], evidence))
    monkeypatch.setattr(LAUNCHER, "_terminate_codex_lane", lambda *args, **kwargs: terminated.append(args))

    def fake_run(command, **kwargs):
        nonlocal calls
        calls += 1
        timeouts.append(kwargs["timeout"])
        if calls == 1:
            return subprocess.CompletedProcess(command, 0, "", "")
        raise LAUNCHER.CommandTransportTimeout("Command timed out before acceptance")

    monkeypatch.setattr(LAUNCHER, "_run", fake_run)

    assert LAUNCHER.main(
        [
            "--profile", "xhigh", "--session", "codex-probe", "--pane", "w1:p5",
            "--cwd", str(ROOT), "--expected-base", "HEAD", "--task", "assign lane",
        ]
    ) == 2
    output = capsys.readouterr().out.splitlines()
    initial = json.loads(output[0])["registry_launcher"]["attempt_id"]
    result = json.loads(output[-1])["assignment"]
    assert result["delivery_state"] == "delivery_uncertain"
    assert result["delivery_certainty"] == "unknown"
    assert result["failure_kind"] == "transport_timeout"
    assert result["prompt_accepted"] is None
    assert result["reconciliation_required"] is True
    assert result["attempt_id"] == initial
    assert result["agent_name"] == "xhigh-main"
    assert terminated == []
    assert timeouts == [LAUNCHER._CODEX_START_TIMEOUT, LAUNCHER._CODEX_ASSIGNMENT_TIMEOUT]


def test_main_reports_deepagents_pane_run_failure(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    evidence = {
        "registry_launcher": {
            "assignment_task_sha256": LAUNCHER._sha256_text("assign lane"),
            "completion_marker": "EXPECTED_MARKER",
        },
        "herdr": {
            "agent_name": "normal-main",
            "session": "session",
            "pane": "pane",
        },
    }
    monkeypatch.setattr(LAUNCHER, "resolve_launch", lambda **kwargs: (["herdr"], evidence))
    monkeypatch.setattr(
        LAUNCHER,
        "_run",
        lambda command, **kwargs: subprocess.CompletedProcess(command, 9, "", "pane failed"),
    )

    assert LAUNCHER.main(
        [
            "--profile", "normal", "--session", "session", "--pane", "pane",
            "--cwd", str(tmp_path), "--expected-base", "HEAD", "--executor", "deepagents",
            "--task", "assign lane",
        ]
    ) == 9
    result = json.loads(capsys.readouterr().out.splitlines()[-1])["assignment"]
    assert result["phase"] == "pane_run"
    assert result["delivery_state"] == "delivery_failed"
    assert result["delivery_certainty"] == "not_delivered"
    assert result["failure_kind"] == "command_exit"


def test_main_immediate_transport_timeout_does_not_expire_long_grant(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    evidence = {
        "registry_launcher": {
            "assignment_task_sha256": LAUNCHER._sha256_text("assign lane"),
            "runtime_grant": {"wall_clock_seconds": {"requested": 600}},
        },
        "codex": {"codex_home": str(tmp_path)},
        "herdr": {
            "executable": "herdr.exe",
            "agent_name": "xhigh-main",
            "session": "session",
            "pane": "pane",
        },
    }
    calls = 0
    terminated: list[tuple[object, ...]] = []
    monkeypatch.setattr(LAUNCHER, "resolve_launch", lambda **kwargs: (["herdr"], evidence))
    monkeypatch.setattr(LAUNCHER, "_terminate_codex_lane", lambda *args, **kwargs: terminated.append(args))

    def fake_run(command, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            return subprocess.CompletedProcess(command, 0, "", "")
        raise LAUNCHER.CommandTransportTimeout("assignment timeout")

    monkeypatch.setattr(LAUNCHER, "_run", fake_run)
    times = iter([0.0, 1.0, 1.0, 1.0, 1.0, 1.0])
    monkeypatch.setattr(LAUNCHER.time, "monotonic", lambda: next(times))

    assert LAUNCHER.main(
        [
            "--profile", "xhigh", "--session", "session", "--pane", "pane",
            "--cwd", str(ROOT), "--expected-base", "HEAD", "--task", "assign lane",
            "--grant-wall-clock-seconds", "600",
        ]
    ) == 2
    result = json.loads(capsys.readouterr().out.splitlines()[-1])["assignment"]
    assert result["delivery_state"] == "delivery_uncertain"
    assert result["delivery_certainty"] == "unknown"
    assert terminated == []


def test_main_watchdog_cleanup_failure_blocks_timeout_completion(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    evidence = {
        "registry_launcher": {
            "assignment_task_sha256": LAUNCHER._sha256_text("assign lane"),
            "runtime_grant": {"wall_clock_seconds": {"requested": 3}},
        },
        "codex": {"codex_home": str(tmp_path)},
        "herdr": {
            "executable": "herdr.exe",
            "agent_name": "xhigh-main",
            "session": "session",
            "pane": "pane",
        },
    }
    calls = 0
    monkeypatch.setattr(LAUNCHER, "resolve_launch", lambda **kwargs: (["herdr"], evidence))
    monkeypatch.setattr(
        LAUNCHER,
        "_terminate_codex_lane",
        lambda *args, **kwargs: {"requested": True, "verified": False, "state": "processes-remain"},
    )
    monkeypatch.setattr(
        LAUNCHER,
        "_herdr_pane",
        lambda *args, **kwargs: {"pane": {"cwd": str(ROOT)}, "process_info": {"foreground_processes": []}},
    )

    def fake_run(command, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            return subprocess.CompletedProcess(command, 0, "", "")
        raise LAUNCHER.CommandTransportTimeout("assignment timeout")

    monkeypatch.setattr(LAUNCHER, "_run", fake_run)
    times = iter([0.0, 4.0, 4.0, 4.0, 4.0, 4.0])
    monkeypatch.setattr(LAUNCHER.time, "monotonic", lambda: next(times))

    assert LAUNCHER.main(
        [
            "--profile", "xhigh", "--session", "session", "--pane", "pane",
            "--cwd", str(ROOT), "--expected-base", "HEAD", "--task", "assign lane",
            "--grant-wall-clock-seconds", "3",
        ]
    ) == 2
    result = json.loads(capsys.readouterr().out.splitlines()[-1])["assignment"]
    assert result["delivery_state"] == "delivery_uncertain"
    assert result["delivery_certainty"] == "unknown"
    assert result["failure_kind"] == "transport_timeout"
    assert result["reconciliation_required"] is True


def test_main_auto_codex_uses_resolved_target(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    codex_home = tmp_path / "codex-home"
    codex_home.mkdir()
    evidence = {
        "registry_launcher": {
            "assignment_task_sha256": LAUNCHER._sha256_text("assign lane"),
        },
        "codex": {"codex_home": str(codex_home)},
        "herdr": {
            "executable": "herdr.exe",
            "agent_name": "xhigh-main",
            "session": "w1",
            "pane": "w1:p5",
        },
    }
    commands: list[list[str]] = []
    monkeypatch.setattr(LAUNCHER, "resolve_launch", lambda **kwargs: (["herdr"], evidence))

    def fake_run(command, **kwargs):
        commands.append(command)
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(LAUNCHER, "_run", fake_run)

    assert LAUNCHER.main(
        [
            "--profile", "xhigh", "--session", "auto", "--pane", "auto",
            "--cwd", str(ROOT), "--expected-base", "HEAD", "--task", "assign lane",
        ]
    ) == 0
    assert commands[-1][1:4] == ["--session", "w1", "agent"]
    assert json.loads(capsys.readouterr().out.splitlines()[-1])["assignment"]["session"] == "w1"


def test_main_reports_failed_assignment_after_start(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    codex_home = tmp_path / "codex-home"
    codex_home.mkdir()
    evidence = {
        "registry_launcher": {
            "assignment_task_sha256": LAUNCHER._sha256_text("assign lane"),
        },
        "codex": {"codex_home": str(codex_home)},
        "herdr": {
            "executable": "herdr.exe",
            "agent_name": "xhigh-main",
            "session": "codex-probe",
            "pane": "w1:p5",
        },
    }
    calls = 0

    monkeypatch.setattr(LAUNCHER, "resolve_launch", lambda **kwargs: (["herdr"], evidence))

    def fake_run(command, **kwargs):
        nonlocal calls
        calls += 1
        return subprocess.CompletedProcess(command, 7 if calls == 1 else 0, "", "start failed")

    monkeypatch.setattr(LAUNCHER, "_run", fake_run)

    assert LAUNCHER.main(
        [
            "--profile", "xhigh", "--session", "codex-probe", "--pane", "w1:p5",
            "--cwd", str(ROOT), "--expected-base", "HEAD", "--task", "assign lane",
        ]
    ) == 7
    output = capsys.readouterr().out.splitlines()
    assignment = json.loads(output[-1])["assignment"]
    assert isinstance(assignment["attempt_id"], str)
    assert assignment["agent_name"] == "xhigh-main"
    assert assignment["delivery_state"] == "delivery_failed"
    assert assignment["delivery_certainty"] == "not_delivered"
    assert assignment["delivery_task_sha256"] == LAUNCHER._sha256_text("assign lane")
    assert assignment["exit_code"] == 7
    assert assignment["failure_kind"] == "command_exit"
    assert assignment["phase"] == "start"
    assert assignment["grant_digest"] is None
    assert assignment["reconciliation_required"] is True
    assert assignment["session"] == "codex-probe"
    assert assignment["status"] == "failed"
    assert assignment["task_sha256"] == LAUNCHER._sha256_text("assign lane")
    assert assignment["delivery"]["state"] == "delivery_failed"
    assert assignment["launcher_exit_code"] == 7
    assert assignment["worker_exit_code"] is None
    assert assignment["performance"]["status"] == "measured"


def test_main_retries_default_agent_name_after_name_taken(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    codex_home = tmp_path / "codex-home"
    codex_home.mkdir()
    evidence = {
        "registry_launcher": {
            "assignment_task_sha256": LAUNCHER._sha256_text("assign lane"),
        },
        "codex": {"codex_home": str(codex_home)},
        "herdr": {
            "executable": "herdr.exe",
            "codex_executable": "codex.exe",
            "agent_name": "normal-main",
            "session": "codex-probe",
            "pane": "w1:p5",
            "pane_cwd": str(ROOT),
        },
        "observation": {"agent_name": "normal-main"},
        "assignment_request": {"redacted_prompt_argv": []},
    }
    commands: list[list[str]] = []
    start_command = [
        "herdr.exe", "--session", "codex-probe", "agent", "start", "normal-main",
        "--kind", "codex", "--pane", "w1:p5", "--timeout", "120000", "--", "codex",
    ]

    monkeypatch.setattr(
        LAUNCHER, "resolve_launch", lambda **kwargs: (start_command, evidence)
    )
    monkeypatch.setattr(
        LAUNCHER,
        "_reconcile_failed_codex_start",
        lambda *args, **kwargs: {"state": "absent", "cleanup": None, "process_ids": []},
    )
    monkeypatch.setattr(
        LAUNCHER,
        "_herdr_pane",
        lambda *args, **kwargs: {"pane": {"cwd": str(ROOT)}, "process_info": {"foreground_processes": []}},
    )

    def fake_run(command, **kwargs):
        commands.append(command)
        if len(commands) == 1:
            return subprocess.CompletedProcess(
                command,
                1,
                '{"error":{"code":"agent_name_taken"}}',
                "",
            )
        if command[3:5] == ["agent", "get"]:
            return subprocess.CompletedProcess(
                command,
                0,
                '{"result":{"agent":{"agent_status":"idle"}}}',
                "",
            )
        if command[3:5] == ["pane", "process-info"]:
            return subprocess.CompletedProcess(
                command,
                0,
                json.dumps({"result": {"process_info": {"foreground_processes": [{"pid": 42, "name": "codex.exe", "argv0": "codex.exe", "cwd": str(ROOT), "children": []}]}}}),
                "",
            )
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(LAUNCHER, "_run", fake_run)

    assert LAUNCHER.main(
        [
            "--profile", "normal", "--session", "codex-probe", "--pane", "w1:p5",
            "--cwd", str(ROOT), "--expected-base", "HEAD", "--task", "assign lane",
        ]
    ) == 0
    assert len(commands) == 5
    retry_name = commands[1][commands[1].index("start") + 1]
    assert retry_name.startswith("normal-main-")
    assert commands[4][commands[4].index("prompt") + 1] == retry_name
    output = capsys.readouterr().out.splitlines()
    initial = json.loads(output[0])["registry_launcher"]["attempt_id"]
    result = json.loads(output[-1])["assignment"]
    assert result["agent_name"] == retry_name
    assert result["prompt_accepted"] is True
    assert result["attempt_id"] != initial
    attempts = result["performance"]["attempts"]
    assert len(attempts) == 2
    assert {item["attempt_id"] for item in attempts} == {initial, result["attempt_id"]}


def test_main_preserves_replacement_attempt_when_start_confirmation_fails(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    codex_home = tmp_path / "codex-home"
    codex_home.mkdir()
    evidence = {
        "registry_launcher": {
            "assignment_task_sha256": LAUNCHER._sha256_text("assign lane"),
        },
        "codex": {"codex_home": str(codex_home)},
        "herdr": {
            "executable": "herdr.exe",
            "codex_executable": "codex.exe",
            "agent_name": "normal-main",
            "session": "codex-probe",
            "pane": "w1:p5",
            "pane_cwd": str(ROOT),
        },
        "observation": {"agent_name": "normal-main"},
        "assignment_request": {"redacted_prompt_argv": []},
    }
    commands: list[list[str]] = []
    start_command = [
        "herdr.exe", "--session", "codex-probe", "agent", "start", "normal-main",
        "--kind", "codex", "--pane", "w1:p5", "--timeout", "120000", "--", "codex",
    ]

    monkeypatch.setattr(
        LAUNCHER, "resolve_launch", lambda **kwargs: (start_command, evidence)
    )
    monkeypatch.setattr(
        LAUNCHER,
        "_reconcile_failed_codex_start",
        lambda *args, **kwargs: {"state": "absent", "cleanup": None, "process_ids": []},
    )
    monkeypatch.setattr(
        LAUNCHER,
        "_herdr_pane",
        lambda *args, **kwargs: {"pane": {"cwd": str(ROOT)}, "process_info": {"foreground_processes": []}},
    )

    def fake_run(command, **kwargs):
        commands.append(command)
        if len(commands) == 1:
            return subprocess.CompletedProcess(
                command, 1, '{"error":{"code":"agent_name_taken"}}', "",
            )
        if command[3:5] == ["agent", "get"]:
            return subprocess.CompletedProcess(
                command, 0, '{"result":{"agent":{"agent_status":"idle"}}}', "",
            )
        if command[3:5] == ["pane", "process-info"]:
            return subprocess.CompletedProcess(
                command,
                0,
                '{"result":{"process_info":{"foreground_processes":[{"pid":42,"name":"powershell.exe","children":[]}]}}}',
                "",
            )
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(LAUNCHER, "_run", fake_run)

    assert LAUNCHER.main(
        [
            "--profile", "normal", "--session", "codex-probe", "--pane", "w1:p5",
            "--cwd", str(ROOT), "--expected-base", "HEAD", "--task", "assign lane",
        ]
    ) == 2
    output = capsys.readouterr().out.splitlines()
    initial = json.loads(output[0])["registry_launcher"]["attempt_id"]
    result = json.loads(output[-1])["assignment"]
    assert result["attempt_id"] != initial
    assert result["agent_name"].startswith("normal-main-")
    assert result["delivery_state"] == "not_attempted"
    assert result["execution"]["state"] == "unknown"
    assert result["task_result"] == {"state": "unverified", "accepted": None}
    assert result["reconciliation_required"] is True


def test_launcher_allows_external_codex_controller(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HERDR_ENV", raising=False)

    environment = LAUNCHER._herdr_environment()

    assert "HERDR_ENV" not in environment


def test_target_selector_requires_both_auto_values() -> None:
    with pytest.raises(LAUNCHER.LaunchBlocked, match="must be used together"):
        LAUNCHER._resolve_target_selector(ROOT, "auto", "w1:p5", "herdr.exe")


def test_pane_ownership_lock_blocks_same_pane_and_releases_after_failure(
    tmp_path: Path,
) -> None:
    with LAUNCHER._pane_ownership_lock(tmp_path, "session", "pane"):
        with pytest.raises(LAUNCHER.LaunchBlocked, match="owns pane"):
            with LAUNCHER._pane_ownership_lock(tmp_path, "session", "pane"):
                pytest.fail("same pane lock acquired")

    with LAUNCHER._pane_ownership_lock(tmp_path, "session", "pane"):
        pass


def test_target_selector_uses_default_session_for_workspace_qualified_pane(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        LAUNCHER,
        "_json_command",
        lambda command, **kwargs: {
            "result": {
                "snapshot": {
                    "panes": [
                        {
                            "workspace_id": "wG",
                            "pane_id": "wG:p1",
                            "cwd": str(ROOT),
                        }
                    ]
                }
            }
        },
    )
    inspected_sessions: list[str] = []

    def inspect_candidate(*args, **kwargs):
        inspected_sessions.append(args[1])
        return {"pane": {}}

    monkeypatch.setattr(LAUNCHER, "_herdr_pane", inspect_candidate)

    session, pane, resolution = LAUNCHER._resolve_target_selector(
        ROOT, "auto", "auto", "herdr.exe",
    )

    assert (session, pane) == ("default", "wG:p1")
    assert inspected_sessions == ["default"]
    assert resolution["status"] == "selected"
    assert resolution["mode"] == "auto"


def test_target_selector_selects_first_deterministic_auto_target(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        LAUNCHER,
        "_json_command",
        lambda command, **kwargs: {
            "result": {
                "snapshot": {
                    "panes": [
                        {"workspace_id": "w1", "pane_id": "w1:p1", "cwd": str(ROOT)},
                        {"workspace_id": "w2", "pane_id": "w2:p1", "cwd": str(ROOT)},
                    ]
                }
            }
        },
    )
    monkeypatch.setattr(LAUNCHER, "_herdr_pane", lambda *args, **kwargs: {"pane": {}})

    session, pane, resolution = LAUNCHER._resolve_target_selector(
        ROOT, "auto", "auto", "herdr.exe",
    )

    assert (session, pane) == ("default", "w1:p1")
    assert resolution["status"] == "selected"
    assert resolution["candidate_count"] == 2


def test_target_selector_reuses_snapshot_and_keeps_rejection_reasons(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    panes = [
        {"workspace_id": "w1", "pane_id": "w1:p1", "cwd": str(ROOT)},
        {"workspace_id": "w2", "pane_id": "w2:p1", "cwd": str(ROOT)},
    ]
    calls: list[list[str]] = []
    monkeypatch.setattr(
        LAUNCHER,
        "_json_command",
        lambda command, **kwargs: calls.append(command) or {"result": {"snapshot": {"panes": panes}}},
    )

    def inspect_candidate(*args, **kwargs):
        if args[2] == "w1:p1":
            raise LAUNCHER.TargetCandidateRejected("Pane already has agent state: w1:p1")
        return {"pane": panes[1]}

    monkeypatch.setattr(LAUNCHER, "_herdr_pane", inspect_candidate)

    session, pane, resolution = LAUNCHER._resolve_target_selector(
        ROOT, "auto", "auto", "herdr.exe",
    )

    assert (session, pane) == ("default", "w2:p1")
    assert len(calls) == 1
    assert resolution["rejections"] == [{
        "session": "default",
        "pane": "w1:p1",
        "reason": "Pane already has agent state: w1:p1",
    }]


def test_target_selector_reports_incomplete_discovery_on_transport_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        LAUNCHER,
        "_json_command",
        lambda command, **kwargs: (_ for _ in ()).throw(
            LAUNCHER.CommandTransportTimeout("snapshot timeout")
        ),
    )

    with pytest.raises(LAUNCHER.TargetResolutionBlocked) as error:
        LAUNCHER._resolve_target_selector(ROOT, "auto", "auto", "herdr.exe")

    assert error.value.resolution["status"] == "incomplete"
    assert error.value.resolution["failure_kind"] == "transport_timeout"


def test_target_selector_rejects_malformed_snapshot_entries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        LAUNCHER,
        "_json_command",
        lambda command, **kwargs: {"result": {"snapshot": {"panes": [None]}}},
    )

    with pytest.raises(LAUNCHER.LaunchBlocked, match="malformed pane entries"):
        LAUNCHER._resolve_target_selector(ROOT, "auto", "auto", "herdr.exe")


def test_target_selector_deadline_is_not_reported_as_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = iter([0.0, 6.0])
    monkeypatch.setattr(LAUNCHER.time, "monotonic", lambda: next(clock))

    with pytest.raises(LAUNCHER.TargetResolutionBlocked) as error:
        LAUNCHER._resolve_target_selector(ROOT, "auto", "auto", "herdr.exe")

    assert error.value.resolution == {
        "status": "incomplete",
        "mode": "auto",
        "failure_kind": "deadline",
    }


def test_target_selector_reports_no_auto_target(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        LAUNCHER,
        "_json_command",
        lambda command, **kwargs: {"result": {"snapshot": {"panes": []}}},
    )

    with pytest.raises(LAUNCHER.TargetResolutionBlocked) as error:
        LAUNCHER._resolve_target_selector(ROOT, "auto", "auto", "herdr.exe")

    assert error.value.resolution == {
        "status": "not_found",
        "mode": "auto",
            "candidate_count": 0,
            "candidates": [],
            "rejections": [],
        }


def test_main_target_resolution_failure_is_not_workflow_blocked(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    error = LAUNCHER.TargetResolutionBlocked(
        "target_resolution=not_found; eligible candidates=0",
        {"status": "not_found", "mode": "auto", "candidate_count": 0, "candidates": []},
    )
    monkeypatch.setattr(LAUNCHER, "resolve_launch", lambda **kwargs: (_ for _ in ()).throw(error))

    assert LAUNCHER.main(["--profile", "xhigh", "--session", "auto", "--pane", "auto", "--cwd", str(ROOT), "--expected-base", "HEAD", "--task", "assign lane"]) == 2
    captured = capsys.readouterr()
    assert "TARGET_RESOLUTION:" in captured.err
    assert "BLOCKED:" not in captured.err
    result = json.loads(captured.out.splitlines()[-1])
    assert result["target_resolution"]["status"] == "not_found"
    assert result["assignment"]["performance"]["status"] == "measured"
    assert all(
        phase["status"] == "unavailable"
        for phase in result["assignment"]["performance"]["phase_durations_ms"].values()
    )


def test_deepagents_main_strips_herdr_environment(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    evidence = {
        "registry_launcher": {
            "assignment_task_sha256": LAUNCHER._sha256_text("assign lane"),
            "completion_marker": "EXPECTED_MARKER",
        },
        "herdr": {
            "agent_name": "normal-main",
            "session": "session",
            "pane": "pane",
            "executable": "herdr.exe",
        },
    }
    captured: dict[str, object] = {}
    monkeypatch.setenv("HERDR_ENV", "1")
    monkeypatch.setattr(LAUNCHER, "resolve_launch", lambda **kwargs: (["herdr"], evidence))
    monkeypatch.setattr(
        LAUNCHER,
        "_deepagents_completion_evidence",
        lambda *args, **kwargs: {
            "state": "completed",
            "marker_present": True,
            "report_present": True,
            "report_sha256": "report",
            "report_chars": 1,
            "foreground_processes": ["powershell.exe"],
            "observation_error": None,
        },
    )
    monkeypatch.setattr(
        LAUNCHER,
        "_read_deepagents_receipt",
        lambda *args, **kwargs: {
            "state": "confirmed",
            "worker_state": "exited",
            "worker_exit_code": 0,
            "descendant_state": "terminated",
            "cleanup_state": "removed",
            "role_views_state": "removed",
            "recovery_required": False,
        },
    )
    monkeypatch.setattr(
        LAUNCHER,
        "_read_deepagents_task_result",
        lambda *args, **kwargs: _confirmed_task_result(),
    )
    monkeypatch.setattr(
        LAUNCHER,
        "_herdr_pane",
        lambda *args, **kwargs: {"pane": {"cwd": str(ROOT)}, "process_info": {"foreground_processes": []}},
    )

    def fake_run(command, **kwargs):
        captured.update(kwargs)
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(LAUNCHER, "_run", fake_run)

    assert LAUNCHER.main(
        [
            "--profile", "normal", "--session", "session", "--pane", "pane",
            "--cwd", str(ROOT), "--expected-base", "HEAD", "--executor", "deepagents",
            "--task", "assign lane",
        ]
    ) == 0
    assert "HERDR_ENV" not in captured["env"]
    assert json.loads(capsys.readouterr().out.splitlines()[-1])["assignment"]["status"] == "completed"


def test_deepagents_main_uses_grant_wall_clock_for_completion_observation(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    evidence = {
        "registry_launcher": {
            "assignment_task_sha256": LAUNCHER._sha256_text("assign lane"),
            "completion_marker": "EXPECTED_MARKER",
            "runtime_grant": {"wall_clock_seconds": {"requested": 120}},
        },
        "herdr": {
            "agent_name": "normal-main",
            "session": "session",
            "pane": "pane",
            "executable": "herdr.exe",
        },
    }
    captured: dict[str, object] = {}
    monkeypatch.setattr(LAUNCHER, "resolve_launch", lambda **kwargs: (["herdr"], evidence))
    monkeypatch.setattr(
        LAUNCHER,
        "_deepagents_completion_evidence",
        lambda *args, **kwargs: captured.update(kwargs) or {
            "state": "completed",
            "marker_present": True,
            "report_present": True,
            "report_sha256": "report",
            "report_chars": 1,
            "foreground_processes": ["powershell.exe"],
            "observation_error": None,
        },
    )
    monkeypatch.setattr(
        LAUNCHER,
        "_run",
        lambda command, **kwargs: subprocess.CompletedProcess(command, 0, "", ""),
    )
    monkeypatch.setattr(
        LAUNCHER,
        "_read_deepagents_receipt",
        lambda *args, **kwargs: {
            "state": "confirmed",
            "worker_state": "exited",
            "worker_exit_code": 0,
            "descendant_state": "terminated",
            "cleanup_state": "removed",
            "recovery_required": False,
        },
    )
    monkeypatch.setattr(
        LAUNCHER,
        "_read_deepagents_task_result",
        lambda *args, **kwargs: _confirmed_task_result(),
    )

    assert LAUNCHER.main(
        [
            "--profile", "normal", "--session", "session", "--pane", "pane",
            "--cwd", str(tmp_path), "--expected-base", "HEAD", "--executor", "deepagents",
            "--task", "assign lane", "--grant-wall-clock-seconds", "120",
        ]
    ) == 0
    assert captured["completion_wait_seconds"] == 120.0
    capsys.readouterr()


def test_deepagents_main_blocks_delivery_without_completion_report(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    evidence = {
        "registry_launcher": {
            "assignment_task_sha256": LAUNCHER._sha256_text("assign lane"),
            "completion_marker": "EXPECTED_MARKER",
        },
        "herdr": {
            "agent_name": "normal-main",
            "session": "session",
            "pane": "pane",
            "executable": "herdr.exe",
        },
    }
    monkeypatch.setattr(LAUNCHER, "resolve_launch", lambda **kwargs: (["herdr"], evidence))
    monkeypatch.setattr(
        LAUNCHER,
        "_run",
        lambda command, **kwargs: subprocess.CompletedProcess(command, 0, "", ""),
    )
    monkeypatch.setattr(
        LAUNCHER,
        "_deepagents_completion_evidence",
        lambda *args, **kwargs: {
            "state": "no-report",
            "report_present": False,
            "report_sha256": LAUNCHER._sha256_text(""),
            "report_chars": 0,
            "foreground_processes": ["powershell.exe"],
            "observation_error": None,
        },
    )

    assert LAUNCHER.main(
        [
            "--profile", "normal", "--session", "session", "--pane", "pane",
            "--cwd", str(ROOT), "--expected-base", "HEAD", "--executor", "deepagents",
            "--task", "assign lane",
        ]
    ) == 2
    assignment = json.loads(capsys.readouterr().out.splitlines()[-1])["assignment"]
    assert assignment["delivery_state"] == "delivered"
    assert assignment["status"] == "unknown"
    assert assignment["task_accepted"] is None
    assert assignment["reconciliation_required"] is True


@pytest.mark.parametrize(("worker_exit_code", "expected_return"), [(0, 0), (7, 7)])
def test_deepagents_main_waits_for_receipt_after_terminal_observation(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    worker_exit_code: int,
    expected_return: int,
) -> None:
    evidence = {
        "registry_launcher": {
            "assignment_task_sha256": LAUNCHER._sha256_text("assign lane"),
            "completion_marker": "EXPECTED_MARKER",
        },
        "herdr": {
            "agent_name": "normal-main",
            "session": "session",
            "pane": "pane",
            "executable": "herdr.exe",
        },
    }
    monkeypatch.setattr(
        LAUNCHER,
        "resolve_launch",
        lambda **kwargs: (["herdr", "-n", "task"], evidence),
    )
    monkeypatch.setattr(
        LAUNCHER,
        "_run",
        lambda command, **kwargs: subprocess.CompletedProcess(command, 0, "", ""),
    )
    monkeypatch.setattr(
        LAUNCHER,
        "_deepagents_completion_evidence",
        lambda *args, **kwargs: {
            "state": "completed",
            "marker_present": True,
            "report_present": True,
            "report_sha256": "report",
            "report_chars": 1,
            "foreground_processes": ["powershell.exe"],
            "observation_error": None,
            "lifecycle_receipt": {
                "state": "confirmed",
                "worker_state": "exited",
                "worker_exit_code": worker_exit_code,
                "descendant_state": "terminated",
                "cleanup_state": "removed",
                "role_views_state": "removed",
                "recovery_required": False,
            },
        },
    )
    monkeypatch.setattr(
        LAUNCHER,
        "_read_deepagents_task_result",
        lambda *args, **kwargs: _confirmed_task_result(),
    )

    assert LAUNCHER.main(
        [
            "--profile", "normal", "--session", "session", "--pane", "pane",
            "--cwd", str(ROOT), "--expected-base", "HEAD", "--executor", "deepagents",
            "--task", "assign lane",
        ]
    ) == expected_return
    assignment = json.loads(capsys.readouterr().out.splitlines()[-1])["assignment"]
    assert assignment["status"] == ("completed" if worker_exit_code == 0 else "failed")
    assert assignment["execution"]["worker_exit_code"] == worker_exit_code
    assert assignment["launcher_exit_code"] == assignment["exit_code"] == expected_return


def test_deepagents_main_exposes_confirmed_receipt_capability_proof(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    capability_digest = hashlib.sha256(b'["git"]').hexdigest()
    evidence = {
        "registry_launcher": {
            "assignment_task_sha256": LAUNCHER._sha256_text("assign lane"),
            "completion_marker": "EXPECTED_MARKER",
            "local_capabilities": {
                "requested": ["git"],
                "effective": ["git"],
                "verification_commands": ["git"],
                "source_task_sha256": LAUNCHER._sha256_text("assign lane"),
                "digest": capability_digest,
            },
        },
        "herdr": {
            "agent_name": "normal-main",
            "session": "session",
            "pane": "pane",
            "executable": "herdr.exe",
        },
    }
    receipt = {
        "state": "confirmed",
        "worker_state": "exited",
        "worker_exit_code": 0,
        "descendant_state": "terminated",
        "cleanup_state": "removed",
        "recovery_required": False,
        "capability_state": "confirmed",
        "capabilities": {
            "requested": ["git"],
            "passed_to_worker": ["git"],
            "validated_available": ["git"],
            "digest": capability_digest,
            "validation_error": None,
        },
    }
    monkeypatch.setattr(LAUNCHER, "resolve_launch", lambda **kwargs: (["herdr", "-n", "task"], evidence))
    monkeypatch.setattr(
        LAUNCHER,
        "_run",
        lambda command, **kwargs: subprocess.CompletedProcess(command, 0, "", ""),
    )
    monkeypatch.setattr(
        LAUNCHER,
        "_deepagents_completion_evidence",
        lambda *args, **kwargs: {
            "state": "completed",
            "marker_present": True,
            "report_present": True,
            "foreground_processes": ["powershell.exe"],
            "observation_error": None,
            "lifecycle_receipt": receipt,
        },
    )
    monkeypatch.setattr(
        LAUNCHER,
        "_read_deepagents_task_result",
        lambda *args, **kwargs: _confirmed_task_result(),
    )

    assert LAUNCHER.main([
        "--profile", "normal", "--session", "session", "--pane", "pane",
        "--cwd", str(ROOT), "--expected-base", "HEAD", "--executor", "deepagents",
        "--local-capability", "git", "--task", "assign lane",
    ]) == 0
    assignment = json.loads(capsys.readouterr().out.splitlines()[-1])["assignment"]
    assert assignment["capability_state"] == "confirmed"
    assert assignment["capabilities"] == receipt["capabilities"]


def test_deepagents_main_does_not_promote_projected_capabilities_without_receipt_proof(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    evidence = {
        "registry_launcher": {
            "assignment_task_sha256": LAUNCHER._sha256_text("assign lane"),
            "completion_marker": "EXPECTED_MARKER",
            "local_capabilities": {
                "requested": ["git"],
                "effective": ["git"],
                "verification_commands": ["git"],
                "source_task_sha256": LAUNCHER._sha256_text("assign lane"),
                "digest": hashlib.sha256(b'["git"]').hexdigest(),
            },
        },
        "herdr": {
            "agent_name": "normal-main",
            "session": "session",
            "pane": "pane",
            "executable": "herdr.exe",
        },
    }
    monkeypatch.setattr(LAUNCHER, "resolve_launch", lambda **kwargs: (["herdr", "-n", "task"], evidence))
    monkeypatch.setattr(
        LAUNCHER,
        "_run",
        lambda command, **kwargs: subprocess.CompletedProcess(command, 0, "", ""),
    )
    monkeypatch.setattr(
        LAUNCHER,
        "_deepagents_completion_evidence",
        lambda *args, **kwargs: {
            "state": "completed",
            "marker_present": True,
            "report_present": True,
            "foreground_processes": ["powershell.exe"],
            "observation_error": None,
            "lifecycle_receipt": {
                "state": "confirmed",
                "worker_state": "exited",
                "worker_exit_code": 0,
                "descendant_state": "terminated",
                "cleanup_state": "removed",
                "recovery_required": False,
                "capability_state": "unavailable",
            },
        },
    )
    monkeypatch.setattr(
        LAUNCHER,
        "_read_deepagents_task_result",
        lambda *args, **kwargs: _confirmed_task_result(),
    )

    assert LAUNCHER.main([
        "--profile", "normal", "--session", "session", "--pane", "pane",
        "--cwd", str(ROOT), "--expected-base", "HEAD", "--executor", "deepagents",
        "--local-capability", "git", "--task", "assign lane",
    ]) == 0
    assignment = json.loads(capsys.readouterr().out.splitlines()[-1])["assignment"]
    assert assignment["capability_state"] == "unavailable"
    assert "capabilities" not in assignment


def test_deepagents_zero_exit_failed_report_is_not_completion() -> None:
    result = LAUNCHER._classify_deepagents_outcome(
        delivery={"state": "delivered", "certainty": "confirmed", "prompt_accepted": True},
        observation={"state": "failed", "report_present": True, "observation_error": None},
        receipt={
            "state": "confirmed",
            "worker_state": "exited",
            "worker_exit_code": 0,
            "descendant_state": "terminated",
            "cleanup_state": "removed",
            "role_views_state": "removed",
            "recovery_required": False,
        },
        fallback_failure_kind=None,
    )

    assert result["execution"]["state"] == "completed"
    assert result["task_result"] == {"state": "unverified", "accepted": None}
    assert result["status"] == "completed"
    assert result["failure_kind"] == "task_result_unverified"
    assert result["launcher_exit_code"] == 2
    assert result["reconciliation_required"] is True
    assert result["delivery"]["prompt_accepted"] is True


def test_deepagents_main_rejects_completion_with_observer_error(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    evidence = {
        "registry_launcher": {
            "assignment_task_sha256": LAUNCHER._sha256_text("assign lane"),
            "completion_marker": "EXPECTED_MARKER",
        },
        "herdr": {
            "agent_name": "normal-main",
            "session": "session",
            "pane": "pane",
            "executable": "herdr.exe",
        },
    }
    monkeypatch.setattr(LAUNCHER, "resolve_launch", lambda **kwargs: (["herdr"], evidence))
    monkeypatch.setattr(
        LAUNCHER,
        "_run",
        lambda command, **kwargs: subprocess.CompletedProcess(command, 0, "", ""),
    )
    monkeypatch.setattr(
        LAUNCHER,
        "_deepagents_completion_evidence",
        lambda *args, **kwargs: {
            "state": "completed",
            "marker_present": True,
            "report_present": True,
            "report_sha256": "report",
            "report_chars": 1,
            "foreground_processes": ["powershell.exe"],
            "observation_error": "pane read failed",
        },
    )

    assert LAUNCHER.main(
        [
            "--profile", "normal", "--session", "session", "--pane", "pane",
            "--cwd", str(ROOT), "--expected-base", "HEAD", "--executor", "deepagents",
            "--task", "assign lane",
        ]
    ) == 2
    assignment = json.loads(capsys.readouterr().out.splitlines()[-1])["assignment"]
    assert assignment["status"] == "unknown"
    assert assignment["task_accepted"] is None
    assert assignment["reconciliation_required"] is True


@pytest.mark.parametrize(
    ("receipt", "observation", "expected"),
    [
        (
            {
                "state": "confirmed",
                "worker_state": "exited",
                "worker_exit_code": 7,
                "descendant_state": "terminated",
                "cleanup_state": "removed",
                "role_views_state": "removed",
                "recovery_required": False,
            },
            {"report_present": True, "observation_error": None},
            {"status": "failed", "execution": "failed", "exit_code": 7},
        ),
        (
            {
                "state": "confirmed",
                "worker_state": "exited",
                "worker_exit_code": 0,
                "descendant_state": "terminated",
                "cleanup_state": "removed",
                "role_views_state": "removed",
                "recovery_required": False,
            },
            {"report_present": False, "observation_error": None},
            {"status": "completed", "execution": "completed", "exit_code": 2},
        ),
        (
            {
                "state": "confirmed",
                "worker_state": "exited",
                "worker_exit_code": 0,
                "descendant_state": "terminated",
                "cleanup_state": "preserved",
                "role_views_state": "preserved",
                "recovery_required": True,
            },
            {"report_present": True, "observation_error": None},
            {"status": "completed", "execution": "completed", "exit_code": 2},
        ),
        (
            {
                "state": "confirmed",
                "worker_state": "start_failed",
                "worker_exit_code": None,
                "descendant_state": "not_started",
                "cleanup_state": "removed",
                "role_views_state": "removed",
                "recovery_required": False,
            },
            {"report_present": False, "observation_error": None},
            {"status": "start_failed", "execution": "start_failed", "exit_code": 2},
        ),
        (
            {
                "state": "confirmed",
                "worker_state": "exited",
                "worker_exit_code": 0,
                "descendant_state": "unknown",
                "cleanup_state": "removed",
                "role_views_state": "removed",
                "recovery_required": False,
            },
            {"report_present": True, "observation_error": None},
            {"status": "completed", "execution": "completed", "exit_code": 2},
        ),
        (
            {"state": "unknown", "detail": "receipt unavailable"},
            {"report_present": True, "observation_error": None},
            {"status": "unknown", "execution": "unknown", "exit_code": 2},
        ),
    ],
)
def test_deepagents_outcome_matrix(
    receipt: dict[str, object],
    observation: dict[str, object],
    expected: dict[str, object],
) -> None:
    result = LAUNCHER._classify_deepagents_outcome(
        delivery={"state": "delivered", "certainty": "confirmed", "prompt_accepted": True},
        observation=observation,
        receipt=receipt,
        fallback_failure_kind=None,
    )

    assert result["status"] == expected["status"]
    assert result["execution"]["state"] == expected["execution"]
    assert result["launcher_exit_code"] == expected["exit_code"]
    assert result["delivery"]["prompt_accepted"] is True
    if receipt.get("state") == "confirmed" and receipt.get("worker_state") == "exited":
        assert result["execution"]["worker_exit_code"] == receipt["worker_exit_code"]


def test_deepagents_task_state_requires_report_for_completion() -> None:
    assert LAUNCHER._deepagents_task_state(
        [{"name": "powershell.exe"}],
        "Running task non-interactively...\nCOMPLETED\nEXPECTED_MARKER\nUsage Stats\n",
        "EXPECTED_MARKER",
    ) == "completed"
    assert LAUNCHER._deepagents_task_state(
        [{"name": "powershell.exe"}],
        "Running task non-interactively...\nCOMPLETED\nOTHER_MARKER\n",
        "EXPECTED_MARKER",
    ) == "no-report"
    assert LAUNCHER._deepagents_task_state(
        [{"name": "powershell.exe"}],
        "Running task non-interactively...\nCOMPLETED\nEXPECTED_MARKER\n",
        "EXPECTED_MARKER",
    ) == "completed"
    assert LAUNCHER._deepagents_task_state(
        [{"name": "powershell.exe"}],
        "Running task non-interactively...\n",
        "EXPECTED_MARKER",
    ) == "no-report"
    assert LAUNCHER._deepagents_task_state(
        [{"name": "python.exe"}],
        "Running task non-interactively...\n",
        "EXPECTED_MARKER",
    ) == "running"


@pytest.mark.parametrize(
    ("pane_output", "expected_state"),
    [
        ("Running task non-interactively...\nFAIL\n", "failed"),
        ("Running task non-interactively...\nFAIL: fixture write failed.\n", "failed"),
        ("Running task non-interactively...\nBLOCKED\n", "failed"),
        ("Running task non-interactively...\nBLOCKED: fixture validation failed.\n", "failed"),
        ("Running task non-interactively...\n[FAIL] Task failed\n", "failed"),
        ('Running task non-interactively...\nExample: "FAIL: fixture write failed."\n', "no-report"),
        ("Running task non-interactively...\nfixture_status = FAIL\n", "no-report"),
        ("Running task non-interactively...\n  FAIL: fixture write failed.\n", "no-report"),
        ("stale FAIL: prior attempt\nRunning task non-interactively...\nCOMPLETED\nEXPECTED_MARKER\n", "completed"),
    ],
)
def test_deepagents_task_state_detects_terminal_failure_verdicts(
    pane_output: str,
    expected_state: str,
) -> None:
    assert LAUNCHER._deepagents_task_state(
        [{"name": "powershell.exe"}],
        pane_output,
        "EXPECTED_MARKER",
    ) == expected_state


@pytest.mark.parametrize("verdict", ["FAIL: fixture write failed.", "BLOCKED"])
def test_deepagents_main_reports_terminal_failure_verdict(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    verdict: str,
) -> None:
    evidence = {
        "registry_launcher": {
            "assignment_task_sha256": LAUNCHER._sha256_text("assign lane"),
            "completion_marker": "EXPECTED_MARKER",
        },
        "herdr": {
            "agent_name": "normal-main",
            "session": "session",
            "pane": "pane",
            "executable": "herdr.exe",
        },
    }
    monkeypatch.setattr(LAUNCHER, "resolve_launch", lambda **kwargs: (["herdr", "-n", "task"], evidence))
    monkeypatch.setattr(
        LAUNCHER,
        "_run",
        lambda command, **kwargs: subprocess.CompletedProcess(command, 0, "", ""),
    )
    monkeypatch.setattr(
        LAUNCHER,
        "_deepagents_completion_evidence",
        lambda *args, **kwargs: {
            "state": "failed",
            "marker_present": True,
            "report_present": True,
            "report_sha256": LAUNCHER._sha256_text(verdict),
            "report_chars": len(verdict),
            "foreground_processes": ["powershell.exe"],
            "observation_error": None,
            "lifecycle_receipt": {
                "state": "confirmed",
                "worker_state": "exited",
                "worker_exit_code": 0,
                "descendant_state": "terminated",
                "cleanup_state": "removed",
                "role_views_state": "removed",
                "recovery_required": False,
            },
        },
    )
    monkeypatch.setattr(
        LAUNCHER,
        "_read_deepagents_task_result",
        lambda *args, **kwargs: _confirmed_task_result("failed"),
    )

    assert LAUNCHER.main(
        [
            "--profile", "normal", "--session", "session", "--pane", "pane",
            "--cwd", str(ROOT), "--expected-base", "HEAD", "--executor", "deepagents",
            "--task", "assign lane",
        ]
    ) == 2
    assignment = json.loads(capsys.readouterr().out.splitlines()[-1])["assignment"]
    assert assignment["status"] == "failed"
    assert assignment["task_result"] == {
        "state": "reported_failed",
        "accepted": None,
        "status": "failed",
    }
    assert assignment["task_accepted"] is None
    assert assignment["execution"]["worker_exit_code"] == 0
    assert assignment["exit_code"] == assignment["launcher_exit_code"] == 2
    assert assignment["reconciliation_required"] is True


@pytest.mark.parametrize("failure", ["process-info", "pane-read"])
def test_deepagents_completion_rejects_observer_error(
    monkeypatch: pytest.MonkeyPatch,
    failure: str,
) -> None:
    process_result = (
        subprocess.CompletedProcess([], 1, "", "process-info failed")
        if failure == "process-info"
        else subprocess.CompletedProcess([], 0, json.dumps({"result": {"process_info": {"foreground_processes": [{"name": "powershell.exe"}]}}}), "")
    )
    read_result = (
        subprocess.CompletedProcess([], 1, "", "pane read failed")
        if failure == "pane-read"
        else subprocess.CompletedProcess([], 0, json.dumps({"result": "COMPLETED\nPROBE_OK"}), "")
    )
    def run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        if "process-info" in command:
            return process_result
        if "wait-output" in command:
            return subprocess.CompletedProcess(command, 1, "", "unsupported")
        return read_result

    monkeypatch.setattr(LAUNCHER, "_run", run)

    evidence = LAUNCHER._deepagents_completion_snapshot(
        "herdr.exe",
        "session",
        "pane",
        env={},
        expected_marker="PROBE_OK",
    )

    assert evidence["state"] == "no-report"
    assert evidence["report_present"] is False
    assert evidence["observation_error"] in {"pane process-info failed", "pane read failed"}


def test_deepagents_completion_converts_transport_timeout_to_bounded_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def timeout_run(*args, **kwargs):
        raise LAUNCHER.CommandTransportTimeout("observation timeout")

    monkeypatch.setattr(LAUNCHER, "_run", timeout_run)

    evidence = LAUNCHER._deepagents_completion_snapshot(
        "herdr.exe",
        "session",
        "pane",
        env={},
        expected_marker="MARKER",
        deadline=LAUNCHER.time.monotonic() + 0.1,
    )

    assert evidence["state"] == "no-report"
    assert evidence["report_present"] is False
    assert evidence["observation_error"] == "pane process-info transport timeout"
    assert evidence["observed_at"] > 0


def test_deepagents_snapshot_distinguishes_observation_deadline_from_transport_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[str]] = []
    monkeypatch.setattr(LAUNCHER, "_run", lambda command, **kwargs: calls.append(command))
    monkeypatch.setattr(LAUNCHER.time, "monotonic", lambda: 1.0)

    evidence = LAUNCHER._deepagents_completion_snapshot(
        "herdr.exe",
        "session",
        "pane",
        env={},
        expected_marker="MARKER",
        deadline=0.5,
    )

    assert calls == []
    assert evidence["observation_error"] == "observation deadline exceeded"
    assert evidence["observation_deadline_exceeded"] is True


@pytest.mark.parametrize("crossing_command", ["process-info", "pane-read"])
def test_deepagents_snapshot_reclassifies_transport_timeout_after_deadline(
    monkeypatch: pytest.MonkeyPatch,
    crossing_command: str,
) -> None:
    process_info = json.dumps({
        "result": {
            "process_info": {
                "foreground_processes": [{"name": "powershell.exe"}],
            },
        },
    })
    clock = [0.0]
    calls: list[list[str]] = []

    def run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        if "wait-output" in command:
            return subprocess.CompletedProcess(command, 1, "", "unsupported")
        if crossing_command == "process-info" and "process-info" in command:
            clock[0] = 2.0
            raise LAUNCHER.CommandTransportTimeout("transport timeout")
        if "process-info" in command:
            return subprocess.CompletedProcess(command, 0, process_info, "")
        if "read" not in command:
            return subprocess.CompletedProcess(command, 0, json.dumps({"result": ""}), "")
        clock[0] = 2.0
        raise LAUNCHER.CommandTransportTimeout("transport timeout")

    monkeypatch.setattr(LAUNCHER, "_run", run)
    monkeypatch.setattr(LAUNCHER.time, "monotonic", lambda: clock[0])

    evidence = LAUNCHER._deepagents_completion_snapshot(
        "herdr.exe",
        "session",
        "pane",
        env={},
        expected_marker="MARKER",
        deadline=1.0,
    )

    assert any(
        "process-info" in command if crossing_command == "process-info" else "read" in command
        for command in calls
    )
    assert evidence["observation_error"] == "observation deadline exceeded"
    assert evidence["observation_deadline_exceeded"] is True


def test_deepagents_completion_waits_for_delayed_report(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    process_info = json.dumps({
        "result": {
            "process_info": {
                "foreground_processes": [{"name": "powershell.exe"}],
            },
        },
    })
    responses = {
        "process-info": iter([
            subprocess.CompletedProcess([], 0, process_info, ""),
            subprocess.CompletedProcess([], 0, process_info, ""),
        ]),
        "read": iter([
            subprocess.CompletedProcess([], 0, json.dumps({"result": "Running task..."}), ""),
            subprocess.CompletedProcess([], 0, json.dumps({"result": "COMPLETED\nPROBE_OK"}), ""),
        ]),
    }

    def run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        if "process-info" in command:
            return next(responses["process-info"])
        if "read" in command:
            return next(responses["read"])
        return subprocess.CompletedProcess(command, 1, "", "unsupported")

    clock = [0.0]
    sleeps: list[float] = []
    monkeypatch.setattr(LAUNCHER, "_run", run)
    monkeypatch.setattr(LAUNCHER.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(LAUNCHER.time, "sleep", lambda seconds: (sleeps.append(seconds), clock.__setitem__(0, clock[0] + seconds)))

    evidence = LAUNCHER._deepagents_completion_evidence(
        "herdr.exe",
        "session",
        "pane",
        env={},
        expected_marker="PROBE_OK",
    )

    assert evidence["state"] == "completed"
    assert sleeps


def test_deepagents_completion_allows_report_after_ninety_seconds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = [0.0]
    sleeps: list[float] = []
    snapshots = iter([
        {"state": "running", "report_present": False},
        {"state": "completed", "report_present": True},
    ])
    monkeypatch.setattr(
        LAUNCHER,
        "_DEEPAGENTS_COMPLETION_POLL_SECONDS",
        100.0,
    )
    monkeypatch.setattr(
        LAUNCHER,
        "_deepagents_completion_snapshot",
        lambda *args, **kwargs: next(snapshots),
    )
    monkeypatch.setattr(LAUNCHER.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(
        LAUNCHER.time,
        "sleep",
        lambda seconds: (sleeps.append(seconds), clock.__setitem__(0, clock[0] + seconds)),
    )

    evidence = LAUNCHER._deepagents_completion_evidence(
        "herdr.exe",
        "session",
        "pane",
        env={},
        expected_marker="PROBE_OK",
    )

    assert evidence["state"] == "completed"
    assert sleeps == [100.0]


def test_deepagents_completion_uses_receipt_before_first_pane_command(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    receipt = {
        "state": "confirmed",
        "worker_state": "exited",
        "worker_exit_code": 0,
        "descendant_state": "terminated",
        "cleanup_state": "removed",
        "recovery_required": False,
    }
    snapshots: list[str] = []
    monkeypatch.setattr(LAUNCHER, "_read_deepagents_receipt", lambda *args, **kwargs: receipt)
    monkeypatch.setattr(
        LAUNCHER,
        "_deepagents_completion_snapshot",
        lambda *args, **kwargs: snapshots.append("pane") or pytest.fail("receipt must bypass pane"),
    )

    evidence = LAUNCHER._deepagents_completion_evidence(
        "herdr.exe",
        "session",
        "pane",
        env={},
        expected_marker="MARKER",
        receipt_file=tmp_path / "result.json",
        attempt_id="attempt-1",
    )

    assert snapshots == []
    assert evidence["lifecycle_receipt"] == receipt
    assert evidence["receipt_authoritative"] is True


def test_deepagents_completion_reads_receipt_between_pane_polls(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    unknown = {"state": "unknown", "detail": "receipt unavailable"}
    confirmed = {
        "state": "confirmed",
        "worker_state": "exited",
        "worker_exit_code": 0,
        "descendant_state": "terminated",
        "cleanup_state": "removed",
        "recovery_required": False,
    }
    receipts = iter([unknown, confirmed])
    snapshots = iter([
        {"state": "running", "report_present": False},
        {"state": "completed", "report_present": True},
    ])
    clock = [0.0]
    sleeps: list[float] = []
    monkeypatch.setattr(LAUNCHER, "_read_deepagents_receipt", lambda *args, **kwargs: next(receipts))
    monkeypatch.setattr(LAUNCHER, "_deepagents_completion_snapshot", lambda *args, **kwargs: next(snapshots))
    monkeypatch.setattr(LAUNCHER.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(
        LAUNCHER.time,
        "sleep",
        lambda seconds: (sleeps.append(seconds), clock.__setitem__(0, clock[0] + seconds)),
    )

    evidence = LAUNCHER._deepagents_completion_evidence(
        "herdr.exe",
        "session",
        "pane",
        env={},
        expected_marker="MARKER",
        receipt_file=tmp_path / "result.json",
        attempt_id="attempt-1",
    )

    assert evidence["lifecycle_receipt"] == confirmed
    assert evidence["state"] == "completed"
    assert evidence["marker_present"] is False
    assert evidence["report_present"] is False
    assert evidence["receipt_authoritative"] is True
    assert sleeps == [1.0]


def test_deepagents_completion_returns_uncertain_receipt_at_deadline(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    clock = [0.0]
    monkeypatch.setattr(LAUNCHER, "_DEEPAGENTS_COMPLETION_WAIT_SECONDS", 0.5)
    monkeypatch.setattr(
        LAUNCHER,
        "_read_deepagents_receipt",
        lambda *args, **kwargs: {"state": "unknown", "detail": "receipt unavailable"},
    )
    monkeypatch.setattr(
        LAUNCHER,
        "_deepagents_completion_snapshot",
        lambda *args, **kwargs: {"state": "completed", "report_present": True},
    )
    monkeypatch.setattr(LAUNCHER.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(
        LAUNCHER.time,
        "sleep",
        lambda seconds: clock.__setitem__(0, clock[0] + seconds),
    )

    evidence = LAUNCHER._deepagents_completion_evidence(
        "herdr.exe",
        "session",
        "pane",
        env={},
        expected_marker="MARKER",
        receipt_file=tmp_path / "result.json",
        attempt_id="attempt-1",
    )

    assert evidence["state"] == "completed"
    assert evidence["lifecycle_receipt"]["state"] == "unknown"


def test_deepagents_completion_recovers_receipt_after_observation_deadline(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    unknown = {"state": "unknown", "detail": "receipt unavailable"}
    confirmed = {
        "state": "confirmed",
        "worker_state": "exited",
        "worker_exit_code": 0,
        "descendant_state": "terminated",
        "cleanup_state": "removed",
        "role_views_state": "removed",
        "recovery_required": False,
    }
    receipts = iter([unknown, unknown, confirmed])
    snapshots = iter([
        {"state": "running", "report_present": False, "observation_error": None},
        {
            "state": "no-report",
            "report_present": False,
            "observation_error": "observation deadline exceeded",
        },
        {"state": "completed", "report_present": True, "observation_error": None},
    ])
    clock = [0.0]
    deadlines: list[float | None] = []
    monkeypatch.setattr(LAUNCHER, "_DEEPAGENTS_COMPLETION_WAIT_SECONDS", 0.5)
    monkeypatch.setattr(
        LAUNCHER,
        "_DEEPAGENTS_RECEIPT_GRACE_SECONDS",
        0.5,
        raising=False,
    )
    monkeypatch.setattr(
        LAUNCHER,
        "_read_deepagents_receipt",
        lambda *args, **kwargs: next(receipts),
    )

    def snapshot(*args: object, **kwargs: object) -> dict[str, object]:
        deadlines.append(kwargs.get("deadline"))
        return next(snapshots)

    monkeypatch.setattr(LAUNCHER, "_deepagents_completion_snapshot", snapshot)
    monkeypatch.setattr(LAUNCHER.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(
        LAUNCHER.time,
        "sleep",
        lambda seconds: clock.__setitem__(0, clock[0] + seconds),
    )

    evidence = LAUNCHER._deepagents_completion_evidence(
        "herdr.exe",
        "session",
        "pane",
        env={},
        expected_marker="MARKER",
        receipt_file=tmp_path / "result.json",
        attempt_id="attempt-1",
    )

    assert evidence["state"] == "completed"
    assert evidence["lifecycle_receipt"] == confirmed
    assert len(deadlines) == 2
    assert deadlines[-1] == 0.5
    assert all(deadline is not None for deadline in deadlines)


def test_deepagents_completion_deadline_receipt_does_not_read_pane_after_confirmation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    clock = [0.0]
    receipt_calls = 0
    snapshot_calls = 0
    confirmed = _confirmed_success_receipt()

    def read_receipt(*args: object, **kwargs: object) -> dict[str, object]:
        nonlocal receipt_calls
        receipt_calls += 1
        return {"state": "unknown", "detail": "receipt unavailable"} if receipt_calls == 1 else confirmed

    def snapshot(*args: object, **kwargs: object) -> dict[str, object]:
        nonlocal snapshot_calls
        snapshot_calls += 1
        return {"state": "no-report", "report_present": False, "observation_error": "deadline"}

    monkeypatch.setattr(LAUNCHER, "_DEEPAGENTS_COMPLETION_WAIT_SECONDS", 0.0)
    monkeypatch.setattr(LAUNCHER, "_DEEPAGENTS_RECEIPT_GRACE_SECONDS", 1.0)
    monkeypatch.setattr(LAUNCHER, "_DEEPAGENTS_RECEIPT_POLL_SECONDS", 0.25)
    monkeypatch.setattr(LAUNCHER, "_read_deepagents_receipt", read_receipt)
    monkeypatch.setattr(LAUNCHER, "_deepagents_completion_snapshot", snapshot)
    monkeypatch.setattr(LAUNCHER.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(
        LAUNCHER.time,
        "sleep",
        lambda seconds: clock.__setitem__(0, clock[0] + seconds),
    )

    evidence = LAUNCHER._deepagents_completion_evidence(
        "herdr.exe",
        "session",
        "pane",
        env={},
        expected_marker="MARKER",
        receipt_file=tmp_path / "result.json",
        attempt_id="attempt-1",
    )

    assert snapshot_calls == 1
    assert evidence["receipt_authoritative"] is True
    assert evidence["report_present"] is False
    assert evidence["diagnostic_observation"]["state"] == "no-report"


def test_deepagents_classification_keeps_missing_managed_task_result_unverified() -> None:
    result = LAUNCHER._classify_deepagents_outcome(
        delivery={"state": "delivered"},
        observation={
            "state": "completed",
            "report_present": True,
            "observation_error": None,
        },
        receipt=_confirmed_success_receipt(),
        fallback_failure_kind=None,
    )

    assert result["task_result"]["state"] == "unverified"
    assert result["status"] == "completed"
    assert result["failure_kind"] == "task_result_unverified"
    assert result["launcher_exit_code"] == 2
    assert result["reconciliation_required"] is True


def test_deepagents_completion_waits_for_slow_cleanup_receipt(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    unknown = {"state": "unknown", "detail": "receipt unavailable"}
    confirmed = {
        "state": "confirmed",
        "worker_state": "exited",
        "worker_exit_code": 0,
        "descendant_state": "terminated",
        "cleanup_state": "removed",
        "role_views_state": "removed",
        "recovery_required": False,
    }
    receipts = iter([unknown, *([unknown] * 5), confirmed])
    snapshots = iter([
        {"state": "completed", "report_present": True},
        {"state": "completed", "report_present": True},
    ])
    clock = [0.0]
    monkeypatch.setattr(LAUNCHER, "_DEEPAGENTS_RECEIPT_POLL_SECONDS", 1.0)
    monkeypatch.setattr(
        LAUNCHER,
        "_read_deepagents_receipt",
        lambda *args, **kwargs: next(receipts),
    )
    monkeypatch.setattr(
        LAUNCHER,
        "_deepagents_completion_snapshot",
        lambda *args, **kwargs: next(snapshots),
    )
    monkeypatch.setattr(LAUNCHER.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(
        LAUNCHER.time,
        "sleep",
        lambda seconds: clock.__setitem__(0, clock[0] + seconds),
    )

    evidence = LAUNCHER._deepagents_completion_evidence(
        "herdr.exe",
        "session",
        "pane",
        env={},
        expected_marker="MARKER",
        receipt_file=tmp_path / "result.json",
        attempt_id="attempt-1",
    )

    assert evidence["state"] == "completed"
    assert evidence["lifecycle_receipt"] == confirmed


def test_deepagents_snapshot_does_not_start_second_pane_command_after_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = [0.0]
    calls: list[list[str]] = []

    def run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        clock[0] = 1.0
        return subprocess.CompletedProcess(command, 0, json.dumps({"result": {"process_info": {"foreground_processes": []}}}), "")

    monkeypatch.setattr(LAUNCHER, "_run", run)
    monkeypatch.setattr(LAUNCHER.time, "monotonic", lambda: clock[0])

    evidence = LAUNCHER._deepagents_completion_snapshot(
        "herdr.exe",
        "session",
        "pane",
        env={},
        expected_marker="MARKER",
        deadline=0.5,
    )

    assert len(calls) == 1
    assert evidence["observation_error"] == "observation deadline exceeded"


def test_deepagents_completion_deadline_preserves_last_state_as_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(LAUNCHER, "_DEEPAGENTS_COMPLETION_WAIT_SECONDS", 0)
    monkeypatch.setattr(
        LAUNCHER,
        "_deepagents_completion_snapshot",
        lambda *args, **kwargs: {"state": "running", "observation_error": None},
    )
    monkeypatch.setattr(LAUNCHER.time, "monotonic", lambda: 0.0)

    evidence = LAUNCHER._deepagents_completion_evidence(
        "herdr.exe",
        "session",
        "pane",
        env={},
        expected_marker="PROBE_OK",
    )

    assert evidence["state"] == "timed_out"
    assert evidence["last_observed_state"] == "running"
    assert evidence["observation_deadline_exceeded"] is True


def test_deepagents_snapshot_captures_gated_pane_wait_output_command_duplicate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[str]] = []

    def run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        if "wait-output" in command:
            return subprocess.CompletedProcess(
                command,
                0,
                json.dumps({"result": "COMPLETED\nMARKER"}),
                "",
            )
        if "process-info" in command:
            return subprocess.CompletedProcess(
                command,
                0,
                json.dumps({"result": {"process_info": {"foreground_processes": []}}}),
                "",
            )
        return subprocess.CompletedProcess(
            command,
            0,
            json.dumps({"result": "COMPLETED\nMARKER"}),
            "",
        )

    monkeypatch.setattr(LAUNCHER, "_run", run)
    evidence = LAUNCHER._deepagents_completion_snapshot(
        "herdr.exe",
        "session",
        "pane",
        env={},
        expected_marker="MARKER",
        deadline=LAUNCHER.time.monotonic() + 5,
    )

    wait_calls = [command for command in calls if "wait-output" in command]
    assert wait_calls
    wait_command = wait_calls[0]
    assert wait_command[:4] == ["herdr.exe", "--session", "session", "pane"]
    assert "wait-output" in wait_command
    assert "--match" in wait_command or "--regex" in wait_command
    assert any("MARKER" in part for part in wait_command)
    assert "--timeout" in wait_command
    assert evidence["state"] == "completed"


def test_deepagents_snapshot_bounds_native_wait_timeout_duplicate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[list[str], object]] = []

    def run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append((command, kwargs.get("timeout")))
        if "wait-output" in command:
            raise LAUNCHER.CommandTransportTimeout("wait timeout")
        return subprocess.CompletedProcess(command, 0, json.dumps({"result": {"process_info": {"foreground_processes": []}}}), "") if "process-info" in command else subprocess.CompletedProcess(command, 0, json.dumps({"result": ""}), "")

    monkeypatch.setattr(LAUNCHER, "_run", run)
    evidence = LAUNCHER._deepagents_completion_snapshot(
        "herdr.exe",
        "session",
        "pane",
        env={},
        expected_marker="MARKER",
        deadline=LAUNCHER.time.monotonic() + 0.01,
    )

    wait_call = next(item for item in calls if "wait-output" in item[0])
    assert float(wait_call[1]) <= LAUNCHER._HERDR_COMMAND_TIMEOUT
    assert evidence["state"] != "completed"


def test_deepagents_snapshot_falls_back_to_pull_probe_after_wait_failure_duplicate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[str]] = []

    def run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        if "wait-output" in command:
            return subprocess.CompletedProcess(command, 1, "", "unsupported")
        if "process-info" in command:
            return subprocess.CompletedProcess(
                command,
                0,
                json.dumps({"result": {"process_info": {"foreground_processes": []}}}),
                "",
            )
        return subprocess.CompletedProcess(
            command,
            0,
            json.dumps({"result": "COMPLETED\nMARKER"}),
            "",
        )

    monkeypatch.setattr(LAUNCHER, "_run", run)
    evidence = LAUNCHER._deepagents_completion_snapshot(
        "herdr.exe",
        "session",
        "pane",
        env={},
        expected_marker="MARKER",
    )

    assert any("wait-output" in command for command in calls)
    assert any("pane" in command and "read" in command for command in calls)
    assert evidence["state"] == "completed"


def test_deepagents_task_state_rejects_stale_marker_output() -> None:
    evidence = LAUNCHER._deepagents_task_state(
        [],
        "Running task non-interactively...\nCOMPLETED\nOLD_MARKER",
        "MARKER",
    )

    assert evidence == "no-report"


def test_deepagents_snapshot_does_not_report_stale_marker_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        if "process-info" in command:
            return subprocess.CompletedProcess(command, 0, json.dumps({"result": {"process_info": {"foreground_processes": []}}}), "")
        return subprocess.CompletedProcess(command, 0, json.dumps({"result": "Running task non-interactively...\nCOMPLETED\nOLD_MARKER"}), "")

    monkeypatch.setattr(LAUNCHER, "_run", run)
    evidence = LAUNCHER._deepagents_completion_snapshot("herdr.exe", "session", "pane", env={}, expected_marker="MARKER")

    assert evidence["marker_present"] is False


def test_deepagents_confirmed_receipt_skips_blocking_marker_wait(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    confirmed = {
        "state": "confirmed",
        "worker_state": "exited",
        "worker_exit_code": 0,
        "descendant_state": "terminated",
        "cleanup_state": "removed",
        "role_views_state": "removed",
        "recovery_required": False,
    }
    calls: list[list[str]] = []

    def run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        if "process-info" in command:
            return subprocess.CompletedProcess(command, 0, json.dumps({"result": {"process_info": {"foreground_processes": []}}}), "")
        return subprocess.CompletedProcess(command, 0, json.dumps({"result": "Running task...\nCOMPLETED\nMARKER"}), "")

    monkeypatch.setattr(LAUNCHER, "_run", run)
    monkeypatch.setattr(LAUNCHER, "_read_deepagents_receipt", lambda *args, **kwargs: confirmed)
    evidence = LAUNCHER._deepagents_completion_evidence(
        "herdr.exe", "session", "pane", env={}, expected_marker="MARKER",
        receipt_file=tmp_path / "result.json", attempt_id="attempt-1",
    )

    assert evidence["lifecycle_receipt"] == confirmed
    assert not any("wait-output" in command for command in calls)


def test_deepagents_snapshot_reserves_deadline_for_final_probe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[list[str], float | None]] = []

    def run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append((command, kwargs.get("timeout")))
        if "process-info" in command:
            return subprocess.CompletedProcess(command, 0, json.dumps({"result": {"process_info": {"foreground_processes": []}}}), "")
        return subprocess.CompletedProcess(command, 1, "", "interval expired")

    monkeypatch.setattr(LAUNCHER, "_run", run)
    LAUNCHER._deepagents_completion_snapshot(
        "herdr.exe", "session", "pane", env={}, expected_marker="MARKER",
        deadline=LAUNCHER.time.monotonic() + 2,
    )

    wait_call = next(item for item in calls if "wait-output" in item[0])
    read_call = next(item for item in calls if "read" in item[0])
    assert float(wait_call[1]) < float(read_call[1])


def test_deepagents_completion_memoizes_current_attempt_marker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshots = iter([
        {"state": "running", "marker_present": True, "report_present": False, "marker_wait_state": "observed"},
        {"state": "completed", "marker_present": False, "report_present": True, "marker_wait_state": "skipped"},
    ])
    marker_observed: list[object] = []

    def snapshot(*args: object, **kwargs: object) -> dict[str, object]:
        marker_observed.append(kwargs.get("marker_observed"))
        return next(snapshots)

    monkeypatch.setattr(LAUNCHER, "_deepagents_completion_snapshot", snapshot)
    monkeypatch.setattr(
        LAUNCHER,
        "_read_deepagents_receipt",
        lambda *args, **kwargs: {"state": "unknown", "detail": "receipt unavailable"},
    )
    monkeypatch.setattr(LAUNCHER.time, "monotonic", lambda: 0.0)
    monkeypatch.setattr(LAUNCHER.time, "sleep", lambda seconds: None)

    evidence = LAUNCHER._deepagents_completion_evidence(
        "herdr.exe", "session", "pane", env={}, expected_marker="MARKER"
    )

    assert marker_observed[:2] == [False, True]
    assert evidence["state"] == "completed"


def test_deepagents_completion_settles_after_pane_run_with_delayed_receipt(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    unknown = {"state": "unknown", "detail": "receipt unavailable"}
    confirmed = {
        "state": "confirmed",
        "worker_state": "exited",
        "worker_exit_code": 0,
        "descendant_state": "terminated",
        "cleanup_state": "removed",
        "role_views_state": "removed",
        "recovery_required": False,
    }
    receipts = iter([unknown, unknown, confirmed])
    snapshots = iter([
        {"state": "completed", "report_present": True},
        {"state": "completed", "report_present": True},
    ])
    clock = [0.0]
    monkeypatch.setattr(LAUNCHER, "_DEEPAGENTS_RECEIPT_POLL_SECONDS", 0.1)
    monkeypatch.setattr(LAUNCHER, "_DEEPAGENTS_RECEIPT_GRACE_SECONDS", 1.0)
    monkeypatch.setattr(LAUNCHER, "_DEEPAGENTS_COMPLETION_WAIT_SECONDS", 1.0)
    monkeypatch.setattr(LAUNCHER, "_read_deepagents_receipt", lambda *args, **kwargs: next(receipts))
    monkeypatch.setattr(LAUNCHER, "_deepagents_completion_snapshot", lambda *args, **kwargs: next(snapshots))
    monkeypatch.setattr(LAUNCHER.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(LAUNCHER.time, "sleep", lambda seconds: clock.__setitem__(0, clock[0] + seconds))

    evidence = LAUNCHER._deepagents_completion_evidence(
        "herdr.exe",
        "session",
        "pane",
        env={},
        expected_marker="MARKER",
        receipt_file=tmp_path / "result.json",
        attempt_id="attempt-1",
    )

    assert evidence["state"] == "completed"
    assert evidence["lifecycle_receipt"] == confirmed


def test_deepagents_completion_settles_after_late_receipt_snapshot(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    unknown = {"state": "unknown", "detail": "receipt unavailable"}
    confirmed = {
        "state": "confirmed",
        "worker_state": "exited",
        "worker_exit_code": 0,
        "descendant_state": "terminated",
        "cleanup_state": "removed",
        "role_views_state": "removed",
        "recovery_required": False,
    }
    receipts = iter([unknown, confirmed])
    snapshots = iter([
        {"state": "no-report", "marker_present": False, "report_present": False},
    ])
    clock = [0.0]
    monkeypatch.setattr(LAUNCHER, "_DEEPAGENTS_COMPLETION_WAIT_SECONDS", 1.0)
    monkeypatch.setattr(LAUNCHER, "_DEEPAGENTS_RECEIPT_GRACE_SECONDS", 2.0)
    monkeypatch.setattr(LAUNCHER, "_DEEPAGENTS_RECEIPT_POLL_SECONDS", 0.1)
    monkeypatch.setattr(LAUNCHER, "_read_deepagents_receipt", lambda *args, **kwargs: next(receipts))
    monkeypatch.setattr(LAUNCHER, "_deepagents_completion_snapshot", lambda *args, **kwargs: next(snapshots))
    monkeypatch.setattr(LAUNCHER.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(
        LAUNCHER.time,
        "sleep",
        lambda seconds: clock.__setitem__(0, clock[0] + seconds),
    )

    evidence = LAUNCHER._deepagents_completion_evidence(
        "herdr.exe",
        "session",
        "pane",
        env={},
        expected_marker="MARKER",
        receipt_file=tmp_path / "result.json",
        attempt_id="attempt-1",
    )

    assert evidence["state"] == "completed"
    assert evidence["marker_present"] is False
    assert evidence["lifecycle_receipt"] == confirmed
    assert evidence["receipt_authoritative"] is True


def test_profiles_share_launch_shape(tmp_path: Path) -> None:
    fake_profile(tmp_path, "normal", 20)
    fake_profile(tmp_path, "ui", None)
    profiles = LAUNCHER.load_agent_profiles(tmp_path / "agents")

    shapes = {
        tuple(LAUNCHER._redacted_arguments(LAUNCHER._codex_arguments(profile, tmp_path)))
        for profile in profiles.values()
    }

    assert len(shapes) == 2
    assert all(shape[:2] == ("-C", str(tmp_path)) for shape in shapes)


def test_missing_executable_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(LAUNCHER.shutil, "which", lambda name: None)

    with pytest.raises(LAUNCHER.LaunchBlocked, match="herdr"):
        LAUNCHER._executable("herdr")


def test_managed_deepagents_executable_uses_setup_owned_path(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(LAUNCHER, "_managed_deepagents_executable", _MANAGED_DEEPAGENTS_RESOLVER)
    managed = tmp_path / ".local" / "bin" / (
        "dcode-project.cmd" if LAUNCHER.os.name == "nt" else "dcode-project"
    )
    managed.parent.mkdir(parents=True)
    managed.write_text("wrapper", encoding="utf-8")
    monkeypatch.setattr(LAUNCHER.Path, "home", lambda: tmp_path)
    monkeypatch.setenv("PATH", str(tmp_path / "unmanaged"))

    assert LAUNCHER._managed_deepagents_executable() == str(managed.resolve())


def test_managed_deepagents_executable_fails_without_setup_owned_wrapper(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(LAUNCHER, "_managed_deepagents_executable", _MANAGED_DEEPAGENTS_RESOLVER)
    monkeypatch.setattr(LAUNCHER.Path, "home", lambda: tmp_path)
    unmanaged = tmp_path / "unmanaged"
    unmanaged.mkdir()
    (unmanaged / ("dcode-project.cmd" if LAUNCHER.os.name == "nt" else "dcode-project")).write_text(
        "unmanaged", encoding="utf-8"
    )
    monkeypatch.setenv("PATH", str(unmanaged))

    with pytest.raises(LAUNCHER.LaunchBlocked, match="setup_deepagents_runtime"):
        LAUNCHER._managed_deepagents_executable()


def test_pane_safety_rejects_existing_agent(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    payload = {"result": {"panes": [{"pane_id": "p1", "cwd": str(tmp_path), "agent": "codex"}]}}
    monkeypatch.setattr(LAUNCHER, "_json_command", lambda command, **kwargs: payload)

    with pytest.raises(LAUNCHER.LaunchBlocked, match="already has agent"):
        LAUNCHER._herdr_pane(tmp_path, "session", "p1", "herdr")


def test_pane_safety_rejects_missing_process_evidence(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    responses = iter([
        {"result": {"panes": [{"pane_id": "p1", "cwd": str(tmp_path)}]}},
        {"result": {"process_info": {}}},
    ])
    monkeypatch.setattr(LAUNCHER, "_json_command", lambda command, **kwargs: next(responses))

    with pytest.raises(LAUNCHER.LaunchBlocked, match="incomplete"):
        LAUNCHER._herdr_pane(tmp_path, "session", "p1", "herdr")


def test_pane_safety_rejects_nested_non_shell_descendant(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    responses = iter([
        {"result": {"panes": [{"pane_id": "p1", "cwd": str(tmp_path)}]}},
        {"result": {"process_info": {"foreground_processes": [
            {"pid": 1, "name": "powershell.exe", "children": [
                {"pid": 2, "name": "cmd.exe", "children": [
                    {"pid": 3, "name": "python.exe", "children": []},
                ]},
            ]},
        ]}}},
    ])
    monkeypatch.setattr(LAUNCHER, "_json_command", lambda command, **kwargs: next(responses))

    with pytest.raises(LAUNCHER.TargetCandidateRejected, match="python.exe"):
        LAUNCHER._herdr_pane(tmp_path, "session", "p1", "herdr")


def test_pane_safety_accepts_nested_shell_only_tree(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    process_info = {"foreground_processes": [
        {"pid": 1, "name": "powershell.exe", "children": [
            {"pid": 2, "name": "cmd.exe", "children": []},
        ]},
    ]}
    responses = iter([
        {"result": {"panes": [{"pane_id": "p1", "cwd": str(tmp_path)}]}},
        {"result": {"process_info": process_info}},
    ])
    monkeypatch.setattr(LAUNCHER, "_json_command", lambda command, **kwargs: next(responses))

    assert LAUNCHER._herdr_pane(tmp_path, "session", "p1", "herdr")["process_info"] == process_info


def test_confirm_codex_start_rejects_unrelated_new_process(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    responses = iter([
        {"result": {"agent": {"agent_status": "working"}}},
        {"result": {"process_info": {"foreground_processes": [
            {"pid": 2, "name": "python.exe", "argv0": "python.exe", "cwd": str(tmp_path), "children": []},
        ]}}},
    ])
    monkeypatch.setattr(LAUNCHER, "_json_command", lambda command, **kwargs: next(responses))

    with pytest.raises(LAUNCHER.LaunchBlocked, match="ownership"):
        LAUNCHER._confirm_codex_start(
            "herdr.exe", "session", "p1", "agent", env={}, before_process_ids={1},
            expected_codex_executable="C:/bin/codex.exe", expected_cwd=tmp_path,
        )


def test_confirm_codex_start_accepts_matching_process_identity(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    responses = iter([
        {"result": {"agent": {"agent_status": "working"}}},
        {"result": {"process_info": {"foreground_processes": [
            {"pid": 2, "name": "codex.exe", "argv0": "C:/bin/codex.exe", "cwd": str(tmp_path), "children": []},
        ]}}},
    ])
    monkeypatch.setattr(LAUNCHER, "_json_command", lambda command, **kwargs: next(responses))

    result = LAUNCHER._confirm_codex_start(
        "herdr.exe", "session", "p1", "agent", env={}, before_process_ids={1},
        expected_codex_executable="C:/bin/codex.exe", expected_cwd=tmp_path,
    )

    assert result["process_ids"] == [2]


def test_deepagents_pane_requires_powershell_shell(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    responses = iter([
        {"result": {"panes": [{"pane_id": "p1", "cwd": str(tmp_path)}]}},
        {"result": {"process_info": {"foreground_processes": [{"name": "cmd.exe"}]}}},
    ])
    monkeypatch.setattr(LAUNCHER, "_json_command", lambda command, **kwargs: next(responses))

    with pytest.raises(LAUNCHER.LaunchBlocked, match="cmd.exe"):
        LAUNCHER._herdr_pane(
            tmp_path,
            "session",
            "p1",
            "herdr",
            executor="deepagents",
        )


def test_resolve_launch_rechecks_selected_target_before_launch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile = LAUNCHER.AgentProfile(
        Path("normal.toml"), "normal", "9router", "combo-normal", 20, "test", "test",
    )
    monkeypatch.setattr(LAUNCHER, "_profile", lambda *args: profile)
    monkeypatch.setattr(LAUNCHER, "_executable", lambda name: f"{name}.exe")
    monkeypatch.setattr(LAUNCHER, "_managed_deepagents_executable", lambda: "dcode-project.exe")
    monkeypatch.setattr(LAUNCHER, "_git_identity", lambda *args: {"head": "head"})
    monkeypatch.setattr(LAUNCHER, "_version", lambda *args, **kwargs: "herdr")
    monkeypatch.setattr(
        LAUNCHER,
        "_resolve_target_selector",
        lambda *args, **kwargs: ("session", "pane", {"status": "selected"}),
    )
    monkeypatch.setattr(
        LAUNCHER,
        "_herdr_pane",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            LAUNCHER.TargetCandidateRejected("Pane already has agent state: pane")
        ),
    )

    with pytest.raises(LAUNCHER.TargetCandidateRejected, match="already has agent state"):
        LAUNCHER.resolve_launch(
            profile_name="normal",
            session="auto",
            pane="auto",
            cwd=ROOT,
            expected_base="HEAD",
            executor="deepagents",
            task="assign lane",
        )


def test_git_identity_rejects_non_root_cwd(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    values = iter([str(tmp_path), str(tmp_path / ".git"), "main", "head", "base"])
    monkeypatch.setattr(LAUNCHER, "_git_value", lambda cwd, *args: next(values))

    with pytest.raises(LAUNCHER.LaunchBlocked, match="exact Git worktree root"):
        LAUNCHER._git_identity(tmp_path / "subdir", "base")


def test_main_dry_run_emits_json_and_does_not_start(monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    evidence = {"registry_launcher": {"profile": "xhigh"}}
    monkeypatch.setattr(LAUNCHER, "resolve_launch", lambda **kwargs: (["herdr"], evidence))
    run = monkeypatch.setattr(LAUNCHER, "_run", lambda command: (_ for _ in ()).throw(AssertionError()))

    assert LAUNCHER.main(
        [
            "--profile",
            "xhigh",
            "--session",
            "codex-probe",
            "--pane",
            "w1:p5",
            "--cwd",
            str(ROOT),
            "--expected-base",
            "HEAD",
            "--task",
            "dry run",
            "--dry-run",
        ]
    ) == 0
    assert json.loads(capsys.readouterr().out) == evidence


def test_terminate_codex_lane_blocks_empty_preclose_process_info(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[str]] = []

    def fake_run(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(
            command,
            0,
            json.dumps({"result": {"process_info": {"foreground_processes": []}}}),
            "",
        )

    monkeypatch.setattr(LAUNCHER, "_run", fake_run)

    result = LAUNCHER._terminate_codex_lane(
        "herdr.exe",
        "session",
        "pane",
        env={},
    )

    assert result["verified"] is False
    assert "empty process information" in result["detail"]
    assert len(calls) == 1


def test_terminate_codex_lane_checks_recorded_processes_after_pane_close(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    process_info = {
        "result": {
            "process_info": {
                "foreground_processes": [
                    {
                        "pid": 101,
                        "name": "codex.exe",
                        "children": [{"pid": 102, "name": "node.exe"}],
                    }
                ]
            }
        }
    }
    commands: list[list[str]] = []

    def fake_run(command, **kwargs):
        commands.append(command)
        if "process-info" in command:
            return subprocess.CompletedProcess(command, 0, json.dumps(process_info), "")
        if "close" in command:
            return subprocess.CompletedProcess(command, 0, "", "")
        return subprocess.CompletedProcess(command, 0, json.dumps({"result": {"panes": []}}), "")

    monkeypatch.setattr(LAUNCHER, "_run", fake_run)
    monkeypatch.setattr(LAUNCHER, "_process_ids_alive", lambda process_ids: {102})

    result = LAUNCHER._terminate_codex_lane(
        "herdr.exe",
        "session",
        "pane",
        env={},
    )

    assert result["verified"] is False
    assert result["state"] == "processes-remain"
    assert result["remaining_process_ids"] == [102]
    assert len(commands) == 3


def test_terminate_codex_lane_detects_new_nested_non_shell_process(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    process_infos = iter([
        {"foreground_processes": [
            {"pid": 101, "name": "codex.exe", "children": []},
        ]},
        {"foreground_processes": [
            {"pid": 201, "name": "powershell.exe", "children": [
                {"pid": 202, "name": "node.exe", "children": []},
            ]},
        ]},
    ])

    def fake_run(command, **kwargs):
        if "process-info" in command:
            return subprocess.CompletedProcess(
                command, 0, json.dumps({"result": {"process_info": next(process_infos)}}), "",
            )
        if "close" in command:
            return subprocess.CompletedProcess(command, 0, "", "")
        return subprocess.CompletedProcess(command, 0, json.dumps({"result": {"panes": [{"pane_id": "pane"}]}}), "")

    monkeypatch.setattr(LAUNCHER, "_run", fake_run)
    monkeypatch.setattr(LAUNCHER, "_process_ids_alive", lambda process_ids: set())

    result = LAUNCHER._terminate_codex_lane("herdr.exe", "session", "pane", env={})

    assert result["verified"] is False
    assert result["state"] == "processes-remain"
    assert result["remaining_processes"] == ["node.exe"]


def test_deepagents_marker_with_live_worker_does_not_report_completed() -> None:
    assert LAUNCHER._deepagents_task_state(
        [{"name": "python.exe"}],
        "COMPLETED\nEXPECTED_MARKER\n",
        "EXPECTED_MARKER",
    ) == "running"


def test_assignment_result_builder_keeps_lifecycle_facts_independent() -> None:
    result = LAUNCHER._build_assignment_result(
        dispatch_id="dispatch",
        attempt_id="attempt",
        agent_name="normal-main",
        delivery={"state": "confirmed"},
        execution={"state": "unknown"},
        observation={"state": "timed_out"},
        task_result={"state": "unknown"},
        cleanup={"state": "unknown"},
        performance={"status": "measured"},
        launcher_exit_code=2,
    )

    assert result["assignment"]["dispatch_id"] == "dispatch"
    assert result["assignment"]["attempt_id"] == "attempt"
    assert result["assignment"]["delivery"]["state"] == "confirmed"
    assert result["assignment"]["execution"]["state"] == "unknown"
    assert result["assignment"]["observation"]["state"] == "timed_out"
    assert result["assignment"]["task_result"]["state"] == "unknown"
    assert result["assignment"]["cleanup"]["state"] == "unknown"
    assert result["assignment"]["launcher_exit_code"] == 2
    assert result["assignment"]["worker_exit_code"] is None


def test_assignment_result_builder_derives_compatibility_from_structured_facts() -> None:
    result = LAUNCHER._build_assignment_result(
        dispatch_id="dispatch",
        attempt_id="attempt",
        agent_name="normal-main",
        delivery={"state": "confirmed"},
        execution={"state": "failed", "worker_exit_code": 7},
        observation={"state": "observed"},
        task_result={"state": "reported_failed", "accepted": False},
        cleanup={"state": "removed"},
        performance={"status": "measured"},
        launcher_exit_code=2,
    )

    assignment = result["assignment"]
    assert assignment["status"] == "failed"
    assert assignment["failure_kind"] == "task_report_failed"
    assert assignment["reconciliation_required"] is False


def test_assignment_result_builder_marks_incomplete_structured_facts_for_reconciliation() -> None:
    result = LAUNCHER._build_assignment_result(
        dispatch_id="dispatch",
        attempt_id="attempt",
        agent_name="normal-main",
        delivery={"state": "confirmed"},
        execution={"state": "unknown"},
        observation={"state": "timed_out"},
        task_result={"state": "unverified", "accepted": None},
        cleanup={"state": "unknown"},
        performance={"status": "measured"},
        launcher_exit_code=2,
    )

    assignment = result["assignment"]
    assert assignment["status"] == "unknown"
    assert assignment["reconciliation_required"] is True


def test_performance_snapshot_uses_structured_phase_values() -> None:
    performance = LAUNCHER._new_performance_evidence()

    assert performance["phase_durations_ms"]["delivery"] == {
        "status": "not_attempted",
        "duration_ms": None,
    }
    LAUNCHER._record_performance_phase(performance, "delivery", 0.0, now=0.0124)
    assert performance["phase_durations_ms"]["delivery"] == {
        "status": "measured",
        "duration_ms": 12.4,
    }
    LAUNCHER._record_performance_phase(performance, "delivery", 0.02, now=0.025)
    assert performance["phase_occurrences"]["delivery"] == [
        {"status": "measured", "duration_ms": 12.4, "attempt_id": None},
        {"status": "measured", "duration_ms": 5.0, "attempt_id": None},
    ]
    assert performance["phase_aggregates"]["delivery"] == {
        "status": "measured",
        "duration_ms": 17.4,
        "occurrence_count": 2,
    }


def test_performance_finalization_keeps_trailing_work_unattributed() -> None:
    performance = LAUNCHER._new_performance_evidence()
    LAUNCHER._record_performance_phase(performance, "preflight", 0.0, now=1.0)

    LAUNCHER._finalize_performance(performance, 0.0, now=1.5)

    assert performance["total_duration_ms"] == 1500.0
    assert performance["unattributed_duration_ms"] == 500.0


def test_performance_attempts_and_phases_keep_retry_attribution() -> None:
    performance = LAUNCHER._new_performance_evidence()

    LAUNCHER._record_performance_phase(
        performance, "delivery", 1.0, now=1.2, attempt_id="attempt-1"
    )
    LAUNCHER._record_performance_phase(
        performance, "delivery", 2.0, now=2.4, attempt_id="attempt-2"
    )
    LAUNCHER._record_performance_attempt(performance, "attempt-1", 1.0, now=1.3)
    LAUNCHER._record_performance_attempt(performance, "attempt-2", 2.0, now=2.5)

    assert [item["attempt_id"] for item in performance["phase_occurrences"]["delivery"]] == [
        "attempt-1",
        "attempt-2",
    ]
    assert [item["attempt_id"] for item in performance["attempts"]] == [
        "attempt-1",
        "attempt-2",
    ]


def test_performance_finalization_samples_current_clock_and_unions_overlaps() -> None:
    performance = LAUNCHER._new_performance_evidence()
    LAUNCHER._record_performance_phase(performance, "preflight", 0.0, now=2.0)
    LAUNCHER._record_performance_phase(performance, "target_discovery", 1.0, now=3.0)

    LAUNCHER._finalize_performance(performance, 0.0, now=4.0)

    assert performance["total_duration_ms"] == 4000.0
    assert performance["unattributed_duration_ms"] == 1000.0


def test_deepagents_snapshot_captures_gated_pane_wait_output_command(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[str]] = []

    def run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        if "wait-output" in command:
            return subprocess.CompletedProcess(
                command, 0, json.dumps({"result": "COMPLETED\nMARKER"}), ""
            )
        if "process-info" in command:
            return subprocess.CompletedProcess(
                command,
                0,
                json.dumps({"result": {"process_info": {"foreground_processes": []}}}),
                "",
            )
        return subprocess.CompletedProcess(
            command, 0, json.dumps({"result": "COMPLETED\nMARKER"}), ""
        )

    monkeypatch.setattr(LAUNCHER, "_run", run)
    evidence = LAUNCHER._deepagents_completion_snapshot(
        "herdr.exe",
        "session",
        "pane",
        env={},
        expected_marker="MARKER",
        deadline=LAUNCHER.time.monotonic() + 5,
    )

    wait_command = next(command for command in calls if "wait-output" in command)
    assert wait_command[:4] == ["herdr.exe", "--session", "session", "pane"]
    assert "--regex" in wait_command
    assert r"(?m)^MARKER$" in wait_command
    assert "--timeout" in wait_command
    assert evidence["state"] == "completed"


def test_deepagents_snapshot_bounds_native_wait_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[list[str], object]] = []

    def run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append((command, kwargs.get("timeout")))
        if "wait-output" in command:
            raise LAUNCHER.CommandTransportTimeout("wait timeout")
        if "process-info" in command:
            return subprocess.CompletedProcess(
                command,
                0,
                json.dumps({"result": {"process_info": {"foreground_processes": []}}}),
                "",
            )
        return subprocess.CompletedProcess(command, 0, json.dumps({"result": ""}), "")

    monkeypatch.setattr(LAUNCHER, "_run", run)
    evidence = LAUNCHER._deepagents_completion_snapshot(
        "herdr.exe",
        "session",
        "pane",
        env={},
        expected_marker="MARKER",
        deadline=LAUNCHER.time.monotonic() + 0.01,
    )

    wait_call = next(item for item in calls if "wait-output" in item[0])
    assert float(wait_call[1]) <= LAUNCHER._HERDR_COMMAND_TIMEOUT
    assert evidence["state"] != "completed"


def test_deepagents_snapshot_falls_back_to_pull_probe_after_wait_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[str]] = []

    def run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        if "wait-output" in command:
            return subprocess.CompletedProcess(command, 1, "", "unsupported")
        if "process-info" in command:
            return subprocess.CompletedProcess(
                command,
                0,
                json.dumps({"result": {"process_info": {"foreground_processes": []}}}),
                "",
            )
        return subprocess.CompletedProcess(
            command, 0, json.dumps({"result": "COMPLETED\nMARKER"}), ""
        )

    monkeypatch.setattr(LAUNCHER, "_run", run)
    evidence = LAUNCHER._deepagents_completion_snapshot(
        "herdr.exe", "session", "pane", env={}, expected_marker="MARKER"
    )

    assert any("wait-output" in command for command in calls)
    assert any("read" in command for command in calls)
    assert evidence["state"] == "completed"


def test_deepagents_snapshot_anchors_marker_wait_to_output_line(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[str]] = []

    def run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        if "process-info" in command:
            return subprocess.CompletedProcess(
                command,
                0,
                json.dumps({"result": {"process_info": {"foreground_processes": []}}}),
                "",
            )
        return subprocess.CompletedProcess(
            command,
            0,
            json.dumps({"result": "COMPLETED\nMARKER"}),
            "",
        )

    monkeypatch.setattr(LAUNCHER, "_run", run)
    LAUNCHER._deepagents_completion_snapshot(
        "herdr.exe", "session", "pane", env={}, expected_marker="MARKER"
    )

    wait_command = next(command for command in calls if "wait-output" in command)
    pattern = wait_command[wait_command.index("--regex") + 1]
    assert pattern == r"(?m)^MARKER$"


def test_deepagents_snapshot_rejects_stale_marker_output() -> None:
    assert LAUNCHER._deepagents_task_state(
        [], "Running task non-interactively...\nCOMPLETED\nOLD_MARKER", "MARKER"
    ) == "no-report"


def test_launcher_wait_test_names_are_unique() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    names = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    wait_names = [name for name in names if "wait" in name]
    assert len(wait_names) == len(set(wait_names))


def test_deepagents_main_bounds_native_attempt_and_keeps_acceptance_pending(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    evidence = {
        "registry_launcher": {
            "assignment_task_sha256": LAUNCHER._sha256_text("assign lane"),
            "completion_marker": "EXPECTED_MARKER",
        },
        "herdr": {
            "agent_name": "normal-main",
            "session": "session",
            "pane": "pane",
            "executable": "herdr.exe",
        },
    }
    captured: dict[str, object] = {}
    monkeypatch.setattr(LAUNCHER, "resolve_launch", lambda **kwargs: (["herdr"], evidence))

    def run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        captured.setdefault("worker_timeout", kwargs.get("timeout"))
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(LAUNCHER, "_run", run)
    monkeypatch.setattr(
        LAUNCHER,
        "_read_deepagents_receipt",
        lambda *args, **kwargs: {
            "state": "confirmed",
            "worker_state": "exited",
            "worker_exit_code": 0,
            "descendant_state": "terminated",
            "cleanup_state": "removed",
            "role_views_state": "removed",
            "recovery_required": False,
        },
    )
    monkeypatch.setattr(
        LAUNCHER,
        "_deepagents_completion_evidence",
        lambda *args, **kwargs: captured.update(kwargs) or {
            "state": "completed",
            "marker_present": True,
            "report_present": True,
            "foreground_processes": [],
            "observation_error": None,
        },
    )
    monkeypatch.setattr(
        LAUNCHER,
        "_read_deepagents_task_result",
        lambda *args, **kwargs: _confirmed_task_result(),
    )

    assert LAUNCHER.main(
        [
            "--profile", "normal", "--session", "session", "--pane", "pane",
            "--cwd", str(ROOT), "--expected-base", "HEAD", "--executor", "deepagents",
            "--task", "assign lane",
        ]
    ) == 0

    assert float(captured["worker_timeout"]) <= LAUNCHER._DEEPAGENTS_RUN_TIMEOUT
    assert float(captured["attempt_deadline"]) - LAUNCHER.time.monotonic() <= math.nextafter(
        LAUNCHER._DEEPAGENTS_RUN_TIMEOUT,
        math.inf,
    )
    assert float(captured["completion_wait_seconds"]) <= (
        LAUNCHER._DEEPAGENTS_RUN_TIMEOUT - LAUNCHER._DEEPAGENTS_RECEIPT_GRACE_SECONDS
    )
    assignment = json.loads(capsys.readouterr().out.splitlines()[-1])["assignment"]
    assert assignment["task_result"] == {
        "state": "reported_completed",
        "accepted": None,
        "status": "completed",
    }
    assert assignment["task_accepted"] is None


def test_deepagents_snapshot_orders_marker_wait_before_final_reads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    def run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        if "wait-output" in command:
            calls.append("wait")
            return subprocess.CompletedProcess(command, 0, json.dumps({"result": ""}), "")
        if "process-info" in command:
            calls.append("process")
            return subprocess.CompletedProcess(
                command,
                0,
                json.dumps({"result": {"process_info": {"foreground_processes": []}}}),
                "",
            )
        calls.append("read")
        return subprocess.CompletedProcess(command, 0, json.dumps({"result": "COMPLETED\nMARKER"}), "")

    monkeypatch.setattr(LAUNCHER, "_run", run)

    evidence = LAUNCHER._deepagents_completion_snapshot(
        "herdr.exe",
        "session",
        "pane",
        env={},
        expected_marker="MARKER",
    )

    assert calls == ["wait", "process", "read"]
    assert evidence["state"] == "completed"


def test_deepagents_completion_stops_observing_after_terminal_evidence(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    snapshots: list[dict[str, object]] = []
    confirmed = {
        "state": "confirmed",
        "worker_state": "exited",
        "worker_exit_code": 0,
        "descendant_state": "terminated",
        "cleanup_state": "removed",
        "recovery_required": False,
    }
    monkeypatch.setattr(LAUNCHER, "_read_deepagents_receipt", lambda *args, **kwargs: confirmed)
    def snapshot(*args: object, **kwargs: object) -> dict[str, object]:
        value = {"state": "no-report", "report_present": False}
        snapshots.append(value)
        return value

    monkeypatch.setattr(LAUNCHER, "_deepagents_completion_snapshot", snapshot)
    monkeypatch.setattr(LAUNCHER.time, "sleep", lambda *_: pytest.fail("settlement polled after terminal evidence"))

    evidence = LAUNCHER._deepagents_completion_evidence(
        "herdr.exe",
        "session",
        "pane",
        env={},
        expected_marker="MARKER",
        receipt_file=tmp_path / "result.json",
        attempt_id="attempt-1",
    )

    assert len(snapshots) == 0
    assert evidence["lifecycle_receipt"] == confirmed
    assert evidence["state"] == "completed"
    assert evidence["receipt_authoritative"] is True
