---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
layer: change
name: coordination-simplification-and-evidence-boundaries
targets:
  - scripts/project_os_runtime/attempt.py
  - scripts/project_os_runtime/results.py
  - scripts/project_os_runtime/acceptance.py
  - scripts/project_os_runtime/plan_preparation.py
  - scripts/project_os_runtime/reconciliation.py
  - scripts/project_os_runtime/lane.py
  - scripts/project_os_runtime/secretary_adapter.py
  - scripts/project_os_runtime/secretary_receipts.py
  - scripts/project_os_runtime/secretary_evidence.py
  - scripts/secretary_live_runtime.py
  - scripts/secretary_live_pilot.py
  - scripts/herdr_main_launcher.py
  - scripts/herdr_parallel_dispatch.py
  - scripts/dcode_project.py
  - scripts/benchmark_completion_monitoring.py
  - tests/test_benchmark_completion_monitoring.py
  - tests/test_project_os_runtime.py
  - tests/test_plan_preparation.py
  - tests/test_evidence_release.py
  - tests/test_reconciliation.py
  - tests/test_project_os_reconciliation.py
  - tests/test_secretary_adapter.py
  - tests/test_secretary_receipts.py
  - tests/test_secretary_evidence.py
  - tests/test_secretary_live_runtime.py
  - tests/test_secretary_live_pilot.py
  - tests/test_herdr_main_launcher.py
  - tests/test_herdr_parallel_dispatch.py
  - tests/test_deepagents_result_contract.py
  - tests/test_dcode_project.py
  - tests/test_skill_project_secretary.py
  - tests/test_skill_chief_of_staff.py
  - tests/test_sync_agent_adapters.py
  - .agents/skills/skill-project-secretary/SKILL.md
  - .agents/skills/skill-chief-of-staff/SKILL.md
  - docs/architecture.md
  - docs/usage.md
  - docs/operating_system/planning/planning-dispatch.md
  - docs/operating_system/runtime/runtime-surfaces.md
  - docs/operating_system/tooling/runtime-tool-resolution.md
  - docs/operating_system/procedures/runtime-adapter-procedure.md
  - docs/superpowers/plans/2026-10-16-coordination-simplification-and-evidence-boundaries-plan.md
  - generated_agents/
---

# Coordination Simplification And Evidence Boundaries

## Review Of The Supplied Recommendation

The recommendation is directionally correct and should be treated as a
sequenced simplification program, not as permission to redesign or remove the
Secretary–CoS–Worker hierarchy. The repository already states the intended
organizational boundary: direct execution remains valid, Secretary is
optional, CoS owns coordination and acceptance, Workers own bounded execution,
and runtime evidence is not durable workflow truth.

The following corrections make the recommendation implementation-ready:

1. **Do not introduce duplicate contract systems.** `TaskResult` already has a
   validated `dcode-project.task-result.v1` schema in
   `scripts/project_os_runtime/results.py`; `TaskContract` is already
   represented by normalized plan/lane inputs in
   `scripts/project_os_runtime/plan_preparation.py` and `lane.py`;
   `execution_binding_digest()` and `same_attempt_binding()` already provide
   important binding primitives in `scripts/project_os_runtime/attempt.py`.
   The first implementation should consolidate those primitives rather than
   add a parallel task database, receipt schema, or identity registry.
2. **Do not enable the managed Secretary path by flipping its capability flag.**
   `run_normal()` is intentionally capability-blocked while `run_probe()` is a
   qualification path. Normal in-session Secretary reasoning must remain
   usable without Herdr, provider telemetry, or live receipts; managed runtime
   changes require separate live A/B evidence.
3. **Treat acceptance and cleanup as separate proofs.**
   `evaluate_acceptance()` already produces an acceptance decision and proof,
   while `release_authorized_evidence()`, plan transitions, and attempt
   settlement protect different resources. The work should centralize proof
   validation and remove duplicated semantic checks without allowing cleanup
   failures to rewrite task correctness.
4. **Use receipt-first observation as a measured optimization.** The launcher
   already has structured task-result and receipt observation paths. The change
   should reduce redundant polling only after a baseline identifies the
   recurring cost and after stale, mismatched, timeout, and cleanup failure
   paths remain fail-closed.
5. **Keep plan parsing and full-plan revision checks authoritative.** Normalize
   task inputs once and require explicit resolved plan identity at governed
   activation, but retain whole-plan revision checks for atomic ledger writes.
   Do not create an independently maintained task database.
6. **Defer broad lifecycle renaming.** The current architecture intentionally
   distinguishes admission, runtime settlement, acceptance, and retention.
   Reduce aliases only where an inventory proves they duplicate one fact; do
   not replace the existing safety vocabulary with a second lifecycle model in
   this plan.

## Goal

Make the smallest safe coordination structure the default while reducing
duplicated identity, semantic-result, acceptance, and observation logic. The
implementation must preserve the existing trust boundaries and fail-closed
behavior, and it must not claim operational benefit until equivalent real
workloads provide fresh measurements.

The governing rule is:

> No changed cross-boundary decision means no cross-boundary message.

The desired steady state is:

```text
simple work                  → direct executor
one bounded substantial task → Worker → TaskResult
multiple independent lanes   → CoS → TaskContract → Worker
cross-workstream attention   → Secretary → relevant CoS
acceptance                   → one CoS acceptance proof
runtime cleanup              → one resource/settlement proof
```

## Implementation Outcomes

### Progressive coordination remains the canonical routing policy

The Secretary and CoS documentation, tests, and generated adapters describe
progressive escalation without requiring a Secretary hop for normal work or a
CoS hop merely because a Worker exists. Managed Secretary runtime remains an
experimental qualification surface; normal in-session Secretary behavior does
not depend on its receipts, provider identity, Herdr transport, or economics
pilot.

### Existing semantic contracts have one owner each

The implementation reuses and tightens the existing normalized plan/lane
contract, `dcode-project.task-result.v1`, attempt binding/digest primitives,
CoS acceptance proof, and runtime settlement/resource evidence. Downstream
consumers no longer reinterpret terminal text, pane content, provider aliases,
or telemetry as semantic completion or acceptance.

### Acceptance, settlement, and retention are independently consumable

`evaluate_acceptance()` remains the owner of semantic acceptance. Plan
advancement consumes its validated proof plus dependency/revision facts.
Evidence release consumes the same proof plus resource, retention, and exact
artifact identity facts. Runtime settlement blocks reuse and cleanup claims
without retroactively changing task acceptance unless cleanup is an explicit
task condition.

### Observation cost is reduced only when evidence admits it

The launcher uses Worker-owned structured results and completion receipts as
the normal success signal, performs one bounded final diagnostic, and uses
process/pane inspection only for missing attribution, timeout, stall, or
cleanup uncertainty. Fresh evidence records subprocess count, completion
detection delay, cleanup correctness, unresolved-resource rate, false
blockers, duplicate execution, and accepted-outcome latency.

### Governed activation and continuation consume resolved identity

Plan-bound execution receives explicit plan path, expected plan revision, and
task ID before activation. Runtime grants stay immutable for an attempt;
redispatch occurs only for timeout, authority/scope changes, immutable base
drift, accepted checkpoint continuation, or a material resource request. Plan
estimate changes alone do not force retirement and redispatch.

### Documentation and generated surfaces have one coordination contract

Role ownership, activation criteria, allowed communication edges, escalation,
and truth hierarchy have one canonical documentation owner. Secretary, CoS,
runtime, and usage docs link to or specialize that contract rather than
restate competing versions. Generated agent surfaces are refreshed only from
canonical sources through `scripts/sync_agent_adapters.py`.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-executing-plans`, `skill-project-secretary`, `skill-chief-of-staff`, `skill-backend-verification`, `skill-performance-optimization`, `skill-code-standards`, `skill-plan-document-reviewer`, `skill-verification-before-completion`
- Isolation: `fresh dedicated task-owned worktree from freshly fetched origin/main at the exact activation SHA; create the task-specific feature branch in that worktree; preserve the original checkout untouched`
- Commit policy: `verified task-boundary checkpoint commits are preauthorized after task-local proof and ledger update; no push or merge is authorized by this plan`
- Preauthorized local actions: `read the declared sources, edit only the declared plan/code/test/documentation surfaces, run bounded local tests and validators, run approved read-only benchmark/probe commands, and regenerate declared generated surfaces from canonical sources`
- User-approval actions: `push, merge, publication, credential or provider changes, destructive recovery, discard, cleanup outside task-owned paths, and any scope or authority expansion`
- Parallel ownership: `none; shared contracts, acceptance, launcher behavior, and documentation require ordered integration`
- Sequential fallback: `baseline and inventory → common-path boundary → contract consolidation → acceptance/settlement → observation optimization → continuation/docs/economics → final verification`
- Drift gate: `capture origin/main, HEAD, merge-base, worktree status, and this plan's SHA-256 at activation; if the fetched origin/main or plan content differs from the reviewed activation inputs, rerun Task 1 inventory and reconcile the plan before any production edit`

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/coordination-simplification-and-evidence-boundaries`
- Base commit: `2bf4f94c21044165f3c293b46171c959b873fb4d`
- Expected workspace: `original checkout may be dirty; capture and preserve its actual status at activation; task worktree starts clean from the exact fetched origin/main base and contains only the task branch plus this plan`
- Next action: `run final aggregate verification and reconcile the plan to verification-before-completion`
- Blockers: `none`

## Activation Evidence

- Activation date: `2026-10-16`
- Original checkout: `C:\Users\HOANG PHI LONG DANG\repos\project-OS-starter`
- Original checkout branch: `main`
- Original checkout `HEAD`: `7196983549392a5780f80b060daba5b05dd04d10`
- Original checkout status: `pre-existing modifications preserved; see activation command output and do not copy them into the task worktree`
- Fetched `origin/main`: `2bf4f94c21044165f3c293b46171c959b873fb4d`
- Reviewed plan SHA-256 before activation: `01EC45DE7F2A0A4892886B582C184E772C9FFE09D5FB5DC5B7ED750052675E4B`
- Task worktree: `C:\Users\HOANG PHI LONG DANG\.codex\worktrees\coordination-simplification-and-evidence-boundaries\project-OS-starter`
- Task branch: `codex/coordination-simplification-and-evidence-boundaries`
- Task worktree `HEAD`: `2bf4f94c21044165f3c293b46171c959b873fb4d`
- Task worktree merge-base with `origin/main`: `2bf4f94c21044165f3c293b46171c959b873fb4d`
- Task worktree pre-edit diff against `origin/main`: `empty`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | task worktree | `codex` | none | source inventory, focused baseline tests, current Git/base proof | `639 passed, 1 skipped`; inventory and admission decision recorded below |
| Task 2 | `completed` | task worktree | `codex` | Task 1 | role-boundary tests/docs and generated-surface check | `already satisfied/no-op`; canonical role boundaries and managed-runtime block are consistent |
| Task 3 | `completed` | task worktree | `codex` | Tasks 1–2 | contract/digest/result regression suite | `already satisfied/no-op`; one execution digest owner, explicit identity checks, and structured-result boundary already exist |
| Task 4 | `completed` | task worktree | `codex` | Task 3 | acceptance, transition, release, settlement, and stale-proof tests | `279 passed, 1 skipped`; semantic acceptance proof no longer embeds settlement/resource facts |
| Task 5 | `completed` | task worktree | `codex` | Tasks 3–4 | launcher receipt-first success/failure tests and benchmark evidence | `381 passed`; optimization deferred because baseline/candidate medians and p95s are identical |
| Task 6 | `completed` | task worktree | `codex` | Tasks 2–5 | explicit plan-binding/continuation tests, documentation sync, final validation | `112 passed`; repository, planning, adapter, and whitespace validators pass; no activation gap required a code change |

## Task Breakdown

### Task 1: Establish the rebase, drift, baseline, and impact gate

**Purpose:**
- Prove the current source of truth, identify duplicate representations and
  callers, and admit only changes justified by current repository evidence.

**Task Function:**
- Build the source-first change inventory, base/drift gate, and performance
  decision gate.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: read-only architecture and call-graph inventory with
  performance-evidence judgment; resolve through Planning Dispatch before
  activation.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: the lead controller owns the initial inventory; independent
  review begins after the write set is stable.

**Specification Coverage:**
- Supplied recommendations 3–9, 12–15, and 17.
- Existing source/tests are authoritative over the pasted verdict.
- No new contract, registry, lifecycle vocabulary, or runtime path is admitted
  without a mapped owner and regression proof.

**Required Skills:**
- `skill-performance-optimization`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/project_os_runtime/attempt.py:execution_binding_digest`, `scripts/project_os_runtime/attempt.py:same_attempt_binding`, `scripts/project_os_runtime/attempt.py:normalize_attempt`
- Inspect: `scripts/project_os_runtime/results.py:validate_task_result`, `scripts/project_os_runtime/results.py:parse_task_result`, `scripts/project_os_runtime/results.py:parse_result_receipt`
- Inspect: `scripts/project_os_runtime/acceptance.py:evaluate_acceptance`, `scripts/project_os_runtime/acceptance.py:authorize_dependent_transition`, `scripts/project_os_runtime/acceptance.py:release_authorized_evidence`
- Inspect: `scripts/project_os_runtime/plan_preparation.py:prepare_plan_lanes`, `scripts/project_os_runtime/plan_preparation.py:apply_accepted_plan_transitions`
- Inspect: `scripts/secretary_live_runtime.py:run_normal`, `scripts/secretary_live_runtime.py:run_probe`, `scripts/herdr_main_launcher.py:_classify_deepagents_outcome`, `scripts/herdr_main_launcher.py:_deepagents_completion_evidence`
- Inspect: `scripts/dcode_project.py:_runtime_binding_digest`, attempt claim/settlement helpers, and result publication
- Verify: `tests/test_project_os_runtime.py`, `tests/test_plan_preparation.py`, `tests/test_evidence_release.py`, `tests/test_herdr_main_launcher.py`, `tests/test_secretary_live_runtime.py`, `tests/test_dcode_project.py`

**Dependencies:**
- The proposed plan is reviewed, but the implementation base is not accepted
  until activation captures a fresh `origin/main` SHA.

**Authority:**
- Preauthorized local actions: inspect declared files, run read-only tests/benchmark help and focused baseline commands, record the inventory and admission decision in this plan, and create no production changes
- Stop for: base mismatch, a missing canonical owner, an unbounded duplicate contract, a required external credential/provider action, or evidence that changes the approved scope

**Steps:**
- [x] Step 1: From the original checkout, run `git fetch origin main`, record `git rev-parse origin/main`, `git status --short --untracked-files=all`, and `Get-FileHash -Algorithm SHA256 docs/superpowers/plans/2026-10-16-coordination-simplification-and-evidence-boundaries-plan.md`; preserve the captured dirty state without copying it into the task worktree.
- [x] Step 2: Create `codex/coordination-simplification-and-evidence-boundaries` from the exact fetched `origin/main` SHA in a clean dedicated worktree; record worktree `HEAD`, branch, `git merge-base HEAD origin/main`, and `git diff origin/main...HEAD` before edits.
- [x] Step 3: Compare the activation plan SHA and base SHA with the reviewed inputs recorded in Coordination State. If either differs, rerun this inventory and reconcile the plan before production edits.
- [x] Step 4: Inventory all producers and consumers of task results, runtime receipts, binding digests, acceptance proofs, settlement facts, and terminal/pane observations.
- [x] Step 5: Inventory normal Secretary callers and prove that in-session Secretary behavior does not depend on `run_normal()` or managed receipts.
- [x] Step 6: Classify Tasks 2–6 as `needed`, `already satisfied`, or `deferred`; reconcile the frontmatter target set with the actual potential mutation set and record the decision in the task ledger.
- [x] Step 7: Run the existing focused baseline suite and benchmark/reporting entry points with bounded repetitions; classify live managed-Secretary economics as measured, blocked, or unavailable rather than treating blocked evidence as benefit.

**Verification:**
- [x] `py -3 -m pytest -q tests/test_project_os_runtime.py tests/test_plan_preparation.py tests/test_evidence_release.py tests/test_reconciliation.py tests/test_project_os_reconciliation.py tests/test_herdr_main_launcher.py tests/test_secretary_live_runtime.py tests/test_dcode_project.py`
- Expected: baseline tests pass or their pre-existing failures are recorded with exact names and no new failure is attributed to this plan.
- [x] `py -3 scripts/benchmark_secretary_architecture.py contract 20`
- Expected: deterministic contract benchmark completes and is labeled behavior evidence, not live economics proof.
- [x] `py -3 scripts/benchmark_secretary_reporting.py --phase baseline --repetitions 20 --output .tmp-tests/coordination-simplification-secretary-reporting-baseline.json`
- Expected: benchmark output is written under the task-owned temporary path and includes the measured scenario, repetitions, and result summary.

**Exit Criteria:**
- Every proposed production edit has an owning file, current caller evidence, and a focused proof target; unsupported redesign items are explicitly deferred; the task worktree is based on the freshly verified activation SHA.

**Task 1 Evidence And Admission Decision:**
- [x] Activation/base gate: original checkout `HEAD` was `7196983549392a5780f80b060daba5b05dd04d10`; freshly fetched `origin/main` and task worktree `HEAD` were `2bf4f94c21044165f3c293b46171c959b873fb4d`; task worktree merge-base matched and pre-edit diff was empty.
- [x] Focused baseline: `py -3 -m pytest -q tests/test_project_os_runtime.py tests/test_plan_preparation.py tests/test_evidence_release.py tests/test_reconciliation.py tests/test_project_os_reconciliation.py tests/test_herdr_main_launcher.py tests/test_secretary_live_runtime.py tests/test_dcode_project.py` → `639 passed, 1 skipped`.
- [x] Deterministic contract benchmark: `py -3 scripts/benchmark_secretary_architecture.py contract 20` completed as behavior evidence only; live managed-Secretary economics were not attempted.
- [x] Secretary reporting baseline: `py -3 scripts/benchmark_secretary_reporting.py --phase baseline --repetitions 20 --output .tmp-tests/coordination-simplification-secretary-reporting-baseline.json` completed with schema `secretary-reporting-benchmark-v1` and baseline revision `50ea7498596f7487f0650f3f6c0737c4d2a740dd`.
- [x] Completion-monitoring baseline: `py -3 scripts/benchmark_completion_monitoring.py --baseline-revision origin/main --repetitions 20 --output .tmp-tests/coordination-simplification-completion-monitoring-baseline.json` produced matching baseline/candidate source hashes, `0` lifecycle mismatches, and median subprocess totals of `2.0` on both sides; Task 5 is deferred unless a later code change creates a measurable target.
- [x] Binding/result inventory: `execution_binding_digest()` is the shared execution-binding owner used by lane preparation and dispatch; `dcode_project._runtime_binding_digest()` is a distinct provider/wire configuration digest with dedicated tests, not a duplicate execution-binding contract. `TaskResult` and receipt parsing already perform explicit assignment, attempt, task, and grant identity checks.
- [x] Role/runtime inventory: canonical Secretary/CoS/Worker docs consistently preserve optional Secretary routing, CoS acceptance, Worker bounded autonomy, and diagnostic-only receipts; `run_normal()` remains capability-blocked while probe/smoke paths remain separate.
- [x] Confirmed implementation gap: `evaluate_acceptance()` currently accepts settlement input and copies `settlement_proven`/`resource_settled` into `acceptance_proof`; Task 4 is the only admitted production change from this inventory.
- [x] Deferred/no-op decisions: Task 2 is already satisfied with no documentation edit required; Task 3 is already satisfied with no digest/result migration required; Task 5 is deferred by unchanged baseline/candidate evidence; Task 6 remains pending only for final reconciliation after Task 4.

### Task 2: Reconcile role-policy ownership and managed-Secretary boundaries

**Purpose:**
- Remove contradictory duplicate wording and establish documentation ownership
  without rewriting policy that the repository already satisfies. A no-op is a
  valid outcome when the inventory finds no contradiction.

**Task Function:**
- Audit canonical role contracts, activation policy, ownership references, and
  runtime qualification language.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded policy/documentation change with generated-surface
  synchronization; resolve before activation.

**Validator Profile (optional):**
- Controller-selected: `review-1`
- Selection basis: independent policy-contract validation is useful because the
  change spans canonical skills, runtime docs, and generated adapters.

**Specification Coverage:**
- Supplied recommendations 1–2, 10–11, and 16.
- Preserve optional Secretary, direct execution, CoS acceptance, Worker
  autonomy within scope, and the no-changed-cross-boundary-decision rule.

**Required Skills:**
- `skill-project-secretary`, `skill-chief-of-staff`, `skill-code-standards`

**Files And Symbols:**
- Modify: `.agents/skills/skill-project-secretary/SKILL.md`, `.agents/skills/skill-chief-of-staff/SKILL.md`, `docs/operating_system/planning/planning-dispatch.md`, `docs/architecture.md`, `docs/usage.md`
- Modify only if the inventory identifies contradictory wording: `docs/operating_system/runtime/runtime-surfaces.md`, `docs/operating_system/tooling/runtime-tool-resolution.md`, `docs/operating_system/procedures/runtime-adapter-procedure.md`
- Preserve and test: `scripts/secretary_live_runtime.py:run_normal`, `scripts/secretary_live_runtime.py:run_probe`, `scripts/secretary_live_runtime.py:run_smoke`
- Verify: `tests/test_skill_project_secretary.py`, `tests/test_skill_chief_of_staff.py`, `tests/test_secretary_live_runtime.py`, `tests/test_secretary_live_pilot.py`, `tests/test_deploy_agent_runtime.py`

**Dependencies:**
- Task 1 inventory identifies the canonical wording owner and confirms no normal
  caller requires managed Secretary execution.

**Authority:**
- Preauthorized local actions: edit the declared canonical policy/documentation files, update their contract tests, run adapter synchronization and validation, and preserve the blocked managed runtime behavior
- Stop for: any request to enable live provider execution, weaken acceptance/retirement gates, add a new coordination hop, or change generated files without a canonical source edit

**Steps:**
- [x] Step 1: Use the documentation owner map: `docs/operating_system/planning/planning-dispatch.md` owns activation and route selection; `.agents/skills/skill-project-secretary/SKILL.md` and `.agents/skills/skill-chief-of-staff/SKILL.md` own role-local behavior and message boundaries; `docs/architecture.md` summarizes; runtime docs describe mechanics only.
- [x] Step 2: Remove only contradictory or duplicate wording found by Task 1; do not create a new all-purpose coordination contract. Preserve current correct policy as a no-op when no contradiction exists.
- [x] Step 3: Define managed Secretary runtime, live receipts, and economics pilots as qualification/experimental surfaces; keep normal in-session Secretary reasoning independent of them.
- [x] Step 4: State that Worker tactical decisions remain inside the task contract and that escalation occurs only on authority, scope, dependency, identity, proof, or material blocker changes.
- [x] Step 5: Add or update tests proving direct, bounded-worker, CoS, and Secretary routing boundaries without creating a new launcher or message bus.
- [x] Step 6: Run `py -3 scripts/sync_agent_adapters.py --all-platforms` only when a canonical source changed, then inspect the generated diff and retain only outputs derived from those sources.

**Verification:**
- [x] `py -3 -m pytest -q tests/test_skill_project_secretary.py tests/test_skill_chief_of_staff.py tests/test_secretary_live_runtime.py tests/test_secretary_live_pilot.py tests/test_deploy_agent_runtime.py`
- Expected: role contracts pass; `run_normal()` remains explicitly capability-blocked in managed-runtime tests; probe/smoke compatibility remains separate.
- [x] `py -3 scripts/sync_agent_adapters.py --all-platforms --check`
- Expected: generated agent surfaces match canonical `.agents/skills` sources.

**Exit Criteria:**
- The documentation owner map is explicit, contradictions are removed or the task is recorded as already satisfied, and no normal path depends on managed Secretary qualification.

### Task 3: Consolidate immutable binding and semantic result consumption

**Purpose:**
- Remove repeated reconstruction of immutable attempt identity while preserving
  the existing result schema and fail-closed correlation checks.

**Task Function:**
- Normalize existing binding/digest and result adapters at one shared boundary.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: shared backend contract change spanning attempt, lane,
  result, launcher, and worker wrapper; resolve after Task 1 impact analysis.

**Validator Profile (optional):**
- Controller-selected: `review-1`
- Selection basis: independent validator should check stale-result rejection and
  compatibility behavior across producer and consumer boundaries.

**Specification Coverage:**
- Supplied recommendations 3–5 and 7.
- `TaskResult` remains the only semantic execution result after normalization;
  terminal/pane output is diagnostic only.
- The binding digest is correlation evidence, not authority; explicit identity
  fields remain authoritative wherever a consumer must independently verify
  assignment, attempt, task, grant, repository, worktree, or revision identity.
- Do not add a task database, evidence registry, or parallel receipt schema.

**Required Skills:**
- `skill-backend-verification`, `skill-test-driven-development`, `skill-code-standards`

**Files And Symbols:**
- Modify: `scripts/project_os_runtime/attempt.py:execution_binding_digest`, `scripts/project_os_runtime/attempt.py:same_attempt_binding`, `scripts/project_os_runtime/attempt.py:normalize_attempt`
- Modify: `scripts/project_os_runtime/results.py:validate_task_result`, `scripts/project_os_runtime/results.py:parse_task_result`, `scripts/project_os_runtime/results.py:parse_result_receipt`
- Modify: `scripts/project_os_runtime/lane.py:prepare_lane` and the existing lane descriptor normalization only where it duplicates binding canonicalization
- Modify: `scripts/project_os_runtime/plan_preparation.py:prepare_plan_lanes`, `scripts/dcode_project.py` result publication/attempt binding, and `scripts/herdr_parallel_dispatch.py` only for consumer migration
- Verify: `tests/test_deepagents_result_contract.py`, `tests/test_plan_preparation.py`, `tests/test_dcode_project.py`, `tests/test_herdr_parallel_dispatch.py`, `tests/test_herdr_main_launcher.py`

**Dependencies:**
- Task 1 has identified the complete binding producer/consumer inventory.
- Task 2 has not changed the runtime meaning of a Worker result.

**Authority:**
- Preauthorized local actions: edit the shared binding/result helpers and named consumers, add focused regression tests, run direct boundary tests, and preserve backward-compatible parsing for existing valid receipts
- Stop for: any schema-breaking receipt migration, acceptance decision based on terminal text, removal of stale-result rejection, or new durable identity registry

**Steps:**
- [x] Step 1: Select the existing canonical field set for immutable binding from the current attempt/lane contract and document mutable facts that remain revalidated; do not treat the digest as a substitute for explicit identity checks.
- [x] Step 2: Centralize the existing canonicalization/digest algorithm for lane preparation, worker publication, launcher evidence, and result parsing without changing its field set or encoding.
- [x] Step 3: Ensure normalized consumers carry the binding digest plus producer evidence, explicit identity fields required for independent checks, and mutable boundary facts rather than reconstructing all immutable fields.
- [x] Step 4: Preserve exact checks for assignment ID, attempt ID, task digest, grant digest, repository/worktree, current HEAD, and stale/mismatched result rejection.
- [x] Step 5: Remove provider aliases or compatibility branches only after all callers are migrated and tests prove the old semantic path is unreachable; defer any digest algorithm or field-set change to a separately versioned migration.

**Verification:**
- [x] `py -3 -m pytest -q tests/test_deepagents_result_contract.py tests/test_plan_preparation.py tests/test_dcode_project.py tests/test_herdr_parallel_dispatch.py tests/test_herdr_main_launcher.py`
- Expected: valid current results normalize once; mismatched attempt, assignment, task, grant, or binding identity remains blocked; pane text cannot promote an unconfirmed semantic result.
- [x] `py -3 -m pytest -q tests/test_project_os_runtime.py tests/test_secretary_receipts.py tests/test_secretary_evidence.py`
- Expected: receipt parsing remains bounded, identity-aware, and compatible with existing valid evidence.

**Exit Criteria:**
- Immutable binding is canonicalized once, `TaskResult` is the sole semantic worker result, and all downstream consumers use the normalized contract without weakening fail-closed checks.

### Task 4: Make acceptance, settlement, and retention consume separate proofs

**Purpose:**
- Give semantic acceptance one owner while keeping dependency transitions,
  resource settlement, and evidence release responsible only for their own
  additional facts.

**Task Function:**
- Remove overlapping proof interpretation and expose stable acceptance/resource
  evidence to downstream consumers.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: material backend correctness change with existing focused
  tests and direct boundary proof; resolve before activation.

**Validator Profile (optional):**
- Controller-selected: `review-1`
- Selection basis: independent acceptance/release review is required because
  regressions could authorize an incorrect transition or unsafe deletion.

**Specification Coverage:**
- Supplied recommendations 6–8 and 15.
- Preserve CoS authority, immutable candidate identity, required-condition
  coverage, current verification, stale-result rejection, exact evidence
  identity, independent settlement/resource proof, retirement, and retention
  gates.

**Required Skills:**
- `skill-backend-verification`, `skill-test-driven-development`

**Files And Symbols:**
- Modify: `scripts/project_os_runtime/acceptance.py:evaluate_acceptance`, `scripts/project_os_runtime/acceptance.py:authorize_dependent_transition`, `scripts/project_os_runtime/acceptance.py:authorize_evidence_release`, `scripts/project_os_runtime/acceptance.py:release_authorized_evidence`
- Modify: `scripts/project_os_runtime/plan_preparation.py:apply_accepted_plan_transitions`, `scripts/project_os_runtime/reconciliation.py:reconcile`, `scripts/project_os_runtime/attempt.py:settlement_decision`
- Modify: `scripts/dcode_project.py:_reconcile_attempt`, `scripts/dcode_project.py:_settle_attempt`, and `scripts/dcode_project.py:record_release_authorization` only where they independently reinterpret acceptance
- Verify: `tests/test_project_os_runtime.py`, `tests/test_plan_preparation.py`, `tests/test_evidence_release.py`, `tests/test_reconciliation.py`, `tests/test_project_os_reconciliation.py`, `tests/test_dcode_project.py`

**Dependencies:**
- Task 3 has established the normalized result and binding inputs.

**Authority:**
- Preauthorized local actions: edit the declared acceptance/settlement/release functions and tests, preserve exact artifact identity and retirement checks, and run direct success/failure/state/side-effect proof
- Stop for: any acceptance bypass, automatic acceptance from exit/pane/terminal text, deletion without exact artifact proof, or a cleanup failure being converted into semantic task failure without an explicit task condition

**Steps:**
- [x] Step 1: Define the canonical semantic acceptance proof from `TaskResult`, Git state, verification outcomes, and required task conditions; remove settlement/resource fields from `acceptance_proof` and make its normalized representation immutable to consumers.
- [x] Step 2: Make plan advancement validate the semantic acceptance proof once, then check only dependency state and expected plan revision.
- [x] Step 3: Keep settlement/resource proof independently supplied to release, reuse, and retirement paths; those consumers validate only their additional facts, including retirement/resource proof, retention policy, consumer acknowledgement, and physical artifact identity.
- [x] Step 4: Keep runtime settlement and resource reuse fail-closed when descendants or owned resources are not positively retired.
- [x] Step 5: Remove duplicated mismatch guards only after the focused tests demonstrate equivalent or stronger rejection behavior.

**Verification:**
- [x] `py -3 -m pytest -q tests/test_project_os_runtime.py tests/test_plan_preparation.py tests/test_evidence_release.py tests/test_reconciliation.py tests/test_project_os_reconciliation.py tests/test_dcode_project.py`
- Expected: acceptance PASS/FAIL/BLOCKED decisions remain stable; dependent transitions require a valid semantic acceptance proof; release and settlement separately require valid retirement/resource proof; release rejects stale, replaced, missing, symlinked, or mismatched evidence; cleanup remains independently represented.
- [x] Run direct boundary cases for accepted implementation with pending cleanup, failed verification, stale candidate SHA, dependency mismatch, and replaced evidence artifact.
- Expected: each case returns the owning proof decision and does not overwrite unrelated lifecycle facts.

**Exit Criteria:**
- One acceptance owner exists, downstream consumers check only their additional concerns, and no release or settlement path reimplements semantic acceptance.

**Task 4 Evidence:**
- [x] `scripts/project_os_runtime/acceptance.py:evaluate_acceptance` no longer emits a `settlement` member inside `acceptance_proof`; the existing compatibility input remains accepted but is not part of semantic proof.
- [x] `tests/test_project_os_runtime.py` proves acceptance can pass without settlement proof and that the semantic proof omits settlement facts.
- [x] `tests/test_evidence_release.py` proves release consumes the independently supplied same-attempt runtime settlement and does not depend on an embedded acceptance settlement field.
- [x] Focused verification passed: `279 passed, 1 skipped`.

### Task 5: Reduce observation overhead behind a receipt-first gate

**Purpose:**
- Reduce eager or periodic diagnostics after the existing receipt-first path has
  already established attributable completion, while preserving bounded
  diagnostics and cleanup safety.

**Task Function:**
- Tighten the existing receipt-first observation path and measure whether
  unnecessary follow-up diagnostics can be removed without creating a new
  completion architecture.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: performance-sensitive runtime change with correctness risk;
  resolve only after Task 1 baseline and Task 4 proof boundaries are accepted.

**Validator Profile (optional):**
- Controller-selected: `review-1`
- Selection basis: independent runtime validation should inspect success, stale,
  timeout, attribution, stall, and cleanup paths.

**Specification Coverage:**
- Supplied recommendation 9 and the explicit retained protections list.
- Optimize subprocess count, completion-detection delay, cleanup correctness,
  unresolved-resource rate, and duplicate execution—not worker duration alone.

**Required Skills:**
- `skill-performance-optimization`, `skill-backend-verification`, `skill-test-driven-development`

**Files And Symbols:**
- Modify: `scripts/herdr_main_launcher.py:_deepagents_completion_evidence`, `scripts/herdr_main_launcher.py:_deepagents_receipt_observation`, `scripts/herdr_main_launcher.py:_classify_deepagents_outcome`, and the bounded fallback/retirement path
- Modify: `scripts/dcode_project.py:_publish_result_receipt` only if receipt publication lacks the fields required by the already existing parser
- Verify: `tests/test_herdr_main_launcher.py`, `tests/test_dcode_project.py`, `tests/test_deepagents_result_contract.py`
- Measure: `scripts/benchmark_worker_contract.py`, `scripts/benchmark_completion_monitoring.py`, and the existing launcher performance evidence helpers

**Dependencies:**
- Task 1 baseline identifies a recurring observation cost.
- Tasks 3–4 prove that receipt attribution and cleanup facts are sufficient for
  the success path.

**Authority:**
- Preauthorized local actions: edit the named launcher/receipt consumers, add mocked and bounded runtime tests, run identical before/after benchmark scenarios, and write task-owned evidence under `.tmp-tests/coordination-simplification-*`
- Stop for: missing receipt attribution, changed worker semantics, timeout/cleanup ambiguity, unavailable Herdr wait capability, or a benchmark that cannot compare identical workloads and environment

**Steps:**
- [x] Step 1: Treat the current receipt-first path as the baseline and identify only eager or periodic diagnostics that run after attributable completion has already been established.
- [x] Step 2: Remove or defer those diagnostics only when the existing receipt/result and retirement/resource proof are sufficient; retain fallback diagnostics for missing result, attribution mismatch, approaching timeout, apparent stall, or cleanup uncertainty.
- [x] Step 3: Ensure exact-target and exceptional retry/reconciliation paths retain their stronger validation behavior.
- [x] Step 4: Capture subprocess count, completion detection delay, cleanup correctness, unresolved-resource rate, duplicate execution, false blockers, and accepted-outcome latency for identical workloads before and after the change.
- [x] Step 5: Run the predeclared benchmark and retain the change only if median subprocesses decrease by at least 20%, p95 completion-detection latency regresses by no more than 5%, and lifecycle/cleanup/reconciliation mismatches remain zero; otherwise preserve the baseline path and record Task 5 as deferred.

**Verification:**
- [x] `py -3 -m pytest -q tests/test_herdr_main_launcher.py tests/test_dcode_project.py tests/test_deepagents_result_contract.py tests/test_benchmark_completion_monitoring.py`
- Expected: confirmed structured results avoid pane reads on the success path; missing or conflicting evidence invokes bounded diagnostics and never returns false success.
- [x] `py -3 scripts/benchmark_completion_monitoring.py --baseline-revision origin/main --repetitions 20 --output .tmp-tests/coordination-simplification-completion-monitoring.json`
- Expected: the benchmark compares identical workloads and environment, records subprocess count, completion-detection delay, cleanup correctness, unresolved-resource rate, duplicate execution, false blockers, and accepted-outcome latency, and applies the predeclared retention threshold of at least 20% median subprocess reduction, no more than 5% p95 completion-detection regression, and zero lifecycle/cleanup/reconciliation mismatches; no improvement claim is made for blocked live managed-Secretary probes.

**Exit Criteria:**
- Receipt-first observation is proven safe by focused tests and fresh comparable measurements, or the change is explicitly deferred with the baseline preserved.

**Task 5 Evidence:**
- [x] Focused launcher/receipt benchmark suite passed: `381 passed`.
- [x] Exact benchmark output: `.tmp-tests/coordination-simplification-completion-monitoring.json`.
- [x] Baseline and candidate both measured median/p95 subprocess totals of `2.0`, median/p95 receipt timing of `400.0/650.0 ms`, and `0` lifecycle, cleanup, and reconciliation mismatches.
- [x] The required 20% median subprocess reduction was not met; no launcher or receipt behavior changed and Task 5 is retained as a documented deferral.

### Task 6: Harden governed activation and reconcile the final evidence

**Purpose:**
- Close only the activation/continuation gaps proven by the preceding inventory
  and reconcile final evidence without introducing new coordination machinery.

**Task Function:**
- Harden gap-driven plan-bound activation and continuation, then reconcile the
  final retained, deferred, and blocked outcomes.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: cross-cutting policy and integration task after all shared
  runtime contracts are stable; resolve before activation.

**Validator Profile (optional):**
- Controller-selected: `review-1`
- Selection basis: final plan/document/runtime validation should be independent
  from the implementation executor.

**Specification Coverage:**
- Supplied recommendations 12–17 only where the preceding inventory proves a
  remaining gap, plus the retained protections list.
- Governed execution consumes resolved plan identity; runtime grants remain
  immutable per attempt; full-plan revision checks protect atomic writes; no
  new coordination machinery is added without measured need.

**Required Skills:**
- `skill-chief-of-staff`, `skill-project-secretary`, `skill-code-standards`, `skill-verification-before-completion`

**Files And Symbols:**
- Modify only if Task 1 identifies a concrete activation/continuation gap: `scripts/project_os_runtime/plan_preparation.py:prepare_plan_lanes`, `scripts/project_os_runtime/plan_preparation.py:load_plan`
- Do not automatically modify `scripts/project_os_runtime/attempt.py` or add new plan/revision parameters; do so only if a concrete gap survives the Task 1 inventory and the existing contract cannot express the required check.
- Documentation ownership and generated-surface work remain in Task 2; parser/canonicalization work remains in Task 3 only when the inventory proves duplication.
- Verify: `tests/test_plan_preparation.py`, `tests/test_project_os_runtime.py`, `tests/test_validate_planning_lifecycle.py`

**Dependencies:**
- Tasks 2–5 complete, with any deferred optimization or scope decision recorded
  in the plan ledger.

**Authority:**
- Preauthorized local actions: edit only the gap-bearing activation/continuation sources, update focused tests, run repository validators, and record retained, deferred, blocked, or inconclusive outcomes in this plan
- Stop for: a new lifecycle registry/database, a second task truth source, plan/Git mismatch, changed acceptance authority, external publication, destructive cleanup, or unresolved generated-source drift

**Steps:**
- [x] Step 1: Re-check the Task 1 inventory and activate only the smallest plan-bound activation/continuation hardening needed to close a confirmed gap; preserve already-correct behavior as a no-op.
- [x] Step 2: Preserve immutable runtime grants, explicit resolved identity, accepted checkpoint continuation, and fail-closed redispatch conditions without adding new parameters unless the gap cannot be represented by the existing contract.
- [x] Step 3: Reconcile final evidence across retained changes, Task 5 benchmark results, deferred optimizations, blocked capabilities, and inconclusive live probes; a `BLOCKED_CAPABILITY` or `INCONCLUSIVE` live Secretary result is acceptable without claiming an economic benefit.
- [x] Step 4: Run final verification and record whether each phase was retained, deferred, blocked, or inconclusive.

**Verification:**
- [x] `py -3 -m pytest -q tests/test_plan_preparation.py tests/test_project_os_runtime.py tests/test_validate_planning_lifecycle.py`
- Expected: any confirmed activation/continuation gap is covered while existing explicit identity, immutable-grant, and fail-closed behavior remains intact.
- [x] `py -3 scripts/validate_repo_contracts.py --repo-root . --fast`
- Expected: repository contracts pass without staging or rewriting unrelated user changes.
- [x] `py -3 scripts/validate_planning_lifecycle.py --repo-root . --plan docs/superpowers/plans/2026-10-16-coordination-simplification-and-evidence-boundaries-plan.md`
- Expected: this plan satisfies the current implementation-plan contract and its task ledger is internally consistent.
- [x] `py -3 scripts/sync_agent_adapters.py --all-platforms --check`
- Expected: canonical and generated agent surfaces are synchronized.
- [x] `git diff --check`
- Expected: no whitespace errors in the task-owned diff.

**Exit Criteria:**
- Final proof identifies the retained simplifications, deferred changes, blockers, and measured outcomes; no required task remains unresolved and no generated or canonical surface is stale.

**Task 6 Evidence:**
- [x] Plan-bound activation/continuation coverage passed in `112` focused tests; existing explicit identity and fail-closed behavior remained sufficient, so no Task 6 production edit was admitted.
- [x] `validate_repo_contracts.py --repo-root . --fast`, `validate_planning_lifecycle.py`, `sync_agent_adapters.py --all-platforms --check`, and `git diff --check` passed.
- [x] Final disposition records Task 4 as retained, Task 5 as deferred by threshold, and live managed-Secretary economics as not required for this implementation because no live benefit was claimed.

## Verification

Final artifact-level verification must run after all retained implementation
changes are complete and from the same task-owned worktree:

- `py -3 -m pytest -q tests/test_project_os_runtime.py tests/test_plan_preparation.py tests/test_evidence_release.py tests/test_reconciliation.py tests/test_project_os_reconciliation.py tests/test_secretary_adapter.py tests/test_secretary_receipts.py tests/test_secretary_evidence.py tests/test_secretary_live_runtime.py tests/test_secretary_live_pilot.py tests/test_herdr_main_launcher.py tests/test_dcode_project.py tests/test_deepagents_result_contract.py tests/test_herdr_parallel_dispatch.py`
- `py -3 -m pytest -q tests/test_skill_project_secretary.py tests/test_skill_chief_of_staff.py tests/test_sync_agent_adapters.py tests/test_validate_planning_lifecycle.py tests/test_validate_repo_contracts.py`
- `py -3 scripts/validate_repo_contracts.py --repo-root . --fast`
- `py -3 scripts/validate_planning_lifecycle.py --repo-root . --plan docs/superpowers/plans/2026-10-16-coordination-simplification-and-evidence-boundaries-plan.md`
- `py -3 scripts/sync_agent_adapters.py --all-platforms --check`
- `git diff --check`
- `git status --short --branch`, confirming only the declared task-owned changes
  and preserved pre-existing user changes are present.

## Final Verification Result

- Result: `verified`
- Verified workspace: `C:\Users\HOANG PHI LONG DANG\.codex\worktrees\coordination-simplification-and-evidence-boundaries\project-OS-starter`
- Mechanism: native managed Git worktree
- Branch: `codex/coordination-simplification-and-evidence-boundaries`
- Base branch and commit: `origin/main` at `2bf4f94c21044165f3c293b46171c959b873fb4d`
- Verified code state: `1895446` (`chore: reconcile coordination plan evidence`); final status-only plan update does not change implementation inputs.
- Aggregate verification: `792 passed, 1 skipped` for runtime, acceptance, receipt, launcher, dispatch, and reconciliation tests; `125 passed` for role, adapter, planning, and repository-contract tests.
- Validators: repository contracts, planning lifecycle, required sections, generated adapters, and `git diff --check` all passed.
- Approved deferral: Task 5 receipt-first optimization remains baseline-preserved because the exact benchmark measured no subprocess improvement and zero lifecycle/cleanup/reconciliation mismatches; no live managed-Secretary economic benefit is claimed.
- Repository state: clean task worktree; no push, merge, publication, or cleanup performed.

## Completion Criteria

The plan is ready for completion verification when:

1. progressive coordination and managed-Secretary boundaries are canonical and
   tested;
2. existing task-result, binding, acceptance, settlement, and retention
   contracts have one owner each without a parallel registry or schema;
3. stale, mismatched, timeout, attribution, cleanup, and authority failures
   remain fail-closed;
4. any receipt-first optimization has fresh comparable evidence or is recorded
   as deferred;
5. governed activation and continuation consume explicit resolved identity;
6. canonical documentation and generated surfaces are synchronized;
7. all task-local and final verification evidence is recorded in this plan;
8. deviations, blockers, and deferrals are explicit; and
9. `skill-verification-before-completion` returns `verified` before this plan
   changes from `proposed`/`active` to `completed`.

