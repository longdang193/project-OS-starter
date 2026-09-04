"""
@meta
name: test_native_personal_local_workflow
type: test
scope: unit
domain: docs
covers:
  - Native personal-local workflow source documentation
tags:
  - fast
  - ci-safe
lifecycle:
  status: active
"""

from __future__ import annotations

from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parent.parent


def run_git(repository: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repository), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def test_three_runtime_personal_local_workflow_is_documented() -> None:
    procedure = ROOT / "docs" / "operating_system" / "procedures" / "personal-local-worktree-procedure.md"
    procedure_text = procedure.read_text(encoding="utf-8")
    root_guidance = (ROOT / "docs" / "operating_system" / "templates" / "agents" / "root-AGENTS.template.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "native-personal-local" in procedure_text
    assert "Git worktree" in procedure_text
    assert "Codex, DeepAgents, or Tura" in procedure_text
    assert "planning/planning-dispatch.md" in procedure_text
    assert "Resume In A New Task" in procedure_text
    assert "dcode -r" in procedure_text
    assert "DeepAgents Tool Boundary" in procedure_text
    assert "--no-mcp" in procedure_text
    assert "Codex MCP servers" in procedure_text
    assert "codex.mcp.handoff.v1" in procedure_text
    assert "--handoff-file" in procedure_text
    assert "--mcp-select" in procedure_text
    assert "native-personal-local" in root_guidance
    assert "Codex, DeepAgents, or Tura" in root_guidance
    assert "planning/planning-dispatch.md" in root_guidance
    assert "native-personal-local" in readme
    assert "Codex, DeepAgents, or Tura" in readme
    assert "planning-dispatch.md" in readme


def test_deepagents_default_version_has_single_runtime_owner() -> None:
    setup = (ROOT / "scripts" / "setup_deepagents_runtime.ps1").read_text(encoding="utf-8")
    match = re.search(r'DeepAgentsCodeVersion = "([^"]+)"', setup)
    assert match is not None
    assert match.group(1)
    assert "version pinned by `scripts/setup_deepagents_runtime.ps1`" in (
        ROOT / "README.md"
    ).read_text(encoding="utf-8")
    assert "version pinned by" in (
        ROOT / "docs" / "operating_system" / "procedures" / "personal-local-worktree-procedure.md"
    ).read_text(encoding="utf-8")
    assert "setup-script-pinned `deepagents-code` version" in (
        ROOT / "docs" / "operating_system" / "runtime" / "runtime-surfaces.md"
    ).read_text(encoding="utf-8")
    assert "setup script owns the tested `deepagents-code` version" in (
        ROOT / "docs" / "operating_system" / "procedures" / "runtime-adapter-procedure.md"
    ).read_text(encoding="utf-8")


def test_deepagents_runtime_state_is_ignored() -> None:
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert ".langgraph_api/" in gitignore


def test_native_git_evidence_exposes_tracked_and_untracked_scope_changes(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    run_git(repository, "init", "-q")
    run_git(repository, "config", "user.name", "Test User")
    run_git(repository, "config", "user.email", "test@example.invalid")

    allowed = repository / "allowed.txt"
    allowed.write_text("before\n", encoding="utf-8")
    run_git(repository, "add", "allowed.txt")
    run_git(repository, "commit", "-qm", "baseline")
    base = run_git(repository, "rev-parse", "HEAD").stdout.strip()

    allowed.write_text("after\n", encoding="utf-8")
    (repository / "outside.txt").write_text("outside scope\n", encoding="utf-8")

    tracked = run_git(repository, "diff", "--name-status", "-z", "-M", "-C", "--find-copies-harder", base, "--").stdout.split("\0")
    untracked = run_git(repository, "ls-files", "--others", "--exclude-standard", "-z").stdout.split("\0")

    changed_paths = {tracked[index + 1] for index, entry in enumerate(tracked[:-1]) if entry == "M"}
    untracked_paths = {entry for entry in untracked if entry}

    assert changed_paths == {"allowed.txt"}
    assert untracked_paths == {"outside.txt"}
    assert untracked_paths - {"allowed.txt"}


def test_single_controller_resume_contract_is_documented() -> None:
    procedure_text = (
        ROOT / "docs" / "operating_system" / "procedures" / "personal-local-worktree-procedure.md"
    ).read_text(encoding="utf-8")
    template_text = (
        ROOT / "docs" / "operating_system" / "templates" / "implementation-plan-template.md"
    ).read_text(encoding="utf-8")

    for step in range(1, 8):
        assert f"{step}." in procedure_text
    assert "## Coordination State" in template_text
    assert "Coordination State (Optional)" not in template_text
    assert "Default task executor: `codex | deepagents | tura`" in template_text
    assert "each Git-tracked task ledger `Executor` value is authoritative" in template_text
    assert "Task ledger `Executor` values are `codex`, `deepagents`, or `tura`" in template_text
    assert "`Template Profile` and optional `Validator Profile` remain independent" in template_text
    assert "current DeepAgents launcher uses no MCP" in template_text
    assert "Active task(s)" not in template_text
    assert "multiple active tasks" in template_text
    assert "dependency-ready wave" in template_text
    assert "Last checkpoint" not in template_text
    assert "| Checkpoint |" not in template_text
    assert "git log -1 --format=%H -- <plan-path>" in procedure_text
    assert "Git owns checkpoint\nidentity" in template_text


def test_executor_selection_and_task_override_are_documented() -> None:
    dispatch = (ROOT / "docs" / "operating_system" / "planning" / "planning-dispatch.md").read_text(encoding="utf-8")
    template = (ROOT / "docs" / "operating_system" / "templates" / "implementation-plan-template.md").read_text(encoding="utf-8")

    assert "## Artifact Selection" in dispatch
    assert "## Executor Selection" in dispatch
    assert "`codex`" in dispatch
    assert "`deepagents`" in dispatch
    assert "`tura`" in dispatch
    assert "These are advisory eligibility rules, not a classifier." in dispatch
    assert "Do not map profile rank" in dispatch
    assert "`Controller`" not in template
    assert "`n  `" not in template


def test_git_tracked_coordination_uses_plan_ledger_not_session_ledger() -> None:
    procedure_text = (
        ROOT / "docs" / "operating_system" / "procedures" / "personal-local-worktree-procedure.md"
    ).read_text(encoding="utf-8")
    executing_skill = (
        ROOT / ".agents" / "skills" / "skill-executing-plans" / "SKILL.md"
    ).read_text(encoding="utf-8")
    subagent_skill = (
        ROOT / ".agents" / "skills" / "skill-subagent-driven-development" / "SKILL.md"
    ).read_text(encoding="utf-8")

    assert "Git-tracked coordinated work requires" in procedure_text
    assert 'dcode-project --role <profile> -n "<task>"' in procedure_text
    assert 'project-delegate --role <profile> -n "<task>"' in procedure_text
    assert "Codex, DeepAgents, or Tura" in procedure_text
    assert "Coordination State and task ledger" in executing_skill
    assert "active task ledger `Executor` and `Template Profile`\nvalues" in executing_skill
    assert "project-delegate` for" in executing_skill
    assert "profile is `none`" in executing_skill
    assert "active native Codex subagent capability" in executing_skill
    assert "Coordination State and task ledger" in subagent_skill
    assert "Codex launches one bounded `dcode-project`\n  task" in subagent_skill
    assert "## Profile Selection" in subagent_skill
    assert "Never override the model" in subagent_skill
    assert 'cat "$(git rev-parse --show-toplevel)/.superpowers/sdd/progress.md"' not in subagent_skill
    assert "Do not create `.superpowers/sdd/progress.md`" in subagent_skill


def test_runtime_adapter_contract_separates_executor_profile_and_auto() -> None:
    procedure_text = (
        ROOT / "docs" / "operating_system" / "procedures" / "runtime-adapter-procedure.md"
    ).read_text(encoding="utf-8")

    assert "wrapper\nrejects `--executor` and forces `--executor tura`" in procedure_text
    assert "`auto` is eligible only for the Native Codex controller" in procedure_text
    assert "`auto` answers which eligible ranked model endpoint to" in procedure_text
    assert "Native Codex delegated worker" in procedure_text
    assert "DeepAgents task or internal worker" in procedure_text
    assert "Tura worker" in procedure_text


def test_deepagents_internal_writers_remain_task_bounded() -> None:
    skill = (ROOT / ".agents" / "skills" / "skill-deepagents-executing-plans" / "SKILL.md").read_text(encoding="utf-8")

    assert "Runtime-internal" in skill
    assert "decomposition never becomes plan-level coordination" in skill
    normalized = " ".join(skill.split())
    assert "Nested writers remain inside active task workspace" in normalized
    assert "MAIN AGENT may spawn DeepAgents sub-agents when needed within its assigned lane" in normalized
    assert "MAIN AGENTS may use nested delegation when needed within assigned lane scope" in normalized
    assert "Sub-agents must not spawn peer MAIN AGENTS, activate CoS" in normalized
    assert "read-only decomposition" not in skill

def test_sdd_handoffs_keep_external_runtime_evidence_out_of_deepagents_paths() -> None:
    subagent_skill = (
        ROOT / ".agents" / "skills" / "skill-subagent-driven-development" / "SKILL.md"
    ).read_text(encoding="utf-8")
    implementer_prompt = (
        ROOT / ".agents" / "skills" / "skill-subagent-driven-development" / "implementer-prompt.md"
    ).read_text(encoding="utf-8")

    assert "Repository-local report paths only" in subagent_skill
    assert "Codex validates external or" in subagent_skill
    assert "sanitized facts or content" in subagent_skill
    assert "repository-relative report file path" in implementer_prompt


def test_coordination_authority_and_checkpoint_order_are_consistent() -> None:
    coordination_rule = (
        ROOT / "docs" / "operating_system" / "rules" / "git-tracked-coordination-rule.md"
    ).read_text(encoding="utf-8")
    precedence = (
        ROOT / "docs" / "operating_system" / "governance" / "precedence.md"
    ).read_text(encoding="utf-8")
    executing_skill = (
        ROOT / ".agents" / "skills" / "skill-executing-plans" / "SKILL.md"
    ).read_text(encoding="utf-8")
    subagent_skill = (
        ROOT / ".agents" / "skills" / "skill-subagent-driven-development" / "SKILL.md"
    ).read_text(encoding="utf-8")

    assert "Plan owns workflow state" in executing_skill
    assert "block on mismatch" in executing_skill
    assert "proposed` to `active" in coordination_rule
    assert "may weaken a canonical hard invariant" in precedence
    assert "disposable local mirror" in subagent_skill
    assert "lead creates the checkpoint commit after acceptance" in subagent_skill
    assert "progress ledger" not in subagent_skill


def test_sdd_shell_helpers_are_lf_normalized() -> None:
    scripts = ROOT / ".agents" / "skills" / "skill-subagent-driven-development" / "scripts"

    for name in ("review-package", "sdd-workspace", "task-brief"):
        assert b"\r\n" not in (scripts / name).read_bytes()


def test_deepagents_probe_selection_is_documented() -> None:
    procedure_text = (
        ROOT / "docs" / "operating_system" / "procedures" / "personal-local-worktree-procedure.md"
    ).read_text(encoding="utf-8")
    procedure_lower = procedure_text.lower()

    assert "## DeepAgents Probe Selection" in procedure_text
    assert "Routine probes" in procedure_text
    assert "Extended probes" in procedure_text
    assert "OS temporary directories" in procedure_text
    assert "tests own deterministic boundaries" in procedure_lower
    assert "probes own installed-runtime" in procedure_lower
    assert "Record probe ID" in procedure_text
    assert "executor/profile, exit code" in procedure_text
    assert "DEEPAGENTS_UPGRADE_OK" in procedure_text
    assert "selected model is `combo-normal`" in procedure_text
    assert "`dcode-doctor`" in procedure_text


def test_profile_order_and_independent_validator_selection_are_documented() -> None:
    policy_paths = (
        ROOT / "docs" / "operating_system" / "templates" / "agents" / "root-AGENTS.template.md",
        ROOT / "docs" / "operating_system" / "templates" / "implementation-plan-template.md",
        ROOT / ".agents" / "skills" / "skill-writing-plans" / "SKILL.md",
        ROOT / ".agents" / "skills" / "skill-deepagents-executing-plans" / "SKILL.md",
        ROOT / ".agents" / "skills" / "skill-subagent-driven-development" / "SKILL.md",
        ROOT / "docs" / "operating_system" / "runtime" / "runtime-surfaces.md",
        ROOT / "docs" / "operating_system" / "procedures" / "personal-local-worktree-procedure.md",
        ROOT / "docs" / "operating_system" / "procedures" / "runtime-adapter-procedure.md",
    )
    policy_texts = tuple(path.read_text(encoding="utf-8") for path in policy_paths)
    plan_template = policy_texts[1]

    for text in policy_texts:
        assert "unranked" in text.lower()
        assert "rank" in text.lower()
        assert "independently" in text.lower()
        assert (
            "lower, equal, or higher" in text.lower()
            or (
                "lower, equal, or" in text.lower()
                and "higher validator profile" in text.lower()
            )
            or "no profile-rank relationship is required" in text.lower()
        )
        assert "validator profile must rank above executor profile" not in text.lower()

    assert "discovered profile" in plan_template


    assert "- Selection basis: <validation>" in plan_template
    assert "no profile-rank relationship is required" in plan_template

    xhigh_role = (ROOT / "agents" / "xhigh.toml").read_text(encoding="utf-8")
    assert "validation of " + chr(96) + "high" + chr(96) + " work" not in xhigh_role
    assert "demanding validation" in xhigh_role


def test_checkpoint_identity_is_derived_from_git_ledger_commit(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    plan = repository / "docs" / "plans" / "work.md"
    plan.parent.mkdir(parents=True)
    run_git(repository, "init", "-q")
    run_git(repository, "config", "user.name", "Test User")
    run_git(repository, "config", "user.email", "test@example.invalid")

    task_file = repository / "task.txt"
    task_file.write_text("pending\n", encoding="utf-8")
    plan.write_text("Task 1: active\n", encoding="utf-8")
    run_git(repository, "add", ".")
    run_git(repository, "commit", "-qm", "baseline")
    base = run_git(repository, "rev-parse", "HEAD").stdout.strip()

    task_file.write_text("complete\n", encoding="utf-8")
    plan.write_text("Task 1: completed\n", encoding="utf-8")
    run_git(repository, "add", "task.txt", "docs/plans/work.md")
    run_git(repository, "commit", "-qm", "checkpoint task 1")

    head = run_git(repository, "rev-parse", "HEAD").stdout.strip()
    checkpoint = run_git(
        repository,
        "log",
        "-1",
        "--format=%H",
        "--",
        "docs/plans/work.md",
    ).stdout.strip()

    assert checkpoint == head
    assert run_git(repository, "merge-base", "--is-ancestor", base, checkpoint).returncode == 0
