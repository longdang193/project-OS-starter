---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
name: design-export-evidence-binding-follow-up
targets:
  - docs/operating_system/planning/planning-dispatch.md
  - tests/test_starter_lifecycle_contract.py
  - generated_exports/project-OS-starter-kit/docs/operating_system/planning/planning-dispatch.md
  - generated_exports/project-OS-starter-kit/tests/test_starter_lifecycle_contract.py
---

# Design Export Evidence Binding Follow-up Plan

## Review Findings

### [P1] Independent review must remain conditional

The proposed verdict makes reviewer `PASS` mandatory for every Design Export.
The canonical lifecycle makes independent review applicable only when risk or
policy requires it (`docs/operating_system/planning/planning-dispatch.md:43`).
The follow-up must bind review evidence only when that gate applies.

### [P1] Provider-only identity breaks method neutrality

The verdict requires provider-authoritative identity for every method, while
the canonical policy permits an explicitly selected Design Export method and
keeps named providers out of Starter dependencies
(`docs/operating_system/planning/planning-dispatch.md:16`, `:45-47`).
Use selected-method-authoritative durable output identity. Provider IDs are one
valid form; no provider tool name becomes policy.

### [P2] Generated Starter Kit copies are required outputs

The verdict calls regeneration conditional. The manifest copies all
`docs/operating_system` and `tests/test_starter_lifecycle_contract.py`
(`repo_config/starter-kit-manifest.json:8`, `:35`), and the builder copies
manifest paths into the generated kit (`scripts/build_starter_kit.py:170-185`).
Canonical edits therefore require generated Starter Kit rebuild and inspection.

### [P2] Phrase-only assertions do not protect the contract

The proposed test must cover method neutrality, current-task and requested-
deliverable binding, conditional review binding, and rejection of workspace
presence, stale evidence, inferred classification, and producer self-review.

### [P3] Defer schema and evaluator

No current provider contract, artifact registry, evaluator caller, or stable
machine-readable response exists in this repository. Do not add a rule,
schema, enum, evaluator, provider skill, manifest entry, or tool-specific
integration until a real provider contract creates a concrete consumer need.

### [P1] Execution must use one workspace

The prior plan mixed current-workspace execution with a clean worktree only at
generation time. That loses uncommitted canonical edits unless they are
committed or copied, and the Starter Kit builder reconstructs the whole kit
from all manifest paths. Select current workspace or one clean worktree before
Task 1 and do not switch during execution.

### [P2] Test order must match selected proof method

The plan selected `skill-test-driven-development` but edited policy before
adding its regression test. Keep TDD for this contract change: write the
focused assertion, observe the expected failure, then make the smallest policy
edit and observe the pass.

### [P2] Build must follow repository procedure

Starter Kit procedure validates repository configuration before building. Add
`py -3 scripts/validate_repo_config.py` before
`py -3 scripts/build_starter_kit.py`.

### [P2] Avoid permanent bans on future generic fields

`artifactRef` and `deliverableClass` are not current policy, but banning those
names forever would couple a future real contract to this regression test.
Scope and diff review enforce no speculative schema now. Tests only reject
provider leakage that current policy explicitly forbids.

## Goal

Harden the existing conditional Design Export lifecycle gate without reopening
the completed cross-file promotion reconciliation. Completion must require
durable output identity from the selected export method, bound to the current
task and requested deliverable. Independent review remains conditional and,
when applicable, must bind to the same task and output identities.

## Implementation Outcomes

### Method-neutral fail-closed lifecycle contract

`planning-dispatch.md` remains the sole lifecycle owner. It rejects agent prose,
workspace presence, inferred classification, stale evidence, and producer
self-assessment as completion proof. It accepts provider IDs or another
selected-method-authoritative durable identity when bound to current task and
requested deliverable. Missing identity or freshness evidence leaves the gate
`incomplete` or `blocked`.

### Regression and Starter Kit alignment

The lifecycle test protects the new semantic contract without naming
OpenDesign tools or speculative fields. Starter Kit output is rebuilt from
canonical sources and validated; generated files are never edited directly.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `none`
- Default task executor: `codex`
- Required skills: `skill-test-driven-development`, `skill-verification-before-completion`
- Isolation: `current workspace or one clean worktree selected before Task 1`
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit the two canonical files, run focused tests, build and validate Starter Kit, run repository validation, inspect generated diffs, and run `git diff --check`
- User-approval actions: push, merge, publication, external writes, destructive cleanup, discard, or edits outside declared canonical and generated outputs
- Parallel ownership: none; canonical edits and generation are ordered
- Sequential fallback: Tasks 1 through 2 in order

Before execution, record `git status --short --untracked-files=all` and
`git diff --name-only`. If any manifest-owned source or generated destination
is dirty outside declared scope, stop or select one clean worktree before
Task 1. Otherwise execute entirely in the current workspace. Never switch
workspaces between canonical edits and generation. Preserve all unrelated
changes; do not discard, reset, stash, or overwrite them.

## Task Breakdown

### Task 1: Test and add bound, method-neutral completion rule

**Purpose:**
- Add the missing lifecycle invariant without creating a new policy owner or provider dependency.

**Task Function:**
- Reconcile Design Export completion semantics with existing conditional lifecycle ownership.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: small canonical policy edit with no delegated benefit.

**Validator Profile:**
- Controller-selected: `xhigh`
- Selection basis: adversarial contract review already identified lifecycle and provider-neutrality risks.

**Specification Coverage:**
- Preserve conditional Design Export triggering and conditional independent review.
- Require selected-method-authoritative durable output identity bound to current task and requested deliverable.
- Fail closed when identity cannot be attributed to the current task or run.

**Required Skills:**
- `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `docs/operating_system/planning/planning-dispatch.md:16`, `:27-54`
- Modify: `docs/operating_system/planning/planning-dispatch.md` immediately after the existing approval and method-selection paragraph.
- Verify: `docs/operating_system/prompt_templates/design-spec-prompt.md:23` and `docs/superpowers/plans/2026-08-28-17-53-conditional-design-export-promotion-gate-plan.md:373-378`

**Dependencies:**
- Keep `docs/superpowers/plans/2026-08-28-17-53-conditional-design-export-promotion-gate-plan.md` unchanged; it is completed historical scope.

**Authority:**
- Preauthorized local actions: modify only `planning-dispatch.md` and `tests/test_starter_lifecycle_contract.py`; run the focused test.
- Stop for: mandatory-review wording, provider-specific tool names, new global deliverable taxonomy, or scope beyond the declared file.

**Steps:**
- [x] Add focused assertions for selected-method-authoritative durable output identity, current-task binding, requested-deliverable binding, conditional review, and same-task/output review binding.
- [x] Add assertions rejecting workspace presence, agent prose, inferred classification, evidence from another task or run, and producer self-assessment.
- [x] Add negative assertions for `OpenDesign`, `studio_create`, and `studio_status` only; do not ban generic future field names.
- [x] Run `py -3 -m pytest tests/test_starter_lifecycle_contract.py -q` and confirm expected failure.
- [x] Add the smallest policy paragraph to `planning-dispatch.md` satisfying the failing assertions.
- [x] Re-run `py -3 -m pytest tests/test_starter_lifecycle_contract.py -q` and confirm pass.

**Verification:**
- [x] `py -3 -m pytest tests/test_starter_lifecycle_contract.py -q`
- Expected: first run fails for missing contract; second run passes.

**Exit Criteria:**
- Dispatch owns one provider-neutral, fail-closed completion invariant and does not make independent review universal.

### Task 2: Rebuild and verify Starter Kit outputs

**Purpose:**
- Reconcile generated Starter Kit copies with canonical edits and prove no unrelated surfaces changed.

**Task Function:**
- Run ordered generation, validation, and final scope inspection.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: generation is repository-owned and requires controller authority over dirty-scope classification.

**Validator Profile:**
- Controller-selected: `normal`
- Selection basis: generated parity and command-result validation are deterministic.

**Specification Coverage:**
- Generated copies reflect both canonical files.
- No adapter regeneration, manifest change, rule, evaluator, schema, or provider skill is introduced.

**Required Skills:**
- `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: `repo_config/starter-kit-manifest.json:3-40`, `scripts/build_starter_kit.py:170-185`, generated output tree.
- Modify: generator-owned `generated_exports/project-OS-starter-kit/**` only through `py -3 scripts/build_starter_kit.py`.
- Verify: canonical/generated parity and Git scope.

**Dependencies:**
- Task 1 complete.
- Clean or explicitly classified manifest-owned sources and generated destinations.

**Authority:**
- Preauthorized local actions: build Starter Kit, validate output, run declared tests and validators, inspect diffs.
- Stop for: dirty generator destinations, unrelated source files copied into output, generated drift, failed validation, or paths outside declared scope.

**Steps:**
- [x] Re-run `git status --short --untracked-files=all` and `git diff --name-only`.
- [x] Run `py -3 scripts/validate_repo_config.py`.
- [x] Run `py -3 scripts/build_starter_kit.py`.
- [x] Inspect generated copies of `planning-dispatch.md` and `test_starter_lifecycle_contract.py`.
- [x] Confirm no adapter-owned files changed; do not run `scripts/sync_agent_adapters.py` as an implementation step.
- [x] Run final verification commands.

**Verification:**
- [x] `py -3 scripts/validate_starter_kit.py`
- [x] `py -3 -m pytest tests/test_starter_lifecycle_contract.py tests/test_starter_kit_generation.py -q`
- [x] `py -3 scripts/validate_repo_contracts.py`
- [x] `git diff --check`
- Expected: validation passes; generated copies match canonical sources; final diff contains only two canonical files plus generated Starter Kit copies and this plan.

**Exit Criteria:**
- Starter Kit is rebuilt and validated without adapter changes, speculative infrastructure, or unrelated dirty-work loss.

## Verification

- `py -3 -m pytest tests/test_starter_lifecycle_contract.py tests/test_starter_kit_generation.py -q`
- `py -3 scripts/validate_starter_kit.py`
- `py -3 scripts/validate_repo_contracts.py`
- `git diff --check`
- Inspect `git diff --name-only` and confirm scope is the two canonical files, generated Starter Kit copies, and this plan.

## Completion Criteria

The plan is ready for completion verification when:

1. `planning-dispatch.md` remains sole owner of the Design Export lifecycle gate.
2. Completion requires selected-method-authoritative durable output identity bound to current task and requested deliverable.
3. Independent review remains conditional; applicable `PASS` binds to the same task and output identities.
4. Workspace presence, agent prose, inferred classification, stale evidence, and producer self-assessment cannot establish completion.
5. No provider tool names, provider-specific schema, global deliverable enum, evaluator, new rule, or new manifest entry is introduced; this is proven by task scope and final diff inspection, not permanent generic-field bans.
6. Focused lifecycle tests cover positive binding and fail-closed negative cases.
7. Generated Starter Kit copies are rebuilt from canonical sources and validated.
8. Fresh final verification returns no required failures, stale generated output, or unrecorded scope deviation.

## Execution Evidence

- `py -3 -m pytest tests/test_starter_lifecycle_contract.py -q`: `8 passed` after the red run identified the missing contract.
- `py -3 scripts/validate_repo_config.py`: passed.
- `py -3 scripts/build_starter_kit.py`: rebuilt `generated_exports/project-OS-starter-kit`.
- `py -3 scripts/validate_starter_kit.py`: passed.
- `py -3 -m pytest tests/test_starter_lifecycle_contract.py tests/test_starter_kit_generation.py -q`: `17 passed`.
- `py -3 scripts/validate_repo_contracts.py`: passed; `54 passed` internal checks.
- `git diff --check`: passed with only Git line-ending warnings.
- Canonical/generated hashes match for both changed Starter Kit files.
- Existing unrelated untracked `.playwright-mcp/**` and `db/session_log/**` paths remain untouched.

Plan status: `completed` after implementation and verification evidence.
