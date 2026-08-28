---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
name: review-profile-contract-correction
targets:
  - agents/review.toml
  - tests/test_agent_profile_registry.py
  - generated_agents/codex/agents/review.toml
---

# Review Profile Contract Correction

## Goal

Add `review` as an unranked, explicit-only specialized profile for independent
read-only code review and verification, using `combo-review`, without changing
ranked routing, registry logic, skill ownership, or unrelated workspace state.

## Implementation Outcomes

### Corrected canonical profile

`agents/review.toml` defines `review` with provider `9router` and model
`combo-review`. It omits `rank`, so the profile remains unranked and
non-orderable. It omits `deepagents_compatible`, preserving the registry's
current default of `true`; runtime compatibility is verified separately.

Profile instructions prohibit implementation and Git mutation, permit bounded
verification commands with disposable ignored/cache/temp side effects, and
defer output formatting to the task-specific review contract. `PASS`, `FAIL`,
or `BLOCKED` is only the fallback format when no task format exists.

### Focused configuration proof

`tests/test_agent_profile_registry.py` protects the actual repository profile's
identity and semantics without duplicating generic registry behavior.

### Generated runtime alignment

The Codex generated profile is regenerated from `agents/review.toml`. No
generated file is edited directly.

### Runtime compatibility evidence

One bounded `dcode-project --role review --print-config` check proves role
resolution and effective model selection for the launcher-pinned DeepAgents
executor. The local `dcode-project` wrapper rejects an explicit `--executor`
and invokes the repository launcher with `--executor deepagents`; one
DeepAgents smoke is attempted only when the configured
provider capability is available. A generic environmental blocker is recorded
as `BLOCKED`; proven model/API incompatibility is also `BLOCKED` and prevents
plan completion until the plan is amended, because omitted compatibility
defaults to `true`.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `none`
- Default task executor: `codex`
- Required skills: `skill-test-driven-development`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit named profile and test files, regenerate Codex output, run declared local tests, run bounded local profile smoke
- User-approval actions: provider authentication, external writes, commit, push, discard, cleanup of unrelated files, or destructive recovery
- Parallel ownership: none
- Sequential fallback: execute tasks in listed order

## Task Breakdown

### Task 1: Correct Canonical Review Profile

**Purpose:**
- Replace the current local draft with the reviewed read-only contract.

**Task Function:**
- Agent profile configuration maintenance.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: small, design-clear local configuration change.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused registry proof follows in Task 2.

**Specification Coverage:**
- Profile identity is `review` with model `combo-review`.
- Profile is unranked and explicit-only.
- Profile does not implement fixes or mutate repository-owned state.
- Bounded verification may create disposable ignored/cache/temp artifacts.
- Task-specific output contracts remain authoritative.

**Required Skills:**
- `skill-test-driven-development`

**Files And Symbols:**
- Modify: `agents/review.toml`
- Verify: `scripts/agent_profile_registry.py:load_agent_profiles`

**Dependencies:**
- Current registry schema remains authoritative.
- Preserve unrelated untracked paths, including `.playwright-mcp/` and `db/`.

**Authority:**
- Preauthorized local actions: edit `agents/review.toml` only.
- Stop for: requested provider changes, new registry fields, or changes outside named surfaces.

**Steps:**
- [x] Replace current profile wording with the reviewed contract.
- [x] Keep `model_provider = "9router"` and `model = "combo-review"`.
- [x] Omit both `rank` and `deepagents_compatible`.
- [x] Ban implementation, repository-owned file, Git index, HEAD, branch, commit, and push mutation.
- [x] Permit bounded verification side effects only when disposable and task-authorized.

**Verification:**
- [x] Load the real profile registry.
- Expected: `review.rank is None`, `review.model == "combo-review"`, and `review.deepagents_compatible is True`.

**Exit Criteria:**
- Canonical profile parses and expresses read-only review behavior without taking ownership of task-specific output format.

### Task 2: Add Real-Registry Regression Proof

**Purpose:**
- Prevent accidental removal, ranking, or model drift in the canonical `review` profile.

**Task Function:**
- Configuration regression testing.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: focused test in existing profile-registry suite.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: the focused test is the validation boundary.

**Specification Coverage:**
- Protect actual repository profile identity, unranked semantics, default compatibility, and essential instruction boundaries.

**Required Skills:**
- `skill-test-driven-development`

**Files And Symbols:**
- Modify: `tests/test_agent_profile_registry.py`
- Inspect: existing `load_agent_profiles` test helpers and assertions
- Verify: actual `agents/` directory in current repository

**Dependencies:**
- Task 1 complete.

**Authority:**
- Preauthorized local actions: add one focused test in the named file.
- Stop for: need to change registry implementation or duplicate generic sync tests.

**Steps:**
- [x] Add one test loading the repository's actual profiles.
- [x] Assert `review` exists, has no rank, uses `combo-review`, and defaults to DeepAgents-compatible.
- [x] Assert stable instruction boundaries without comparing the full prose body.

**Verification:**
- [x] `py -3 -m pytest -q tests/test_agent_profile_registry.py`
- Expected: all profile-registry tests pass.

**Exit Criteria:**
- Canonical profile drift fails a focused regression test.

### Task 3: Regenerate Codex Agent Surface

**Purpose:**
- Synchronize the canonical profile into its managed Codex output.

**Task Function:**
- Generated-surface synchronization.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: deterministic generator execution.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: generator drift check provides proof.

**Specification Coverage:**
- Generated output derives from the canonical profile and retains generated ownership headers.

**Required Skills:**
- `none`

**Files And Symbols:**
- Modify through generator: `generated_agents/codex/agents/review.toml`
- Verify: `scripts/sync_agent_adapters.py`

**Dependencies:**
- Task 2 complete.

**Authority:**
- Preauthorized local actions: run adapter synchronization and drift check.
- Stop for: nondeterministic changes or generated edits outside the profile output.

**Steps:**
- [x] Run Codex-only adapter synchronization.
- [x] Confirm generated Codex output contains `review` and `combo-review`.
- [x] Run all-platform drift verification.

**Verification:**
- [x] `py -3 scripts/sync_agent_adapters.py --platform codex`
- [x] `py -3 scripts/sync_agent_adapters.py --check --all-platforms`
- Expected: synchronization succeeds and drift check reports outputs up to date.

**Exit Criteria:**
- Generated Codex profile matches canonical source; no generated file was hand-edited.

### Task 4: Verify Role Resolution and Runtime Capability

**Purpose:**
- Prove static role selection and separately assess whether `combo-review` works through the configured DeepAgents provider route.

**Task Function:**
- Bounded runtime verification.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: Codex owns runtime/provider boundary and final acceptance.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: runtime evidence is collected directly by the lead controller.

**Specification Coverage:**
- `review` resolves explicitly to `combo-review`.
- Runtime compatibility is not claimed from source inspection alone.
- Provider/API failure remains a concrete blocker, not a reason for speculative profile changes.

**Required Skills:**
- `skill-verification-before-completion`

**Files And Symbols:**
- Verify: `scripts/dcode_project.py` role loading and DeepAgents compatibility gate
- Verify: generated role surface under `generated_agents/codex/agents/review.toml`

**Dependencies:**
- Tasks 1–3 complete.
- Existing provider credentials and local runtime configuration are available.

**Authority:**
- Preauthorized local actions: read-only role print-config and one bounded smoke.
- Stop for: authentication, provider, Responses API, or runtime capability blockers; do not install or authenticate new providers.

**Steps:**
- [x] Run `dcode-project --role review --print-config` (the wrapper pins DeepAgents).
- [x] Confirm selected role is `review`, effective model is `openai:combo-review`, and compatibility is `true`.
- [x] Run one bounded DeepAgents read-only review smoke when capability is available.
- [x] Record `PASS`, `FAIL`, or `BLOCKED` with concrete runtime evidence.
- [x] Treat ignored `.deepagents/agents/**` role views as expected launcher-owned runtime output.

**Verification:**
- [x] `dcode-project --role review --print-config`
- [x] Bounded DeepAgents smoke using `--role review` and a read-only task.
- Expected launcher side effect: ignored `.deepagents/agents/**` role views may be created or refreshed.
- Expected: role resolution passes; smoke returns a valid read-only review result or records a specific environmental `BLOCKED` capability.
- `FAIL` only when the worker changes tracked/canonical source, tests, configuration, documentation, Git index, `HEAD`, refs, commits, or other user-owned state.
- Proven `combo-review`/Responses API incompatibility is `BLOCKED` and prevents plan completion until the plan is amended; do not silently set compatibility to `false`.

**Exit Criteria:**
- Static profile behavior is proven. Runtime compatibility is proven by smoke, or an environmental blocker is explicitly recorded. Proven model/API incompatibility blocks completion and requires plan amendment.

## Verification

- `py -3 scripts/sync_agent_adapters.py --check --all-platforms`
- `py -3 -m pytest -q tests/test_agent_profile_registry.py tests/test_sync_agent_adapters.py`
- `dcode-project --role review --print-config`
- `py -3 scripts/validate_planning_lifecycle.py`
- `git diff --check`
- `git status --short`

## Execution Evidence

- `py -3 scripts/validate_planning_lifecycle.py` passed.
- `py -3 scripts/sync_agent_adapters.py --check --all-platforms` passed; generated adapters are current.
- `py -3 -m pytest -q tests/test_agent_profile_registry.py tests/test_sync_agent_adapters.py` passed: `31 passed`.
- `dcode-project --role review --print-config` passed: `selected_role=review`, `effective_model=openai:combo-review`, `selected_executor=deepagents`.
- Bounded DeepAgents smoke completed with exit code 0 after server startup and read-only execution; deterministic capability check returned `PASS` in 52.2s. A prior 120-second attempt timed out, but the 300-second retry completed without `DAEMON_RESTARTED`, artifact-generation failure, or tracked-file mutation.
- `git diff --check` passed. Unrelated `.playwright-mcp/` and `db/` paths remain preserved.

## Completion Criteria

The plan is ready for completion verification when:

1. `agents/review.toml` defines unranked `review` with `combo-review`.
2. Omitted `deepagents_compatible` resolves to `true` through the existing registry default.
3. Profile instructions preserve read-only repository/Git boundaries and task-specific output ownership.
4. A focused real-registry test protects profile identity and semantics.
5. Generated Codex output is synchronized and drift-free.
6. Role print-config proves explicit resolution to `openai:combo-review`.
7. DeepAgents runtime result is `PASS`, or a concrete environmental `BLOCKED` result is recorded; proven model/API incompatibility blocks completion and requires plan amendment.
8. No registry, sync, routing, Starter manifest, or skill logic changes are introduced.
9. Unrelated workspace paths remain preserved.
10. `skill-verification-before-completion` confirms fresh evidence before the plan status changes to `completed`.
