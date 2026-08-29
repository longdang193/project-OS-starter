---
template_id: implementation-plan
contract_version: "1"
name: Switchyard auto-routing contract hardening
artifact_type: plan
status: completed
layer: change
parent_spec: none
---

# Switchyard Auto-Routing Contract Hardening Plan

## Goal

Harden the existing private Switchyard auto-routing integration without changing
routing economics, starter-kit boundaries, or fixed profile semantics.

## Implementation Outcomes

### V1 structural contract is enforceable

Policy v1 accepts only the declared `normal` to `high` automatic band, requires
`route_id = "auto"`, and proves `normal.rank < high.rank`. `low` and `xhigh`
remain explicit-only. Picker, threshold, and recent-window values remain tunable
until calibration justifies a policy change.

### Repository tests are hermetic and CI-covered

Switchyard manager tests run without `$HOME`, user-local runtime files, a running
server, credentials, or network access. The canonical repository contract runner
executes the manager regression suite when that suite exists, while starter-kit
validation remains safe when factory-only files are absent.

### Runtime provenance has one durable owner

The locally patched Switchyard build is reproducible from a tracked upstream
revision, patch artifact, and build/install recipe. The policy no longer presents
an unused minimum-version field as compatibility proof.

### Operational guidance stays private and non-duplicated

`runtime-adapter-procedure.md` states that `auto` is a runtime routing mode, not
a capability profile, and records its experimental/no-savings-claim status. Root
profile guidance, planning schema, and starter-kit contents remain unchanged.

## Non-Goals

- Do not change `capable_first` to `efficient_first`.
- Do not add Switchyard files to the generated starter kit.
- Do not add `agents/auto.toml` or `auto` to plan profile enums.
- Do not add a classifier, analytics store, cost join, new CI workflow, or router.
- Do not run provider-billed calibration or live smoke as part of structural fixes.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Default task executor: `codex`
- Required skills: `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`, `skill-verification-before-completion`
- Isolation: `current workspace` on `codex/switchyard-contract-hardening`
- Commit policy: `no commits during execution`
- Preauthorized local actions: edits to listed repository files, temporary test fixtures, local static checks, hermetic pytest runs, and `git diff --check`
- User-approval actions: external Switchyard checkout/network access, provider-billed requests, runtime deployment, branch creation, commit, push, merge, publication, destructive cleanup, or discarding unrelated changes
- Parallel ownership: none; script, tests, and CI runner share contract ownership
- Sequential fallback: complete tasks in ledger order

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `1`
- Branch: `codex/switchyard-contract-hardening`
- Base commit: `1231f42755774eb9951eb582219ae0e97ed46cb9`
- Active task(s): `none`
- Expected workspace: `plan file plus Tasks 1–4 changes only; preserve no unrelated changes`
- Next action: `none`
- Blockers: `none`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | hermetic manager tests and runner-target assertion | final focused suite `26 passed`; canonical contract suite `42 passed` |
| Task 2 | `completed` | current | `codex` | Task 1 | valid v1 plus inverted/misconfigured rejection tests | `13 passed` |
| Task 3 | `completed` | current | `codex` | Task 2 | tracked provenance artifact or explicit blocker; SSOT cleanup tests | `decision-evidence.patch` SHA-256 `70a16653f171ceb91b4f0ef5f60f679ad0ab0531262c98ae0fefc1f701ede179`; pristine `git apply --check` passed; `13 passed`; config validation passed |
| Task 4 | `completed` | current | `codex` | Task 3 | documentation inspection and full contract checks | `26 focused tests; 42 canonical tests; config/planning/diff checks passed; protected surfaces unchanged` |

## Task Breakdown

### Task 1: Make manager tests hermetic and CI-covered

**Purpose:**
- Remove tests coupled to one developer's `$HOME/.switchyard` installation.
- Put manager regression coverage behind the existing canonical contract gate.

**Task Function:**
- Normalize isolated fixtures and extend existing repository test orchestration.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: mechanical, bounded test and runner edits with no delegated benefit.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused pytest and canonical runner output.

**Specification Coverage:**
- Manager tests must not read user-local runtime files.
- Existing GitHub workflow remains the single CI job.
- Starter-kit-safe conditional script discovery remains intact.

**Required Skills:**
- `skill-test-driven-development`
- `skill-code-standards`

**Files And Symbols:**
- Inspect: `tests/test_manage_switchyard_runtime.py`
- Modify: `tests/test_manage_switchyard_runtime.py`
- Inspect: `scripts/validate_repo_contracts.py:build_subprocess_steps`
- Modify: `scripts/validate_repo_contracts.py:build_subprocess_steps`
- Verify: `tests/test_validate_repo_contracts.py`
- Verify: `.github/workflows/repo-contracts.yml`

**Dependencies:**
- Current source tree remains clean and on base commit `1231f42755774eb9951eb582219ae0e97ed46cb9`.

**Authority:**
- Preauthorized local actions: remove the two home-dependent tests, update fixture helpers, add the manager test path to non-fast pytest targets, and update runner assertions.
- Stop for: changes to workflow topology, starter-kit manifest, runtime outputs, or external Switchyard state.

**Steps:**
- [ ] Step 1: Delete the two tests that read `Path.home() / ".switchyard" / "run-probes.ps1"`.
- [ ] Step 2: Keep all remaining manager tests fixture-only; parameterize fixture ranks only where later rank tests need them.
- [ ] Step 3: Add `tests/test_manage_switchyard_runtime.py` to the existing non-fast `pytest_targets` list, filtered by file existence like current targets.
- [ ] Step 4: Update `test_build_subprocess_steps...` to assert manager tests are included for the source repo and absent safely when the manager is absent.

**Verification:**
- [ ] `py -3 -m pytest tests/test_manage_switchyard_runtime.py tests/test_validate_repo_contracts.py -q`
- [ ] `py -3 scripts/validate_repo_contracts.py --fast`
- Expected: manager tests pass without reading user-local files; source runner lists manager tests; fast runner remains green.

**Exit Criteria:**
- No test under `tests/test_manage_switchyard_runtime.py` references `Path.home()`, `$HOME`, or a real Switchyard installation.

### Task 2: Enforce v1 automatic-band and route identity

**Purpose:**
- Make policy version 1 describe the runtime contract it claims to describe.

**Task Function:**
- Add strict structural validation and failure-path regression coverage.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: local validator change with explicit tests and no delegation benefit.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: direct unit tests cover success and rejection boundaries.

**Specification Coverage:**
- For `policy_version = 1`: `efficient_profile = "normal"`, `capable_profile = "high"`, and `route_id = "auto"`.
- `validate_static_contract()` requires equal providers, distinct model IDs, and `efficient.rank < capable.rank`.
- `low` and `xhigh` cannot become automatic endpoints.
- `picker`, `confidence_threshold`, and `recent_turn_window` remain configurable.

**Required Skills:**
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/manage_switchyard_runtime.py:load_routing_policy`
- Modify: `scripts/manage_switchyard_runtime.py:load_routing_policy`
- Inspect: `scripts/manage_switchyard_runtime.py:validate_static_contract`
- Modify: `scripts/manage_switchyard_runtime.py:validate_static_contract`
- Modify: `tests/test_manage_switchyard_runtime.py:write_role`
- Verify: `repo_config/switchyard-routing.toml`
- Verify: `agents/normal.toml`, `agents/high.toml`, `agents/low.toml`, `agents/xhigh.toml`

**Dependencies:**
- Task 1 keeps manager tests hermetic.

**Authority:**
- Preauthorized local actions: validator and focused test edits only.
- Stop for: picker changes, profile renames, changes to model aliases, or changes to generated runtime output format.

**Steps:**
- [ ] Step 1: Add v1 checks for exact `normal`, `high`, and `auto` identifiers in `load_routing_policy()`.
- [ ] Step 2: Add rank-order validation in `validate_static_contract()`.
- [ ] Step 3: Give synthetic roles distinct ranks matching their meaning; add rejection tests for reversed ranks, `normal → xhigh`, `high → normal`, and non-`auto` route IDs.
- [ ] Step 4: Retain tests proving provider mismatch, duplicate model IDs, missing profiles, and low endpoint rejection.

**Verification:**
- [x] `py -3 -m pytest tests/test_manage_switchyard_runtime.py -q` — `13 passed`
- [ ] `py -3 scripts/manage_switchyard_runtime.py validate --manifest repo_config/switchyard-routing.toml`
- Expected: valid repository policy passes; every invalid band and route identity fails before runtime resolution.

**Exit Criteria:**
- No policy-v1 fixture can silently invert the efficient/capable band or route a different automatic route.

### Task 3: Establish patched-runtime provenance and remove duplicate policy state

**Purpose:**
- Make compatibility reproducible before deleting the misleading version claim.
- Restore one owner for the routing-log field contract.

**Task Function:**
- Recover or record the exact patched Switchyard source lineage, then simplify the tracked policy schema.

**Template Profile:**
- Controller-selected: `high`
- Selection basis: provenance recovery carries compatibility and reproducibility risk; use higher reasoning only if the historical checkout is available.

**Validator Profile:**
- Controller-selected: `normal`
- Selection basis: validator and fixture changes are bounded and deterministic.

**Specification Coverage:**
- Durable provenance must identify upstream repository, exact base revision, local patch artifact, patch hash, build/install command, and compatibility smoke command.
- Provenance belongs under omitted private runtime material, not starter-kit output.
- `routing_log_fields` has one owner in Python.
- `switchyard_min_version` is removed only after provenance is durable; it is not treated as a compatibility gate.

**Required Skills:**
- `skill-central-config-layer`
- `skill-code-standards`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `docs/superpowers/plans/2026-08-25-23-35-switchyard-routing-ssot-decision-evidence-plan.md`
- Inspect: historical isolated Switchyard checkout used for the completed smoke
- Create: `docs/operating_system/runtime/switchyard/decision-evidence.patch`
- Create: `docs/operating_system/runtime/switchyard/README.md`
- Modify: `repo_config/switchyard-routing.toml`
- Modify: `scripts/manage_switchyard_runtime.py:RoutingPolicy,load_routing_policy`
- Modify: `tests/test_manage_switchyard_runtime.py:write_manifest`

**Dependencies:**
- Task 2 establishes the final policy-v1 structural contract.
- The historical patched checkout or equivalent patch content must be recoverable.

**Authority:**
- Preauthorized local actions: read named local source/provenance files, create the declared private runtime provenance files, and update the manager/config/tests.
- Stop for: missing patch content, uncertain upstream lineage, network publication, binary replacement, or provider-billed smoke.

**Steps:**
- [x] Step 1: Recover the exact Switchyard base revision and local decision-evidence patch from the completed experiment context; do not infer patch content from plan prose.
- [x] Step 2: Store the patch and a short build recipe under `docs/operating_system/runtime/switchyard/`; include SHA-256 and the existing compatibility smoke command without credentials.
- [x] Step 3: Verify patch hash and build instructions against the recovered checkout.
- [x] Step 4: Remove `routing_log_fields` from the TOML, `RoutingPolicy`, allowed-key set, loader checks, and test fixture.
- [x] Step 5: Remove `switchyard_min_version` only after Step 3 passes; otherwise leave it in place and mark Task 3 blocked with the exact missing evidence.

**Verification:**
- [ ] `py -3 -m pytest tests/test_manage_switchyard_runtime.py -q`
- [x] `py -3 scripts/validate_repo_config.py` — passed
- [x] Inspect `docs/operating_system/runtime/switchyard/README.md` and recompute the patch hash — matched; pristine `git apply --check` passed
- Expected: no duplicate routing-log list remains; no unsupported config key remains; private runtime provenance is outside starter-kit copy paths.

**Exit Criteria:**
- Either provenance is reproducible and unused version/list fields are removed, or the task stops with no unsafe deletion and a recorded blocker.

### Task 4: Clarify private runtime guidance and close out

**Purpose:**
- Prevent `auto` from being mistaken for a fifth capability profile without duplicating policy ownership.

**Task Function:**
- Make one operational documentation correction and run final repository verification.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: one bounded documentation edit and deterministic checks.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: source inspection plus existing automated checks.

**Specification Coverage:**
- `runtime-adapter-procedure.md` explains `auto` as opt-in runtime routing, not a template or validator profile.
- Documentation does not claim cost savings or imply starter-kit support.
- Root `AGENTS.md`, its canonical template, planning dispatch, planning schema, and starter-kit manifest remain unchanged.

**Required Skills:**
- `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: `docs/operating_system/procedures/runtime-adapter-procedure.md`
- Modify: `docs/operating_system/procedures/runtime-adapter-procedure.md`
- Verify: `docs/operating_system/templates/agents/root-AGENTS.template.md`
- Verify: `docs/operating_system/planning/planning-dispatch.md`
- Verify: `repo_config/starter-kit-manifest.json`
- Verify: `scripts/validate_repo_contracts.py`

**Dependencies:**
- Tasks 1–3 complete, or Task 3 has an explicitly recorded blocker and no unsafe cleanup.

**Authority:**
- Preauthorized local actions: one concise runtime-adapter clarification and declared checks.
- Stop for: edits to root profile guidance, planning enums, starter-kit contents, or generated adapter files.

**Steps:**
- [x] Step 1: Add one paragraph stating `auto` is runtime routing, not a capability profile; v1 chooses only `normal` and `high`; no savings claim is established.
- [x] Step 2: Confirm no duplicate detailed policy appears in root AGENTS or planning dispatch.
- [x] Step 3: Run final focused and canonical checks — `26 passed`; canonical contract validation passed.

**Verification:**
- [x] `py -3 -m pytest tests/test_manage_switchyard_runtime.py tests/test_validate_repo_contracts.py -q` — `26 passed`
- [x] `py -3 scripts/validate_repo_contracts.py` — passed
- [x] `py -3 scripts/validate_repo_config.py` — passed
- [x] `git diff --check` — passed
- [x] `rg -n "Path\.home|routing_log_fields|switchyard_min_version|route_id|capable_first|efficient_first" scripts/manage_switchyard_runtime.py tests/test_manage_switchyard_runtime.py repo_config/switchyard-routing.toml docs/operating_system/procedures/runtime-adapter-procedure.md` — only intentional `route_id` and `capable_first` references remain
- Expected: focused tests and canonical contracts pass; no home-dependent tests remain; only intentional picker references remain; starter-kit files and generated surfaces are unchanged.

**Exit Criteria:**
- Structural contract, hermetic tests, CI coverage, provenance boundary, and private guidance agree with source truth.

## Verification

- `py -3 -m pytest tests/test_manage_switchyard_runtime.py tests/test_validate_repo_contracts.py -q`
- `py -3 scripts/validate_repo_contracts.py`
- `py -3 scripts/validate_repo_config.py`
- `git diff --check`
- Inspect `.github/workflows/repo-contracts.yml` and confirm it still invokes only `scripts/validate_repo_contracts.py`.
- Inspect starter-kit manifest and confirm no Switchyard runtime machinery is copied.

## Completion Criteria

1. Policy v1 rejects invalid endpoint bands, rank inversion, and non-`auto` route identity.
2. Manager tests are hermetic and included in the existing canonical non-fast contract run.
3. `routing_log_fields` has one owner.
4. Patched Switchyard provenance is tracked under private omitted runtime material, or Task 3 remains explicitly blocked without deleting compatibility evidence.
5. Picker behavior remains unchanged until separate calibration evidence supports a change.
6. Starter-kit, root profile guidance, planning schema, and generated adapters remain unchanged.
7. Fresh verification passes with no unrecorded scope deviation.
