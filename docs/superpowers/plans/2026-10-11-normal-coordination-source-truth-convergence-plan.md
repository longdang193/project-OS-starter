---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: active
layer: change
name: normal-coordination-source-truth-convergence
targets:
  - scripts/secretary_live_runtime.py
  - scripts/herdr_main_launcher.py
  - scripts/benchmark_secretary_architecture.py
  - tests/test_secretary_live_runtime.py
  - tests/test_secretary_benchmark.py
  - tests/test_herdr_main_launcher.py
  - tests/test_skill_chief_of_staff.py
  - tests/test_skill_project_secretary.py
  - tests/test_reconciliation.py
  - .agents/skills/skill-chief-of-staff/SKILL.md
  - .agents/skills/skill-project-secretary/SKILL.md
  - docs/operating_system/planning/planning-dispatch.md
  - docs/operating_system/procedures/runtime-adapter-procedure.md
  - docs/operating_system/runtime/runtime-surfaces.md
  - .github/workflows/runtime-contracts.yml
---

# Normal Coordination Source-Truth Convergence

## Verdict Review

Adopt the verdict's central reframing: the architecture is sufficiently
separated, and the next change is a source-truth and correctness convergence
pass rather than another coordination layer.

The governing invariant is:

> An unavailable capability blocks only the action or claim that consumes it.
> It must not prevent Secretary or CoS from understanding the request,
> returning the strongest useful answer supported by available evidence, or
> selecting another independently safe execution path.

The verdict is narrowed before execution in four ways:

1. The completed predecessor plan is historical evidence, not proof of current
   behavior. Record the discrepancy in this plan; do not reopen or rewrite the
   predecessor's task history.
2. Semantic result, resource settlement, and observability completeness remain
   independent facts. A normal result may survive cleanup quarantine, and
   missing optional telemetry must not erase it.
3. Assignment and attempt identities are correlated by field. Distinct valid
   values are expected; conflicting values for the same field are ambiguous.
4. GitHub branch protection and the private launcher-adapter boundary are
   follow-up work, not prerequisites for this convergence pass. This plan
   leaves remote administration and broad launcher refactoring unchanged.

### Source-truth record

| Evidence | Recorded fact |
| --- | --- |
| Historical predecessor | `docs/superpowers/plans/2026-10-11-19-46-normal-coordination-result-and-resource-convergence-plan.md` completed at `88a46f25ba8d9ffe80c5f60823911ef3a6c41158` |
| Current source baseline | `HEAD = origin/main = 0bba4777df5f5a4ad5d6d4946a2b1488eb1da34f` |
| Inconsistent claims | `_observe_submitted_codex` can synthesize a `herdr://` reference from idle/output metadata; `_normalize_invocation_outcome` pools assignment and attempt identities; `_close_herdr_workspace` treats close success as settled without an absence proof; `run_contract_benchmark` emits deterministic six-scenario pairs rather than live measurements |
| Current correction | This plan is the corrective source for the discrepancies; the completed predecessor remains unchanged historical evidence |

## Goal

Make direct Secretary/CoS semantic coordination useful without Herdr, while
allowing a managed Herdr-backed `secretary_live_runtime.py run` to require
Herdr for that managed execution path. Make ordinary managed results report a
useful, attributable semantic result whenever one is actually captured, keep
strict probe claims strict, and make resource, cleanup, policy, benchmark, and
plan evidence agree with executable behavior on the exact Git revision under
test.

## Implementation Outcomes

### Truthful normal results and correlation

Normal `run` distinguishes captured semantic content or a verified retrievable
result from idle state, output counts, output hashes, sequence numbers, exit
codes, cleanup success, and synthetic references. A reference is valid only
when it is attributable to the current invocation/assignment, a named resolver
retrieves its semantic payload before publication, and the payload either
remains retrievable after cleanup or is copied into caller-owned output before
the source resource is retired. Valid `assignment_id` and `attempt_id` values
are checked independently across normal, probe, and sanitizer paths; provider
economics attribution remains a separate proof decision.

### Monotonic and recoverable resource facts

Cleanup evidence for the same resource can advance from provisional unknown to
verified removal, but cannot be downgraded by a weaker observation. Exceptions
after resource acquisition preserve additive `owned_resources` evidence and
`recovery_required`; these fields are invocation evidence, not a registry or
new lifecycle schema. Workspace closure is settled only after the existing
authoritative retirement evidence or one bounded verification proves that
owned panes and processes are gone.

### Action-scoped coordination policy

CoS advisory reasoning can use available repository evidence while stating
freshness or uncertainty. Exact snapshot audits, acceptance, mutation, and
merge claims require exact repository and commit binding. Secretary remains an
optional attention layer and does not gain acceptance or lifecycle authority.

### Honest contract and measurement surfaces

Deterministic benchmark rows remain contract fixtures, but no longer imply
live latency, token, provider, or resource measurements. Explicit `contract`
and `measure` modes keep those concerns separate. Existing production
functions are exercised with fake external boundaries when measurement is
needed, and one CI job owns the Secretary benchmark test and generator.

### Reconciled durable documentation

Canonical skills, runtime documentation, tests, generated adapter views, the
completed predecessor plan, and the final verification record describe the
same behavior. No new receipt schema, runtime database, lifecycle registry,
sweeper, retry manager, or coordination authority is introduced.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-executing-plans`, `skill-using-git-worktrees`, `skill-systematic-debugging`, `skill-code-standards`, `skill-backend-verification`, `skill-test-driven-development`, `skill-verification-before-completion`
- Isolation: `required clean task-specific worktree from base commit`
- Commit policy: `proof-gated local checkpoint commits after Tasks 2 and 3, plus a final verified checkpoint; no push or merge`
- Preauthorized local actions: `read and edit declared repository files, run declared local tests and validators, regenerate declared adapter views, and perform bounded read-only capability checks when already available`
- User-approval actions: `push, merge, GitHub ruleset or branch-protection changes, authentication, provider installation, external writes, destructive recovery, discard, and unrelated cleanup`
- Parallel ownership: `none; runtime result/resource changes and their tests share ordering dependencies`
- Sequential fallback: `Task 1 → Task 2 → Task 3 → Task 4 → Task 5 → final verification`

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/normal-coordination-source-truth-convergence`
- Base commit: `0bba4777df5f5a4ad5d6d4946a2b1488eb1da34f` (`HEAD` = `origin/main`)
- Expected workspace: `clean task-specific worktree created from the base commit; preserve unrelated files outside the worktree`
- Next action: `reconcile Task 4 canonical coordination policy and generated surfaces`
- Blockers: `none`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | task-specific | `lead controller` | none | exact revision, baseline tests, current-plan source-truth record | `HEAD=origin/main=0bba4777df5f5a4ad5d6d4946a2b1488eb1da34f`; focused baseline `340 passed`; current generator returns `360` rows for `30` iterations (`6 scenarios × 2 architectures × 30`); no exact-shape readers for `secretary-invocation-v1` found outside the producer/tests; additive `owned_resources[]` and `recovery_required` are therefore consumer-compatible |
| Task 2 | `completed` | task-specific | `lead controller` | Task 1 | semantic-result and field-aware identity matrix; local checkpoint | `86 passed` in `tests/test_secretary_live_runtime.py tests/test_secretary_evidence_adapter.py tests/test_secretary_receipts.py`; synthetic Herdr references removed; long semantic content retained; same-field conflicts are ambiguous |
| Task 3 | `completed` | task-specific | `lead controller` | Task 2 | cleanup precedence, exception envelope, workspace-settlement matrix; local checkpoint | `287 passed` in `tests/test_secretary_live_runtime.py tests/test_herdr_main_launcher.py tests/test_reconciliation.py`; verified workspace close required for settlement; exception paths retain `owned_resources` and `recovery_required` |
| Task 4 | `active` | task-specific | `lead controller` | Tasks 2–3 | canonical policy tests and generated-surface drift check | pending |
| Task 5 | `pending` | task-specific | `unresolved` | Tasks 2–4 | separate contract/measure modes, consolidated CI, final checkpoint | pending |

## Task Breakdown

### Task 1: Reconcile source truth and historical plan claims

**Purpose:**
- Establish the exact source revision, current executable behavior, and
  predecessor-plan discrepancies before any behavioral edit.

**Task Function:**
- Build a source-first baseline and record the historical-plan correction.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: `bounded repository inspection with no delegation benefit`

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: `lead controller owns the baseline evidence`

**Specification Coverage:**
- Verdict P0 source reconciliation; Git, tests, and exact revision outrank
  completed-plan prose; unrelated workspace state is preserved.

**Required Skills:**
- `skill-code-standards`, `skill-verification-before-completion`

**Files And Symbols:**
- Inspect read-only: `docs/superpowers/plans/2026-10-11-19-46-normal-coordination-result-and-resource-convergence-plan.md` and its completion commit `88a46f25ba8d9ffe80c5f60823911ef3a6c41158`
- Inspect: `scripts/secretary_live_runtime.py::_observe_submitted_codex`, `_normalize_invocation_outcome`, `_close_herdr_workspace`, `run_normal`, `run_probe`
- Inspect consumers: `secretary-invocation-v1`, `resource`, `recovery_required`, and any exact-shape readers across `scripts`, `tests`, and maintained docs
- Inspect: `scripts/secretary_evidence_adapter.py::_identity`, `_join_provider_usage` only to confirm provider attribution remains a separate decision
- Inspect: `scripts/benchmark_secretary_architecture.py::ContractMetric`, `run_contract_benchmark`
- Inspect: focused Secretary, launcher, CoS, Project Secretary, and reconciliation tests
- Verify: `.github/workflows/runtime-contracts.yml` and declared canonical/generated boundaries

**Dependencies:**
- None. Preserve the clean checkout and do not stage or rewrite unrelated files.

**Authority:**
- Preauthorized local actions: `create the declared clean worktree/branch, read declared sources and history, run the baseline focused suite, count deterministic benchmark rows, and record the bounded source-truth note in this plan`
- Stop for: `the checked-out revision changes, the workspace becomes dirty for an unrelated reason, or the required behavior belongs to a different active owner`

**Steps:**
- [x] Step 1: Create the clean task-specific worktree and branch from `0bba4777df5f5a4ad5d6d4946a2b1488eb1da34f`; confirm its `HEAD`, branch, and clean-state assumptions.
- [x] Step 2: Run the focused baseline suite and inspect the current normal result, identity, cleanup, CoS wording, and benchmark assertions.
- [x] Step 3: Confirm the deterministic generator's actual row count and provenance; do not preserve stale claims such as `780` when the current implementation produces `6 × 2 × 30 = 360` rows.
- [x] Step 4: Record in this plan the predecessor path, completion SHA, inconsistent claims, exact source symbols, and disposition that this plan's proof supersedes those claims; leave the predecessor unchanged.
- [x] Step 5: Record whether invocation consumers tolerate additive `owned_resources[]` and `recovery_required` fields before Task 3 changes the output contract.

**Verification:**
- [x] `git rev-parse HEAD origin/main` shows the planned exact revision relationship.
- [x] `py -B -m pytest -q tests/test_secretary_live_runtime.py tests/test_secretary_evidence_adapter.py tests/test_secretary_benchmark.py tests/test_skill_chief_of_staff.py tests/test_skill_project_secretary.py tests/test_herdr_main_launcher.py tests/test_reconciliation.py`
- Expected: the baseline is recorded, the predecessor note is explicit, and no unrelated file changes are introduced.

**Exit Criteria:**
- The clean worktree/branch exists, the implementation boundary and historical discrepancy are recorded in this plan against an exact revision, invocation consumers are inventoried, and the focused baseline is still green or any pre-existing failure is documented.

### Task 2: Make normal semantic results and identity correlation truthful

**Purpose:**
- Ensure normal coordination reports only captured, attributable semantic
  results and accepts distinct valid assignment/attempt identities.

**Task Function:**
- Harden the existing result normalizer and its evidence join points without adding a result service or schema.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: `shared runtime correctness is high-impact but localized to existing production functions`

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: `production-function regression tests cover the contract`

**Specification Coverage:**
- Verdict P0 semantic-result rule and field-by-field correlation; P1 graceful
  degradation before dispatch; no duplicate retry after ambiguous delivery.

**Required Skills:**
- `skill-backend-verification`, `skill-test-driven-development`, `skill-code-standards`

**Files And Symbols:**
- Modify: `scripts/secretary_live_runtime.py::_observe_submitted_codex` so idle/output count/hash/sequence never creates a semantic result reference
- Modify: `scripts/secretary_live_runtime.py::_normalize_invocation_outcome`, `_binding_matches`, `_launcher_facts_match`, `sanitize_launcher_result`, `run_normal`, `run_probe`
- Add or refine one small shared field-aware correlation helper in `scripts/secretary_live_runtime.py` used by normal, probe, and sanitizer inputs; do not share the result-validity decision with provider economics attribution
- Verify and modify only required expectations in `tests/test_secretary_live_runtime.py`; run `tests/test_secretary_evidence_adapter.py` as a regression suite without changing its provider proof policy unless Task 1 finds a direct field-correlation defect

**Dependencies:**
- Task 1 source inventory and reconciliation note complete.

**Authority:**
- Preauthorized local actions: `edit the declared runtime functions and focused tests using fake subprocess/Herdr boundaries only, then create the declared local checkpoint commit after proof passes`
- Stop for: `captured result ownership requires a new durable schema, raw transport output would need to be persisted, or a retry/dispatch authority must be redesigned`

**Steps:**
- [x] Step 1: Add failing cases for idle plus nonempty output, output hash, sequence number, exit code, cleanup success, and synthetic references with no semantic payload; each must yield `result.state=unavailable`.
- [x] Step 2: Define a verified retrievable reference as current-invocation attributable, resolved by a named resolver, successfully retrieved before publication, and either resolvable after cleanup or materialized into caller-owned output before cleanup. An ephemeral pane/agent reference that is deleted is not final evidence.
- [x] Step 3: Add passing cases for actual correlated content or a verified retrievable result reference; preserve failed-but-reported results independently from execution state.
- [x] Step 4: Keep semantic content separate from the existing 4096-character metadata guard; long valid content must be materialized in caller-owned output or fail explicitly with a reason, never silently become unavailable.
- [x] Step 5: Validate `assignment_id` against `assignment_id` and `attempt_id` against `attempt_id`; accept distinct valid values and mark same-field conflicts ambiguous.
- [x] Step 6: Assert ambiguous delivery never authorizes a second launch and keep provider economics attribution as a separate receipt/session/coverage decision.
- [x] Step 7: Keep strict probe readiness dependent on its required receipt/telemetry evidence without allowing probe-only blocking to change normal semantic results.

**Verification:**
- [x] `py -B -m pytest -q tests/test_secretary_live_runtime.py tests/test_secretary_evidence_adapter.py tests/test_secretary_receipts.py`
- Expected: normal results are reported only from semantic evidence, distinct valid IDs pass, same-field conflicts are ambiguous, and missing optional receipts/provider telemetry do not erase a normal result.

**Exit Criteria:**
- The normal path no longer manufactures semantic completion from runtime observation, verified references survive cleanup or are materialized before cleanup, long semantic content is handled explicitly, and normal/probe/sanitizer identity consumers use the same field-aware rule without coupling provider economics validity to result validity.

### Task 3: Make cleanup evidence monotonic and exception-safe

**Purpose:**
- Preserve recovery information after partial failure and settle resources only
  when authoritative removal evidence exists.

**Task Function:**
- Reconcile resource evidence at the existing finalization boundaries and prove workspace closure with bounded evidence.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: `resource safety requires direct boundary proof and no new lifecycle subsystem`

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: `failure-path and cleanup tests use fake Herdr boundaries`

**Specification Coverage:**
- Verdict P0 monotonic cleanup, exception recovery envelope, and workspace
  closure proof; P1 local ownership and no cleanup daemon/sweeper.

**Required Skills:**
- `skill-backend-verification`, `skill-test-driven-development`, `skill-code-standards`

**Files And Symbols:**
- Modify: `scripts/secretary_live_runtime.py::_close_herdr_workspace`, `_prepare_herdr_target`, `_release_codex_agent`, `_normalize_invocation_outcome`, `run_normal`, `run_probe`
- Inspect for reusable proof: `scripts/herdr_main_launcher.py::_terminate_codex_lane`, `retire_lane`, `retire_settled_lane`
- Add or refine one small pure resource-evidence reducer in `scripts/secretary_live_runtime.py` keyed by resource identity, evidence authority, and observation time; it aggregates authoritative launcher/Herdr retirement facts and does not inspect or retire processes itself
- Modify: `tests/test_secretary_live_runtime.py` and the narrowly affected launcher tests in `tests/test_herdr_main_launcher.py`

**Dependencies:**
- Task 2 result and identity fields are stable.

**Authority:**
- Preauthorized local actions: `edit declared cleanup/finalization functions and tests, reuse existing authoritative launcher/Herdr retirement evidence, perform bounded read-only verification when the existing capability is available, and create the declared local checkpoint commit after proof passes`
- Stop for: `workspace closure cannot be proven without a new daemon/registry, ownership would cross into unrelated resources, or cleanup would require destructive recovery approval`

**Steps:**
- [x] Step 1: Define the same-resource precedence as `verified removed > verified quarantined/preserved > provisional unknown > absent`, with explicit authoritative-conflict handling.
- [x] Step 2: Ensure later verified removal can upgrade earlier unknown evidence and cannot be downgraded by a weaker launcher observation.
- [x] Step 3: Treat `owned_resources[]` as additive invocation evidence, not a registry, durable ownership authority, or new lifecycle state machine. Retain `secretary-invocation-v1` when consumers tolerate additive fields; otherwise update exact-shape consumers explicitly before publication.
- [x] Step 4: Make every exception after workspace/agent acquisition retain owned resource identities, current state, and `recovery_required`; preserve `result` independently. Cover both `cleanup succeeds → settled/recovery_required=false` and `cleanup unproven → quarantined/recovery_required=true`.
- [x] Step 5: Reuse authoritative launcher/Herdr retirement evidence for pane/process/descendant proof. Secretary only reduces evidence; it does not become a second process-lifecycle owner.
- [x] Step 6: Prove workspace closure either from an existing Herdr guarantee or with one bounded post-close check for the captured workspace/pane/process identities; return quarantined/unresolved when proof is unavailable.
- [x] Step 7: Verify agent, pane, workspace, and process ownership remain local to the creating owner; do not add a global resource manager or retry permission after ambiguous delivery.

**Verification:**
- [x] `py -B -m pytest -q tests/test_secretary_live_runtime.py tests/test_herdr_main_launcher.py tests/test_reconciliation.py`
- Expected: unknown→removed converges to settled, close failure is quarantined, exceptions preserve recovery identity, and result content remains available after cleanup.

**Exit Criteria:**
- Resource state is monotonic and truthful for normal and probe paths, with no loss of recovery information, no false settlement, no duplicated retirement logic, and no new lifecycle schema.

### Task 4: Reconcile canonical coordination policy and generated surfaces

**Purpose:**
- Make action-scoped capability requirements and Secretary/CoS boundaries agree
  across canonical skills, operating-system documentation, tests, and generated
  adapter views.

**Task Function:**
- Edit canonical policy once, regenerate derived agent surfaces, and remove only contradictory wording.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: `canonical-source edit and deterministic adapter synchronization are straightforward`

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: `skill contract tests plus generated drift validation`

**Specification Coverage:**
- Verdict P0 CoS advisory contradiction; P1 frozen Secretary–CoS–Worker model,
  pre-dispatch graceful degradation, decision-delta communication, and
  Git/Plan/GitHub durable truth.

**Required Skills:**
- `skill-code-standards`

**Files And Symbols:**
- Modify canonical sources: `.agents/skills/skill-chief-of-staff/SKILL.md`, `.agents/skills/skill-project-secretary/SKILL.md`
- Modify only when source inspection finds stale contract wording: `docs/operating_system/planning/planning-dispatch.md`, `docs/operating_system/procedures/runtime-adapter-procedure.md`, `docs/operating_system/runtime/runtime-surfaces.md`
- Regenerate: `generated_agents/codex/skills/skill-chief-of-staff/SKILL.md`, `generated_agents/codex/skills/skill-project-secretary/SKILL.md`, `generated_agents/claude/skills/skill-chief-of-staff/SKILL.md`, `generated_agents/claude/skills/skill-project-secretary/SKILL.md`, `generated_agents/antigravity/skills/skill-chief-of-staff/SKILL.md`, `generated_agents/antigravity/skills/skill-project-secretary/SKILL.md`
- Modify: `tests/test_skill_chief_of_staff.py`, `tests/test_skill_project_secretary.py`

**Dependencies:**
- Tasks 2–3 establish the executable result/resource semantics that the policy must describe.

**Authority:**
- Preauthorized local actions: `edit canonical skill/docs sources, regenerate declared generated views, and run contract/drift checks`
- Stop for: `a generated file requires direct editing, wording would grant Secretary/CoS acceptance or lifecycle authority, or a new durable coordination state is proposed`

**Steps:**
- [ ] Step 1: Change repository snapshot binding so advisory reasoning may state uncertainty/freshness without exact SHA, while exact audit, acceptance, mutation, and merge claims retain exact binding.
- [ ] Step 2: Reconcile wording for optional receipts, provider telemetry, Herdr, runtime sessions, and event hints so they remain evidence/capability gates only for claims that consume them.
- [ ] Step 3: Preserve the existing Secretary→CoS→Worker decision boundary and decision-delta handoff; do not add mesh communication, full-history handoffs, or routine Worker→Secretary progress.
- [ ] Step 4: Regenerate all declared agent views from canonical sources and update only tests that assert the corrected contract.

**Verification:**
- [ ] `py -B -m pytest -q tests/test_skill_chief_of_staff.py tests/test_skill_project_secretary.py`
- [ ] `py -B scripts/sync_agent_adapters.py --all-platforms --check`
- Expected: canonical and generated wording agree; advisory reasoning remains useful without exact SHA, while exact claims remain strict.

**Exit Criteria:**
- No maintained policy surface contradicts the action-scoped capability invariant or the durable-truth ownership model.

### Task 5: Convert the benchmark into an honest fixture and CI contract

**Purpose:**
- Preserve deterministic correctness coverage while preventing benchmark output
  from claiming live performance or runtime evidence it did not collect.

**Task Function:**
- Instrument existing production boundaries with fake external edges and label unavailable measurements explicitly.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: `bounded measurement/CI change with explicit performance evidence requirements`

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: `benchmark assertions and final verification own measurement validity`

**Specification Coverage:**
- Verdict P1 benchmark fixture correction, production-path instrumentation, CI
  coverage, sample-size-aware metrics, and no unsupported optimization claim.

**Required Skills:**
- `skill-backend-verification`, `skill-performance-optimization`, `skill-code-standards`

**Files And Symbols:**
- Modify: `scripts/benchmark_secretary_architecture.py::ContractMetric`, `_metric`, `_target_metric`, `_baseline_metric`, `run_contract_benchmark`, and CLI output
- Modify: `tests/test_secretary_benchmark.py`
- Modify: `.github/workflows/runtime-contracts.yml` only to consolidate ownership: keep platform-sensitive Secretary runtime tests in `runtime`, move `tests/test_secretary_benchmark.py` to the existing `benchmark` job beside the generator, and do not add a workflow or duplicate the test
- Inspect: `tests/test_validate_repo_contracts.py::test_secretary_contract_suites_have_one_workflow_owner` and workflow-ownership validation
- Verify: `scripts/secretary_live_runtime.py::run_normal`, `_normalize_invocation_outcome`, and existing launcher boundaries are the source of measured counters

**Dependencies:**
- Tasks 2–4 complete so result/resource/policy labels are stable.

**Authority:**
- Preauthorized local actions: `edit the declared benchmark/test/CI surfaces and run deterministic or bounded local production-path measurements with fake external boundaries, then create the final local checkpoint after proof passes`
- Stop for: `a new telemetry database, provider write, live credential requirement, statistical claim from insufficient samples, or unrelated CI change`

**Steps:**
- [ ] Step 1: Add explicit `contract` and `measure` CLI modes. `contract` emits deterministic expected architecture cases; `measure` exercises production functions with fake external boundaries and reports measured/unavailable/not-attempted evidence.
- [ ] Step 2: Keep deterministic baseline/target scenarios as a contract fixture and label every row `deterministic-fake`, `live=false`, with unavailable latency/token fields; do not call this an empirical before/after improvement without running both exact historical and candidate SHAs through the same harness.
- [ ] Step 3: Add production-path instrumentation for launches, commands, provider queries, subprocesses, messages, retries, duplicate effects, and remaining resources without hardcoding those values in fixture rows.
- [ ] Step 4: Add the normal/probe/resource matrix to benchmark assertions, including result preservation under missing optional evidence and no duplicate retry after ambiguity.
- [ ] Step 5: Emit measured, unavailable, and not-attempted states with provenance and sample count; emit percentiles only when the declared sample threshold is met.
- [ ] Step 6: Move `tests/test_secretary_benchmark.py` from the two-OS `runtime` job to the existing Ubuntu `benchmark` job, keep one workflow owner, and preserve no-live-capability execution.

**Verification:**
- [ ] `py -B -m pytest -q tests/test_secretary_benchmark.py tests/test_secretary_live_runtime.py tests/test_secretary_evidence_adapter.py tests/test_validate_repo_contracts.py`
- [ ] `py -B scripts/benchmark_secretary_architecture.py contract 30`
- [ ] `py -B scripts/benchmark_secretary_architecture.py measure`
- Expected: contract rows remain honest fixtures; measured rows identify their production boundary and sample support; no latency/token claim appears without evidence; exactly one workflow owns the Secretary benchmark test.

**Exit Criteria:**
- CI protects correctness assertions rather than only JSON generation, benchmark output cannot be mistaken for live performance evidence, and no historical performance improvement is claimed without same-harness SHA comparison.

## Verification

Final artifact verification runs only after all tasks are complete:

- [ ] `py -B -m pytest -q tests/test_secretary_live_runtime.py tests/test_secretary_evidence_adapter.py tests/test_secretary_benchmark.py tests/test_skill_chief_of_staff.py tests/test_skill_project_secretary.py tests/test_herdr_main_launcher.py tests/test_reconciliation.py`
- [ ] `py -B scripts/validate_repo_contracts.py --repo-root . --fast`
- [ ] `py -B scripts/validate_planning_lifecycle.py --repo-root .`
- [ ] `py -B scripts/sync_agent_adapters.py --all-platforms --check`
- [ ] `py -B scripts/validate_agent_runtime_drift.py --all-platforms --skip-deploy-check`
- [ ] `git diff --check`
- [ ] Confirm `git status --short --untracked-files=all` contains only declared plan/task changes and no unrelated mutation.
- [ ] Confirm every CI result used for acceptance is bound to the exact candidate head SHA; stale or unavailable remote evidence is recorded as such.
- [ ] Confirm proof-gated local checkpoint commits exist after Tasks 2 and 3 and at final verification, with no push or merge performed by this plan.

### Required deterministic probe matrix

- [ ] Idle plus output but no semantic response → `result=unavailable`.
- [ ] Captured semantic response → `result=reported`.
- [ ] Different valid assignment/attempt IDs → accepted.
- [ ] Conflicting values for one identity field → rejected or `ambiguous`.
- [ ] Cleanup unknown followed by authoritative removal → `settled`.
- [ ] Workspace close failure → `quarantined` with recovery required.
- [ ] Exception after workspace creation, cleanup succeeds → `execution=failed`, `result=unavailable`, `resource=settled`, `recovery_required=false`.
- [ ] Exception after workspace creation, cleanup unproven → `execution=failed`, `result=unavailable`, `resource=quarantined`, resource identity retained, `recovery_required=true`.
- [ ] Provider or structured receipt unavailable → normal reasoning/result unaffected.
- [ ] Ambiguous delivery → exactly one launch and reconciliation before retry.
- [ ] Captured result followed by cleanup → result remains accessible.
- [ ] Direct advisory CoS without exact SHA → useful answer with uncertainty.
- [ ] Exact audit without exact SHA → blocked or explicitly qualified.

### Required bounded live proof

When the already configured managed capability is available, run one disposable
Herdr-backed Secretary request with a unique nonce. Direct Secretary/CoS
semantic reasoning remains available even when this managed path is not:

```text
Return exactly SECRETARY_PROBE_<nonce>.
Do not modify files.
Do not create another Worker.
```

Require the actual nonce, no repository mutation, no duplicate attempt, and
capture `workspace_id`, `pane_id`, `agent_name`, and owned process identity where
available before cleanup. Query those same identities afterward and require
them to be absent/retired, or explicitly quarantined with recovery evidence;
generic disappearance of unrelated resources is not sufficient. Require
result survival after cleanup. 
Run strict receipt qualification separately. If strict probing returns
`BLOCKED_CAPABILITY` while normal invocation returns the semantic result, record
that as the expected graceful-degradation outcome. If Herdr/provider/receipt
capability is unavailable, preserve the normal source/test proof and record the
live gate as unavailable rather than fabricating a result.

## Completion Criteria

The plan is complete only when:

1. The exact candidate revision, production behavior, tests, benchmark output,
   canonical guidance, generated views, and this plan's source-truth record
   agree; the historical completed predecessor remains unchanged.
2. Direct Secretary/CoS semantic coordination does not require Herdr. A
   managed Herdr-backed invocation may require Herdr, but its unavailability
   constrains only that managed execution path and does not globally block
   reasoning or alternative safe routing.
3. Strict probe claims remain blocked when their required evidence is absent.
4. Identity correlation is field-aware and ambiguity-safe across all declared
   normal/probe/sanitizer consumers; provider economics attribution remains a
   separate proof decision.
5. Cleanup/resource evidence is monotonic, exception-safe, ownership-bound,
   and explicit about quarantine; Secretary reduces authoritative retirement
   evidence rather than owning a second lifecycle implementation.
6. CoS/Secretary policy distinguishes advisory reasoning from exact snapshot,
   acceptance, mutation, and merge claims.
7. Deterministic `contract` fixtures and `measure` production-path output are
   structurally separated; CI has exactly one owner for the benchmark test and
   no historical improvement claim is made without same-harness SHA evidence.
8. Canonical skill edits are synchronized to generated views and all declared
   validators pass.
9. The bounded live gate is either fresh and passing or its precise unavailable
   capability and preserved local proof are recorded.
10. No unrelated dirty/untracked workspace file is staged, rewritten, deleted,
    or treated as evidence for this plan.

## Non-Goals and Stop Conditions

- No GitHub branch-protection or ruleset mutation; handle that as a separate
  administrative change after this plan has source/test proof.
- No new receipt schema, lifecycle database, resource registry, cleanup daemon,
  generic retry manager, event bus, CoS CLI, or CoS-to-CoS communication.
- No broad refactor of private Herdr launcher helpers; stabilize the current
  behavior first and schedule adapter decoupling separately if measurements show
  it is still material.
- No interpretation that managed Herdr CLI availability is required for the
  Secretary or CoS semantic roles themselves.
- No provider installation, authentication, data-access widening, external
  writes, force push, merge, or destructive recovery.
- Stop and revise if the implementation requires a durable schema migration,
  moves acceptance or lifecycle authority to Secretary, CoS, middleware, or
  reporting, or cannot prove resource ownership without a new global owner.

## Rollback and Risk

Keep each runtime change localized to the existing Secretary/Herdr boundary and
retain the old strict probe contract while normal semantics are corrected. If a
task weakens identity or resource proof, revert that task's local edits and keep
the new regression test failing as the guard. If live capability is absent,
record the unavailable evidence and rely on deterministic production-function
tests plus source-first reconciliation; do not convert missing capability into
false success or false failure.

