---
layer: change
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
name: deepagents-mcp-autonomy
targets:
  - scripts/dcode_project.py
  - tests/test_dcode_project.py
  - scripts/herdr_main_launcher.py
  - tests/test_herdr_main_launcher.py
  - scripts/setup_deepagents_runtime.ps1
  - README.md
  - docs/operating_system/procedures/runtime-adapter-procedure.md
  - docs/operating_system/procedures/personal-local-worktree-procedure.md
  - docs/operating_system/tooling/runtime-tool-resolution.md
  - docs/operating_system/tooling/frontend-backend-integration-tools.md
  - docs/operating_system/runtime/runtime-surfaces.md
  - docs/operating_system/templates/implementation-plan-template.md
  - .agents/skills/skill-executing-plans/SKILL.md
  - .agents/skills/skill-deepagents-executing-plans/SKILL.md
  - .agents/skills/skill-writing-plans/SKILL.md
  - .agents/skills/skill-subagent-driven-development/SKILL.md
  - .agents/skills/skill-chief-of-staff/SKILL.md
  - docs/operating_system/templates/agents/root-AGENTS.template.md
  - generated_agents/
---

# DeepAgents MCP Autonomy

## Goal

Allow DeepAgents to select and call MCP tools from one approved MCP pool while
keeping Codex-owned configuration, credentials, policy, and Git coordination.
Minimize per-task MCP management. Preserve default-deny behavior when direct
MCP access is not explicitly enabled.

## Implementation Outcomes

### Agent-selected approved MCP pool

`dcode-project` exposes a configured MCP pool to DeepAgents through native
DeepAgents MCP configuration. DeepAgents may choose any server and tool in the
approved pool at runtime. Unknown servers, tools, config paths, and unmanaged
runtime flags remain rejected.

### Safe configuration projection

Codex MCP configuration remains the source of server definitions. Launcher
projection does not copy credentials into task text, handoff facts, tracked
files, or logs. Runtime discovery cannot silently widen the approved pool.

### Contract and regression alignment

Launcher tests prove disabled, approved, denied, malformed, and cleanup paths.
Canonical runtime procedures, skills, README guidance, setup behavior, and
generated agent surfaces describe the same direct-MCP contract.

## Execution Approach

- Mode: `parallel-capable`
- Coordination: `git-tracked`
- Default task executor: `codex`
- Required skills: `skill-code-standards`, `skill-backend-verification`, `skill-dispatching-parallel-agents`, `skill-verification-before-completion`
- Isolation: `current workspace`; preserve pre-existing user changes and disposable paths
- Commit policy: `no commits during execution`
- Preauthorized local actions: inspect source; add this plan; edit declared launcher, tests, canonical docs, skills, and setup script; run focused validators; run bounded installed-runtime MCP smoke only when configuration already exists
- User-approval actions: credentials, authentication, runtime installation, external MCP writes, commits, push, merge, publication, destructive cleanup, and changes outside declared targets
- Parallel ownership: read-only review lanes may run concurrently; one implementation writer owns all code/config/doc changes after review
- Sequential fallback: review findings first, activate plan, patch once, run independent validation review, then final verification

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/lightmem2-overlay-hub`
- Base commit: `070ae5b`
- Expected workspace: preserve existing modified canonical/generated coordination files and untracked `.playwright-mcp/`, `db/`, and `out/`; do not clean or reset them
- Next action: final verification passed; user decides commit or further runtime smoke
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | native `dcode` MCP behavior and safe projection recommendation | `dcode --help`; `dcode mcp config`; review PASS with live-proof deferral |
| Task 2 | `completed` | current | `codex` | none | affected canonical files, generated surfaces, and test matrix | review FAIL recorded; stale contract map returned |
| Task 3 | `completed` | current | `codex` | Tasks 1-2 | focused launcher tests pass | `114 passed`; py_compile; diff check; independent review findings resolved |
| Task 4 | `completed` | current | `codex` | Task 3 | sync and contract validators pass | `71 passed`; sync and parity checks passed; stale scan clean |
| Task 5 | `completed` | current | `codex` | Task 3, Task 4 | review PASS plus final test evidence | `PASS`; 187 focused tests; lifecycle/contracts; sync parity; starter validation; diff check |

## Task Breakdown

### Task 1: Native Runtime And Security Review

**Purpose:**
- Determine safest minimal use of `dcode --mcp-config`, discovery paths, trust flags, and runtime home isolation.

**Task Function:**
- Review native runtime behavior and identify implementation constraints.

**Template Profile:**
- Controller-selected: `review`
- Selection basis: independent security/runtime verification; no edits permitted.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: review lane is itself read-only validation.

**Specification Coverage:**
- DeepAgents may select tools from an approved MCP pool; runtime must not inherit unmanaged MCPs or credentials.

**Required Skills:**
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/dcode_project.py:_mcp_capabilities`, `scripts/dcode_project.py:main`
- Inspect: `scripts/setup_deepagents_runtime.ps1`
- Verify: installed `dcode --help`, `dcode mcp config`, and bounded fake-process argv capture

**Dependencies:**
- none

**Authority:**
- Preauthorized local actions: read-only inspection and bounded help/config commands
- Stop for: credentials, login, installation, or external MCP calls

**Steps:**
- [x] Confirm native config format and discovery precedence.
- [x] Identify how launcher prevents unrelated user/project MCP configs from entering a task.
- [x] Recommend smallest safe policy/config mechanism and required failure tests.

**Verification:**
- [x] Return `PASS`, `FAIL`, or `BLOCKED` with path:line and command evidence.

**Exit Criteria:**
- Safe native projection path and known runtime risks documented.

### Task 2: Repository Contract And Test Review

**Purpose:**
- Map all canonical policy, procedure, generated, and regression surfaces that currently enforce `--no-mcp`.

**Task Function:**
- Review repository contract and change impact.

**Template Profile:**
- Controller-selected: `review`
- Selection basis: independent source/test review; no edits permitted.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: review lane is itself read-only validation.

**Specification Coverage:**
- Direct MCP support changes runtime, security, setup, and delegation contracts together.

**Required Skills:**
- `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/dcode_project.py`, `tests/test_dcode_project.py`
- Inspect: README, runtime procedures, canonical DeepAgents skills, root template
- Verify: `scripts/sync_agent_adapters.py` ownership and relevant validators

**Dependencies:**
- none

**Authority:**
- Preauthorized local actions: read-only inspection; no tracked-file edits
- Stop for: scope requiring unrelated runtime or product changes

**Steps:**
- [x] Identify exact stale assertions and docs.
- [x] Separate canonical sources from generated outputs.
- [x] Return disjoint implementation ownership and focused proof commands.

**Verification:**
- [x] Return `PASS`, `FAIL`, or `BLOCKED` with path:line evidence.

**Exit Criteria:**
- Complete impact map and test/documentation matrix returned.

### Task 3: Implement Launcher Projection

**Purpose:**
- Add config-driven approved MCP pool projection and agent runtime selection without weakening default-deny behavior.

**Task Function:**
- Implement smallest native launcher change supported by Tasks 1-2.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded multi-file implementation with ordinary contract risk.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent security and regression review.

**Specification Coverage:**
- Approved pool visible to DeepAgents; DeepAgents chooses within pool; credentials stay out of task text and tracked state.

**Required Skills:**
- `skill-code-standards`, `skill-backend-verification`

**Files And Symbols:**
- Modify: `scripts/dcode_project.py`
- Modify: `tests/test_dcode_project.py`
- Modify: `scripts/herdr_main_launcher.py`
- Modify: `tests/test_herdr_main_launcher.py`
- Verify: launcher argv, environment, temp-config cleanup, and failure paths

**Dependencies:**
- Tasks 1-2 complete

**Authority:**
- Preauthorized local actions: edit only declared launcher/test files; run focused tests
- Stop for: native runtime limitation requiring installation/authentication or policy expansion

**Steps:**
- [x] Implement approved MCP pool selection and isolated native config projection.
- [x] Remove only the unconditional Herdr-side `--no-mcp` injection; preserve explicit default-deny policy in `dcode-project`.
- [x] Preserve `codex.mcp.handoff.v1` as facts/provenance, not tool access.
- [x] Add tests for disabled/default, approved selection, unknown selection, config leakage, and cleanup.

**Verification:**
- [x] `py -3 -m pytest tests/test_dcode_project.py tests/test_herdr_main_launcher.py -q`
- Expected: all focused tests pass, including new direct-MCP contract cases.

**Exit Criteria:**
- Launcher exposes only policy-approved MCPs and keeps existing executor/runtime contracts intact.

### Task 4: Reconcile Docs, Skills, Setup, And Generated Outputs

**Purpose:**
- Replace stale no-MCP-only guidance with the approved-pool contract.

**Task Function:**
- Update canonical documentation and regenerate derived agent surfaces.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded canonical-source and generated-output reconciliation.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: generated-surface and stale-reference verification.

**Specification Coverage:**
- Docs must state direct MCP is opt-in/configured, agent-selected within approved pool, and default-deny outside it.

**Required Skills:**
- `skill-code-standards`

**Files And Symbols:**
- Modify: `README.md`, runtime procedures, tooling guidance, runtime surfaces, plan template, canonical DeepAgents skills, root template
- Modify if required: `scripts/setup_deepagents_runtime.ps1`
- Regenerate: `generated_agents/`
- Verify: `scripts/sync_agent_adapters.py` and stale `--no-mcp` assertions

**Dependencies:**
- Task 3 complete

**Authority:**
- Preauthorized local actions: edit declared canonical surfaces; run sync and validators
- Stop for: generated output conflict with unrelated pre-existing user edits

**Steps:**
- [x] Update canonical text and setup behavior to match implemented boundary.
- [x] Run adapter sync; do not hand-edit generated outputs.
- [x] Verify no stale contract claims remain outside historical plans.

**Verification:**
- [x] `py -3 scripts/sync_agent_adapters.py`
- [x] `py -3 -m pytest tests/test_sync_agent_adapters.py tests/test_validate_repo_contracts.py -q`

**Exit Criteria:**
- Canonical and generated surfaces agree with launcher behavior.

### Task 5: Independent Verification

**Purpose:**
- Confirm direct MCP autonomy, security boundary, generated parity, and preservation of unrelated work.

**Task Function:**
- Final verification and change review.

**Template Profile:**
- Controller-selected: `review`
- Selection basis: independent final acceptance review.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: final review lane owns validation only.

**Specification Coverage:**
- Direct MCP works only through approved pool; default-deny and cleanup remain intact.

**Required Skills:**
- `skill-verification-before-completion`, `skill-backend-verification`

**Files And Symbols:**
- Verify: all changed files and current Git diff
- Verify: focused tests, contract validators, and bounded installed-runtime smoke when credentials are already configured

**Dependencies:**
- Tasks 3-4 complete

**Authority:**
- Preauthorized local actions: read-only verification and bounded local tests
- Stop for: authentication, external MCP side effects, unrelated failures, or dirty-state ambiguity

**Steps:**
- [x] Run focused launcher and contract tests.
- [x] Run repository validation appropriate to changed surfaces.
- [x] Inspect diff and confirm pre-existing changes remain untouched.

**Verification:**
- [x] `py -3 -m pytest tests/test_dcode_project.py tests/test_sync_agent_adapters.py tests/test_validate_repo_contracts.py -q`
- [x] `py -3 scripts/validate_starter_kit.py`

**Exit Criteria:**
- Independent reviewer returns `PASS`; no required proof remains missing.

## Verification

- `py -3 -m pytest tests/test_dcode_project.py tests/test_sync_agent_adapters.py tests/test_validate_repo_contracts.py -q`
- `py -3 scripts/validate_starter_kit.py`
- `git diff --check`
- bounded native DeepAgents MCP smoke only when existing credentials and approved MCP config are already available

## Completion Criteria

The plan is ready for completion verification when:

1. DeepAgents can select and call approved MCP tools through launcher-owned configuration.
2. Default-deny, unknown-tool rejection, credential exclusion, and cleanup tests pass.
3. Canonical docs, skills, setup, and generated outputs match source behavior.
4. Existing user changes and disposable paths remain intact.
5. Independent verification returns `PASS` with fresh command evidence.
