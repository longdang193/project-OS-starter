from __future__ import annotations

import importlib.util
import json
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


def test_codex_arguments_project_complete_contract(tmp_path: Path) -> None:
    fake_profile(tmp_path, "review", None)
    profile = LAUNCHER._profile(tmp_path / "agents", "review")

    arguments = LAUNCHER._codex_arguments(profile, tmp_path)

    assert arguments[:2] == ["-C", str(tmp_path)]
    assert 'model_provider="9router"' in arguments
    assert 'model="combo-review"' in arguments
    assert 'developer_instructions="do not modify files"' in arguments


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
            "--wait",
            "--timeout",
            "30000",
    ]

    bounded = LAUNCHER._codex_assignment_command(
        "herdr.exe", "session", "xhigh-main", "assign lane", timeout_ms=600000,
    )
    assert bounded[-1] == "600000"


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


def test_resolve_launch_builds_deepagents_pane_command(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile = LAUNCHER.AgentProfile(
        Path("normal.toml"),
        "normal",
        "9router",
        "combo-normal",
        20,
        True,
        "test",
        "do not modify files",
    )
    monkeypatch.setattr(LAUNCHER, "_profile", lambda *args: profile)
    monkeypatch.setattr(LAUNCHER, "_executable", lambda name: f"{name}.exe")
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

    assert command == [
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
        "--no-mcp",
        "-n",
        "'Return exactly DEEPAGENTS_ADAPTER_OK [Runtime Grant: delegation.child_agents = deny]'",
    ]

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
        "delivery_task_sha256": LAUNCHER._sha256_text(
            "Return exactly DEEPAGENTS_ADAPTER_OK [Runtime Grant: delegation.child_agents = deny]"
        ),
        "grant_digest": evidence["registry_launcher"]["grant_digest"],
    }
    assert LAUNCHER._DEEPAGENTS_RUN_TIMEOUT == 1800.0


def test_resolve_launch_enables_direct_mcp_only_for_explicit_selection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile = LAUNCHER.AgentProfile(
        Path("normal.toml"),
        "normal",
        "9router",
        "combo-normal",
        20,
        True,
        "test",
        "do not modify files",
    )
    monkeypatch.setattr(LAUNCHER, "_profile", lambda *args: profile)
    monkeypatch.setattr(LAUNCHER, "_executable", lambda name: f"{name}.exe")
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


def test_normalize_runtime_grant_rejects_unsupported_codex_turn_limit() -> None:
    with pytest.raises(LAUNCHER.LaunchBlocked, match="turn budget"):
        LAUNCHER._normalize_runtime_grant(
            executor="codex",
            grant_turns="8",
            grant_wall_clock_seconds="native",
            mcp_select=[],
        )


@pytest.mark.parametrize("child_agents", ["allow", "deny", None])
def test_normalize_runtime_grant_projects_child_agent_authority(child_agents: str | None) -> None:
    grant = LAUNCHER._normalize_runtime_grant(
        executor="codex",
        grant_turns="native",
        grant_wall_clock_seconds="native",
        mcp_select=[],
        grant_child_agents=child_agents,
    )

    assert grant["delegation"]["child_agents"] == (child_agents or "deny")


def test_normalize_runtime_grant_rejects_invalid_child_agent_authority() -> None:
    with pytest.raises(LAUNCHER.LaunchBlocked, match="child_agents"):
        LAUNCHER._normalize_runtime_grant(
            executor="codex",
            grant_turns="native",
            grant_wall_clock_seconds="native",
            mcp_select=[],
            grant_child_agents="maybe",
        )


def test_normalize_runtime_grant_allows_codex_wall_clock_watchdog() -> None:
    grant = LAUNCHER._normalize_runtime_grant(
        executor="codex",
        grant_turns="native",
        grant_wall_clock_seconds="600",
        mcp_select=[],
    )

    assert grant["wall_clock_seconds"] == {
        "requested": 600,
        "effective": 600,
        "enforcement": "outer-watchdog",
    }
    assert grant["outer_watchdog_seconds"] == 600


def test_normalize_runtime_grant_rejects_wall_clock_above_watchdog() -> None:
    with pytest.raises(LAUNCHER.LaunchBlocked, match="1800"):
        LAUNCHER._normalize_runtime_grant(
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
        True,
        "test",
        "do not modify files",
    )
    monkeypatch.setattr(LAUNCHER, "_profile", lambda *args: profile)
    monkeypatch.setattr(LAUNCHER, "_executable", lambda name: f"{name}.exe")
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
    assert command[-1] == "'Return exactly GRANT_OK [Runtime Grant: delegation.child_agents = allow]'"


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
        True,
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
    monkeypatch.setattr(LAUNCHER, "_git_identity", lambda *args: {"head": "head"})
    monkeypatch.setattr(
        LAUNCHER,
        "_herdr_pane",
        lambda cwd, session, pane, herdr, **kwargs: {
            "pane": {"cwd": str(cwd)},
            "process_info": {"foreground_processes": []},
        },
    )

    _, evidence = LAUNCHER.resolve_launch(
        profile_name="normal",
        session="codex-probe",
        pane="w1:p1",
        cwd=ROOT,
        expected_base="HEAD",
        executor="codex",
        grant_child_agents="allow",
        task="original task",
    )

    delivery_task = "original task [Runtime Grant: delegation.child_agents = allow]"
    prompt_argv = evidence["assignment_request"]["redacted_prompt_argv"]
    assert f"task=<sha256:{LAUNCHER._sha256_text(delivery_task)}>" in prompt_argv
    assert evidence["registry_launcher"]["assignment_task_sha256"] == LAUNCHER._sha256_text(
        "original task"
    )
    assert evidence["registry_launcher"]["delivery_task_sha256"] == LAUNCHER._sha256_text(
        delivery_task
    )


def test_resolve_launch_quotes_mcp_selectors_for_powershell(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile = LAUNCHER.AgentProfile(
        Path("normal.toml"),
        "normal",
        "9router",
        "combo-normal",
        20,
        True,
        "test",
        "do not modify files",
    )
    monkeypatch.setattr(LAUNCHER, "_profile", lambda *args: profile)
    monkeypatch.setattr(LAUNCHER, "_executable", lambda name: f"{name}.exe")
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
        True,
        "lead",
        "lead instructions",
    )
    lane_profile = LAUNCHER.AgentProfile(
        lane_root / "agents" / "normal.toml",
        "normal",
        "9router",
        "model-B",
        20,
        True,
        "lane",
        "lane instructions",
    )
    seen_roots: list[Path] = []

    def select_profile(agents_root: Path, name: str) -> LAUNCHER.AgentProfile:
        seen_roots.append(agents_root)
        return lane_profile if agents_root == lane_root / "agents" else lead_profile

    monkeypatch.setattr(LAUNCHER, "_profile", select_profile)
    monkeypatch.setattr(LAUNCHER, "_executable", lambda name: f"{name}.exe")
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


def test_deepagents_rejects_incompatible_profile(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile = LAUNCHER.AgentProfile(
        Path("review.toml"),
        "review",
        "9router",
        "combo-review",
        None,
        False,
        "test",
        "review only",
    )
    monkeypatch.setattr(LAUNCHER, "_profile", lambda *args: profile)

    with pytest.raises(LAUNCHER.LaunchBlocked, match="not compatible"):
        LAUNCHER.resolve_launch(
            profile_name="review",
            session="session",
            pane="pane",
            cwd=ROOT,
            expected_base="HEAD",
            executor="deepagents",
            task="task",
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
    assert commands == [
        ["herdr"],
        [
            "herdr.exe",
            "--session",
            "codex-probe",
            "agent",
            "prompt",
            "xhigh-main",
            "assign lane [Runtime Grant: delegation.child_agents = allow]",
            "--wait",
            "--timeout",
            "30000",
        ],
    ]
    output = capsys.readouterr().out.splitlines()
    assert json.loads(output[-1])["assignment"] == {
        "agent_name": "xhigh-main",
        "delivery_state": "delivered",
        "delivery_certainty": "confirmed",
        "delivery_task_sha256": LAUNCHER._sha256_text(
            "assign lane [Runtime Grant: delegation.child_agents = allow]"
        ),
        "exit_code": 0,
        "failure_kind": None,
        "grant_digest": None,
        "phase": "prompt",
        "prompt_accepted": True,
        "reconciliation_required": False,
        "session": "codex-probe",
        "status": "delivered",
        "task_sha256": LAUNCHER._sha256_text("assign lane"),
        "wait": "settled",
    }


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
    times = iter([0.0, 9.0])
    monkeypatch.setattr(LAUNCHER.time, "monotonic", lambda: next(times))

    assert LAUNCHER.main(
        [
            "--profile", "xhigh", "--session", "auto", "--pane", "auto",
            "--cwd", str(ROOT), "--expected-base", "HEAD", "--task", "assign lane",
            "--grant-wall-clock-seconds", "8",
        ]
    ) == 124
    output = capsys.readouterr().out.splitlines()
    result = json.loads(output[-1])["assignment"]
    assert {key: value for key, value in result.items() if key != "watchdog"} == {
        "agent_name": "xhigh-main",
        "delivery_state": "watchdog_expired",
        "delivery_certainty": "unknown",
        "delivery_task_sha256": LAUNCHER._sha256_text("assign lane"),
        "exit_code": 124,
        "failure_kind": "watchdog_expired",
        "grant_digest": None,
        "phase": "prompt",
        "prompt_accepted": None,
        "reconciliation_required": False,
        "session": "codex-probe",
        "status": "TIMEOUT",
        "task_sha256": LAUNCHER._sha256_text("assign lane"),
    }
    watchdog = result["watchdog"]
    assert watchdog["requested_seconds"] == 8
    assert watchdog["enforcement"] == "outer-watchdog"
    assert watchdog["elapsed_seconds"] >= 0
    assert watchdog["termination"] == cleanup
    assert terminated == [("herdr.exe", "codex-probe", "w1:p5")]


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
    terminated: list[tuple[object, ...]] = []

    monkeypatch.setattr(LAUNCHER, "resolve_launch", lambda **kwargs: (["herdr"], evidence))
    monkeypatch.setattr(LAUNCHER, "_terminate_codex_lane", lambda *args, **kwargs: terminated.append(args))

    def fake_run(command, **kwargs):
        nonlocal calls
        calls += 1
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
    result = json.loads(capsys.readouterr().out.splitlines()[-1])["assignment"]
    assert result["delivery_state"] == "delivery_uncertain"
    assert result["delivery_certainty"] == "unknown"
    assert result["failure_kind"] == "transport_timeout"
    assert result["prompt_accepted"] is None
    assert result["reconciliation_required"] is True
    assert terminated == []


def test_main_reports_deepagents_pane_run_failure(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    evidence = {
        "registry_launcher": {
            "assignment_task_sha256": LAUNCHER._sha256_text("assign lane"),
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
    times = iter([0.0, 1.0])
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

    def fake_run(command, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            return subprocess.CompletedProcess(command, 0, "", "")
        raise LAUNCHER.CommandTransportTimeout("assignment timeout")

    monkeypatch.setattr(LAUNCHER, "_run", fake_run)
    times = iter([0.0, 4.0])
    monkeypatch.setattr(LAUNCHER.time, "monotonic", lambda: next(times))

    assert LAUNCHER.main(
        [
            "--profile", "xhigh", "--session", "session", "--pane", "pane",
            "--cwd", str(ROOT), "--expected-base", "HEAD", "--task", "assign lane",
            "--grant-wall-clock-seconds", "3",
        ]
    ) == 2
    result = json.loads(capsys.readouterr().out.splitlines()[-1])["assignment"]
    assert result["delivery_state"] == "watchdog_expired"
    assert result["status"] == "BLOCKED"
    assert result["exit_code"] == 2
    assert result["watchdog"]["termination"]["verified"] is False


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
    assert json.loads(output[-1])["assignment"] == {
        "agent_name": "xhigh-main",
        "delivery_state": "delivery_failed",
        "delivery_certainty": "not_delivered",
        "delivery_task_sha256": LAUNCHER._sha256_text("assign lane"),
        "exit_code": 7,
        "failure_kind": "command_exit",
        "phase": "start",
        "grant_digest": None,
        "reconciliation_required": True,
        "session": "codex-probe",
        "status": "failed",
        "task_sha256": LAUNCHER._sha256_text("assign lane"),
    }


def test_launcher_allows_external_codex_controller(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HERDR_ENV", raising=False)

    environment = LAUNCHER._herdr_environment()

    assert "HERDR_ENV" not in environment


def test_target_selector_requires_both_auto_values() -> None:
    with pytest.raises(LAUNCHER.LaunchBlocked, match="must be used together"):
        LAUNCHER._resolve_target_selector(ROOT, "auto", "w1:p5", "herdr.exe")


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


def test_deepagents_main_strips_herdr_environment(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    evidence = {
        "registry_launcher": {
            "assignment_task_sha256": LAUNCHER._sha256_text("assign lane"),
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
            "report_present": True,
            "report_sha256": "report",
            "report_chars": 1,
            "foreground_processes": ["powershell.exe"],
            "observation_error": None,
        },
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


def test_deepagents_main_blocks_delivery_without_completion_report(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    evidence = {
        "registry_launcher": {
            "assignment_task_sha256": LAUNCHER._sha256_text("assign lane"),
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
    assert assignment["status"] == "no-report"
    assert assignment["task_accepted"] is False
    assert assignment["reconciliation_required"] is True


def test_deepagents_task_state_requires_report_for_completion() -> None:
    assert LAUNCHER._deepagents_task_state(
        [{"name": "powershell.exe"}],
        "Running task non-interactively...\n[OK] Task completed\n",
    ) == "completed"
    assert LAUNCHER._deepagents_task_state(
        [{"name": "powershell.exe"}],
        "Running task non-interactively...\n",
    ) == "no-report"
    assert LAUNCHER._deepagents_task_state(
        [{"name": "python.exe"}],
        "Running task non-interactively...\n",
    ) == "running"


def test_deepagents_task_state_detects_failure_report() -> None:
    assert LAUNCHER._deepagents_task_state(
        [{"name": "powershell.exe"}],
        "[FAIL] Task failed\n",
    ) == "failed"


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
    responses = iter([
        subprocess.CompletedProcess([], 0, process_info, ""),
        subprocess.CompletedProcess([], 0, json.dumps({"result": "Running task..."}), ""),
        subprocess.CompletedProcess([], 0, process_info, ""),
        subprocess.CompletedProcess([], 0, json.dumps({"result": "[OK] Task completed"}), ""),
    ])
    clock = [0.0]
    sleeps: list[float] = []
    monkeypatch.setattr(LAUNCHER, "_run", lambda *args, **kwargs: next(responses))
    monkeypatch.setattr(LAUNCHER.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(LAUNCHER.time, "sleep", lambda seconds: (sleeps.append(seconds), clock.__setitem__(0, clock[0] + seconds)))

    evidence = LAUNCHER._deepagents_completion_evidence(
        "herdr.exe",
        "session",
        "pane",
        env={},
    )

    assert evidence["state"] == "completed"
    assert sleeps


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
        Path("normal.toml"), "normal", "9router", "combo-normal", 20, True, "test", "test",
    )
    monkeypatch.setattr(LAUNCHER, "_profile", lambda *args: profile)
    monkeypatch.setattr(LAUNCHER, "_executable", lambda name: f"{name}.exe")
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
