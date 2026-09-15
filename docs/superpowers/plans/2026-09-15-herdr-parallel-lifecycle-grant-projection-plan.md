---
layer: change
artifact_type: plan
status: active
template_id: implementation-plan
contract_version: "1"
name: herdr-parallel-lifecycle-grant-projection
parent_spec: docs/superpowers/specs/2026-09-14-parallel-deepagents-dispatch-spec.md
targets:
  - scripts/herdr_parallel_dispatch.py
  - scripts/herdr_main_launcher.py
  - tests/test_herdr_parallel_dispatch.py
  - tests/test_herdr_main_launcher.py
  - docs/superpowers/specs/2026-09-14-parallel-deepagents-dispatch-spec.md
---

# Herdr Parallel Lifecycle, Grant, And Projection Corrections

## Goal

Correct the bounded two-lane Herdr/DeepAgents pilot at its existing lifecycle
boundaries. Preserve separate delivery, execution, observation, task-result,
cleanup, and performance evidence. Make timeout ownership, retirement,
attempt correlation, Runtime Grant propagation, and wait ordering fail closed.
Scope projection to explicit CoS input mappings validated by
`load_lane_descriptors_from_items()`; do not invent automated Markdown or
prose derivation. Do not add a second result schema, durable runtime ledger,
retry engine, streaming transport, Codex wait integration, or concurrency
increase.

## Implementation Outcomes

### Reliable attempt contract

`reported_completed` with `accepted: null` represents complete runtime
reporting with CoS acceptance still pending. Missing or unknown descendant,
cleanup, or ownership evidence never proves retirement. Missing task
verification prevents acceptance, but independently proven resource settlement
may release capacity. Completion classification is:

| Evidence | Capacity | Runtime unresolved | CoS acceptance |
| --- | --- | --- | --- |
| Correlated completion report; ownership and cleanup settled | Retired | `false` | Pending |
| Missing or unverified task report; ownership and cleanup settled | Retired | `true` | Pending |
| Unknown descendant or cleanup state | Occupied | `true` | Blocked |

Timeout results preserve partial output and attempt/process identity while
retaining explicit reconciliation ownership.

### Bound Runtime Grant

Every admitted lane carries the existing normalized Runtime Grant. The helper
maps admitted requested grant values to launcher CLI arguments. Comparison
contract: admitted requested grant maps to CLI arguments; correlated
preparation evidence is the source of normalized `runtime_grant` and
`grant_digest`; correlated final assignment evidence must carry the matching
digest. Reuse one normalization/digest implementation. Conflicting top-level
and nested MCP selectors block; no selector wins silently. Child delegation
remains policy enforcement, not runtime-enforced subtree budgeting.

### Correct observation and projection

Confirmed receipts skip unnecessary blocking marker waits but still receive
bounded pane/process evidence needed for task reporting and ownership. An
unresolved attempt remembers whether the current attempt marker was observed,
uses a short wait that reserves time for receipt rereads and final probes, and
distinguishes interval expiry from transport failure. Earlier uncertainty stays
recorded until later authoritative evidence resolves it. CoS supplies descriptors
from existing task, profile, Git, Herdr, and grant owners; missing or ambiguous
fields block. File-backed descriptors use the same validation path.

### Proof and documentation

Focused regression tests cover partial timeout output, ownership handback,
grant propagation and mismatch, explicit retirement states, receipt-aware wait
ordering, and runtime completion versus CoS acceptance. The active parallel
dispatch specification matches executable behavior. No performance or
executor-fitness claim is promoted without fresh paired measurements.

## Execution Approach

- Mode: `parallel-capable`
- Coordination: `git-tracked`
- Execution model: `plan-bound-execution via CoS`
- Lead controller: native Codex; sole writer of `Coordination State` and task ledger
- MAIN AGENT transport: Herdr; each write-capable lane uses one isolated Git worktree
- Required skills: `skill-chief-of-staff`, `skill-dispatching-parallel-agents`, `skill-plan-document-reviewer`, `skill-executing-plans`, `skill-backend-verification`, `skill-systematic-debugging`, `skill-test-driven-development`, `skill-verification-before-completion`, `skill-using-git-worktrees`
- Isolation: dedicated worktree per write-capable lane from the recorded base commit; preserve lead-workspace untracked `.playwright-mcp/` and `db/`
- Commit policy: lane commits are implementation artifacts; lead creates one checkpoint only after accepting task proof and updating this ledger; no push or remote merge authority; accepted local lane integration remains authorized to the lead
- Preauthorized local actions: create declared isolated worktrees, inspect and edit listed files, run listed local tests and validators, run bounded Herdr capability checks, and execute bounded harmless runtime proof after the plan is activated
- User-approval actions: push, remote merge, publication, destructive recovery, discard, cleanup outside task-owned worktrees, credential/authentication changes, external writes, and any live worker smoke not explicitly accepted by the activated plan
- Parallel ownership: Task 2 owns dispatcher source plus dispatcher tests; Task 3 owns launcher source plus launcher tests; Task 4 owns the active specification; no shared write paths inside a wave
- Wave order: Task 1 first; Tasks 2 and 3 run in parallel from the accepted Task 1 checkpoint; Task 4 serializes local integration before active-spec review; Task 5 performs final verification against the combined revision
- Review/integration: Codex-only; MAIN AGENTS do not update plan state, accept another lane, merge, or clean worktrees
- Sequential fallback: if isolated DeepAgents binding or parallel execution cannot be proven, CoS rebinds the task to Codex or runs dependency-ready lanes sequentially without changing scope; rebind immediately only when no launch occurred, otherwise reconcile the existing attempt first

## Coordination State

- Coordination owner: `native Codex lead controller / CoS`
- Coordination mode: `plan-bound-execution`
- Coordination schema: `2`
- Branch: `codex/herdr-parallel-lifecycle-grant-projection`
- Base commit: `3a7f3941bfbed3765ce956d7b9e1d80b005ca41f`
- Activation checkpoint: `f2902a60bb40ed537e1e6fc42598a7ff351062be`
- Expected workspace: lead remains on current checkout; write-capable lanes use isolated worktrees from the base commit; `.playwright-mcp/` and `db/` remain untouched
- Next action: establish fresh Task 2 and Task 3 worktrees from the accepted Task 1 checkpoint and dispatch independent root-cause patch lanes
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | isolated worktree | `codex` | none | red contract tests plus baseline | commit `55affa393c9ffa4ffc50b5a45e8e6cc621ee383f`; 169 passed, 8 intended correction reds; CoS `PASS` |
| Task 2 | `active` | isolated worktree | `codex` | Task 1 | dispatcher tests and direct helper proof | root-cause patch lane pending |
| Task 3 | `active` | isolated worktree | `codex` | Task 1 | launcher tests and bounded observation proof | root-cause patch lane pending |
| Task 4 | `pending` | lead workspace | `codex` | Tasks 2–3 | integrated revision and active spec consistency | pending |
| Task 5 | `pending` | lead workspace | `codex` | Task 4 | focused, full, contract, runtime, and Git verification | pending |

CoS resolves each pending executor and template profile independently through
`docs/operating_system/planning/planning-dispatch.md`. `deepagents` is eligible
only after host-Git/worktree binding and capability checks pass. A failed or
uncertain binding rebinds the task to `codex`; it does not widen authority or
change task ownership. Child delegation remains denied unless the computed
Runtime Grant explicitly permits it and the child scope is a strict subset.

Revision protocol: `3a7f3941bfbed3765ce956d7b9e1d80b005ca41f` remains the original
baseline. The activation checkpoint is Task 1’s starting revision and is recorded
in this ledger after activation. After Task 1 proof is accepted, the lead creates
a checkpoint at `55affa393c9ffa4ffc50b5a45e8e6cc621ee383f` and creates Task 2 and
Task 3 worktrees from it. After both implementation lanes are accepted, the lead
integrates them locally and creates the combined checkpoint before Task 4 reviews
the active specification. Task 5 runs only against that combined revision. Git
remains the source of checkpoint identity; the plan records task state and
evidence, not copied future commit IDs.

## Task Breakdown

### Task 1: Establish failing lifecycle and grant cases

**Purpose:**
- Convert each verified verdict defect into a failing regression test before production changes.

**Task Function:**
- Define executable boundary cases and record the current baseline without changing production code.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: Herdr-supervised Codex lane needs ordinary repo context plus lifecycle-test reasoning; no child delegation grant.

**Validator Profile (optional):**
- Controller-selected: `review`
- Selection basis: independently check that each red test fails for the intended missing behavior.

**Specification Coverage:**
- Covers honest completion semantics, conservative retirement, attempt correlation, bounded observation, Runtime Grant binding, and no unsafe retry after uncertainty.

**Required Skills:**
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/herdr_parallel_dispatch.py:run_lane`, `scripts/herdr_parallel_dispatch.py:_launcher_command`, `scripts/herdr_parallel_dispatch.py:_admit_lanes`, `scripts/herdr_main_launcher.py:_classify_deepagents_outcome`, `scripts/herdr_main_launcher.py:_deepagents_completion_evidence`
- Modify: `tests/test_herdr_parallel_dispatch.py`, `tests/test_herdr_main_launcher.py`
- Verify: `tests/test_herdr_parallel_dispatch.py`, `tests/test_herdr_main_launcher.py`

**Dependencies:**
- Original baseline is `3a7f3941bfbed3765ce956d7b9e1d80b005ca41f`; Task 1 starts from the activation checkpoint recorded in Coordination State.
- Preserve unrelated lead-workspace paths `.playwright-mcp/` and `db/`.

**Authority:**
- Preauthorized local actions: edit only the two named test files and run focused Python tests with mocked subprocesses.
- Stop for: a required behavior not covered by the active parent specification, a new result schema, live worker execution, or changes outside the two test files.

**Steps:**
- [x] Step 1: Record baseline focused test output and current Git/worktree identity.
- [x] Step 2: Add red tests for timeout before preparation and after preparation, `TimeoutExpired.output`/`.stderr` preservation, byte decoding, incomplete trailing JSON, attempt/process identity, and unresolved ownership handback.
- [x] Step 3: Add red tests proving absent or `unknown` `descendant_state` stays occupied while explicit `terminated` or `not_started` can retire capacity only with explicit cleanup evidence.
- [x] Step 4: Define and test the comparison contract: admitted requested grant maps to launcher CLI arguments; correlated preparation supplies normalized `runtime_grant` and `grant_digest`; correlated final assignment supplies the matching digest. Add red tests for grant mismatch blocking and conflicting top-level/nested MCP selectors.
- [x] Step 5: Add red tests proving confirmed receipts skip `pane wait-output` but retain bounded pane/process probes; unresolved attempts reread receipt after bounded wait.
- [x] Step 6: Add red classification coverage proving `reported_completed` plus `accepted: null` is runtime completion pending CoS acceptance, not accepted success.
- [x] Step 7: Feed actual JSON evidence emitted by the existing launcher composition/classification path into the dispatcher test; do not hand-construct an equivalent completion fixture.

**Verification:**
- [x] `python -m pytest -q tests/test_herdr_parallel_dispatch.py tests/test_herdr_main_launcher.py`
- Expected: existing tests pass; newly added cases fail only at unimplemented correction points, including both timeout phases and the launcher-to-dispatcher evidence path.

**Exit Criteria:**
- Every required correction has one failing, behavior-specific test with exact evidence fields and state expectations.

### Task 2: Harden dispatcher timeout, retirement, and grant binding

**Purpose:**
- Make the parallel helper preserve unresolved attempt evidence, enforce explicit retirement states, and forward the canonical Runtime Grant.

**Task Function:**
- Implement the smallest dispatcher-side correction against existing JSONL and assignment evidence.

**Template Profile:**
- Controller-selected: `high`
- Selection basis: independent Herdr Codex lane must trace shared dispatcher callers and correct subprocess, retirement, and grant-boundary defects without widening scope.

**Validator Profile (optional):**
- Controller-selected: `review`
- Selection basis: inspect timeout ownership, grant mismatch handling, and capacity transitions independently.

**Specification Coverage:**
- Covers bounded parallel lifecycle, attempt-safe evidence, conservative retirement, Runtime Grant subset binding, sibling preservation, and file/in-memory descriptor symmetry.

**Required Skills:**
- `skill-test-driven-development`
- `skill-backend-verification`
- `skill-dispatching-parallel-agents`
- `skill-systematic-debugging`

**Files And Symbols:**
- Inspect: `scripts/herdr_parallel_dispatch.py:_REQUIRED_FIELDS`, `scripts/herdr_parallel_dispatch.py:_launcher_command`, `scripts/herdr_parallel_dispatch.py:parse_launcher_records`, `scripts/herdr_parallel_dispatch.py:run_lane`, `scripts/herdr_parallel_dispatch.py:_admit_lanes`, `scripts/herdr_parallel_dispatch.py:run_parallel`
- Modify: `scripts/herdr_parallel_dispatch.py`, `tests/test_herdr_parallel_dispatch.py`
- Verify: `tests/test_herdr_parallel_dispatch.py`, launcher command capture, and JSONL result output

**Dependencies:**
- Task 1 accepted with red cases present at commit `55affa393c9ffa4ffc50b5a45e8e6cc621ee383f`.
- Launcher already accepts `--grant-turns`, `--grant-wall-clock-seconds`, `--grant-child-agents`, and `--mcp-select`; do not duplicate launcher grant normalization.
- Runtime Grant shape remains the normalized launcher shape: `turns.requested`, `wall_clock_seconds.requested`, `mcp_select`, `delegation.child_agents`, and `grant_digest`.
- Task 2 starts from the accepted Task 1 checkpoint. Task 3 owns launcher output flushing; Task 2 consumes that output and does not modify launcher source.

**Authority:**
- Preauthorized local actions: modify only dispatcher source and its focused tests, run mocked subprocess checks, and run the supported dispatcher CLI help check with static lane descriptors kept in tests.
- Stop for: launcher source changes, a durable attempt registry, automatic kill/retry, grant inference from missing fields, or any worktree/process cleanup requiring destructive action.

**Steps:**
- [ ] Step 1: Use `skill-systematic-debugging` to trace `run_lane()` callers, parser/assignment consumers, and capacity transitions; confirm each red test maps to one shared root cause and check sibling paths for the same defect.
- [ ] Step 2: Make lane admission require an explicit requested Runtime Grant, normalize it through the existing launcher-compatible shape, validate structure without deriving authority from task prose, and reject conflicting top-level/nested MCP selectors.
- [ ] Step 3: Extend `_launcher_command()` to forward requested grant values and canonical MCP selectors; preserve existing redacted command behavior.
- [ ] Step 4: Compare correlated preparation `runtime_grant`/`grant_digest` and final assignment `grant_digest` against the admitted lane binding; classify mismatch as unresolved and keep capacity occupied.
- [ ] Step 5: On timeout, use one helper that retains the `Popen` handle, drains and closes its pipes, reaps the process, normalizes available text/byte `output` and `stderr`, preserves raw partial records, and extracts parseable attempt identity. Record process identity plus the helper’s reconciliation ownership. Do not retry or replace execution until that same attempt is reaped; if no launch occurred, rebind immediately is allowed.
- [ ] Step 6: Keep incomplete trailing JSON as malformed evidence without discarding preceding valid preparation or assignment records.
- [ ] Step 7: Require explicit `descendant_state` in `{terminated, not_started}` for retirement; treat missing or `unknown` as occupied. Require explicit cleanup state `removed` with `recovery_required` false.
- [ ] Step 8: Keep settled resource retirement separate from unresolved task-result evidence; a missing task report may still retire capacity when ownership and cleanup are independently settled. Preserve sibling results and nonzero coordinator status.
- [ ] Step 9: Implement the explicit completion matrix: correlated completion plus settled ownership/cleanup retires with CoS acceptance pending; missing/unverified task report plus settled ownership/cleanup retires but remains runtime-unresolved; unknown descendant or cleanup stays occupied and runtime-unresolved.

**Verification:**
- [ ] `python -m pytest -q tests/test_herdr_parallel_dispatch.py`
- Expected: timeout partial output, grant forwarding/mismatch, explicit retirement, stale/malformed evidence, and sibling-preservation tests pass.
- [ ] `python scripts/herdr_parallel_dispatch.py --help`
- Expected: helper remains file-backed and capped at two lanes; no new retry or ledger options appear.

**Exit Criteria:**
- Dispatcher never treats missing lifecycle evidence or foreign grant evidence as safe retirement, and timeout output gives CoS enough identity to reconcile the same attempt.

### Task 3: Correct launcher classification and receipt-aware waits

**Purpose:**
- Align launcher observation order and result classification without adding acceptance authority or Codex wait integration.

**Task Function:**
- Implement bounded DeepAgents observation and preserve independent lifecycle sections at the existing launcher composition boundary.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: independent Herdr Codex lane must trace launcher observation callers and correct bounded receipt/pane/process behavior with focused regression proof.

**Validator Profile (optional):**
- Controller-selected: `review`
- Selection basis: independently inspect wait ordering, stale marker handling, and acceptance separation.

**Specification Coverage:**
- Covers honest delivery/completion semantics, receipt correlation, bounded observation, timeout uncertainty, cleanup authority, and CoS-only acceptance.

**Required Skills:**
- `skill-test-driven-development`
- `skill-backend-verification`
- `skill-systematic-debugging`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:_deepagents_completion_snapshot`, `scripts/herdr_main_launcher.py:_deepagents_completion_evidence`, `scripts/herdr_main_launcher.py:_classify_deepagents_outcome`, `scripts/herdr_main_launcher.py:_build_assignment_result`, `scripts/herdr_main_launcher.py:main`
- Modify: `scripts/herdr_main_launcher.py`, `tests/test_herdr_main_launcher.py`
- Verify: launcher unit tests, launcher JSON assignment output, Herdr wait capability help/schema

**Dependencies:**
- Task 1 accepted with launcher red cases present at commit `55affa393c9ffa4ffc50b5a45e8e6cc621ee383f`.
- Preserve `_build_assignment_result()` as the single result composition boundary.
- Preserve current `pane wait-output` fallback and fail-closed Codex numeric wall-clock behavior.

**Authority:**
- Preauthorized local actions: modify only launcher source and its focused tests, run mocked Herdr commands, and run bounded read-only Herdr capability checks.
- Stop for: production `agent wait`, raw socket/event transport, automatic acceptance, automatic cleanup/retry, or changes to `scripts/dcode_project.py`.

**Steps:**
- [ ] Step 1: Use `skill-systematic-debugging` to trace `_deepagents_completion_snapshot()` and `_deepagents_completion_evidence()` callers, confirm shared wait/receipt root causes, and check for equivalent stale-marker or transport handling elsewhere.
- [ ] Step 2: Read the receipt before marker waiting. Memoize observation of the current attempt marker. If receipt is confirmed, skip blocking `wait-output` while retaining one bounded pane read and process probe.
- [ ] Step 3: For unresolved receipts, perform one short bounded marker wait, reserving transport overhead and time for receipt rereads plus fresh pane/process probes inside the absolute observation and settlement deadlines. Do not give the native wait and enclosing subprocess identical timeout budgets.
- [ ] Step 4: Preserve stale-marker rejection. Classify marker absence during this interval separately from transport failure; retain earlier uncertainty, but let later authoritative receipt/process/pane evidence resolve it. Never let wait success prove task acceptance, cleanup, retirement, or retry safety.
- [ ] Step 5: Keep `reported_completed` with `accepted: null`, status `completed`, and explicit reconciliation semantics. Ensure compatibility fields do not convert pending CoS acceptance into `true`; dispatcher remains the consumer that classifies CoS acceptance.
- [ ] Step 6: Keep missing receipt, observer error, unknown descendant, and cleanup recovery states unresolved even when worker exit code is zero.
- [ ] Step 7: Record every wait/probe timeout as bounded observation uncertainty with attempt identity and existing performance evidence. Test the production observation path with a receipt appearing during wait and process state changing before the final probe.
- [ ] Step 8: Run launcher with `python -u` or explicitly flush preparation output so attempt identity reaches the dispatcher before timeout.

**Verification:**
- [ ] `python -m pytest -q tests/test_herdr_main_launcher.py`
- Expected: receipt-aware ordering, stale marker, observer failure, timeout, classification matrix, and independent lifecycle-field tests pass.
- [ ] `herdr agent wait --help`
- Expected: capability remains inspectable only; launcher does not call it in captured production command tests.
- [ ] `herdr pane wait-output --help`
- Expected: bounded `--regex`/`--timeout` capability remains available for DeepAgents observation.

**Exit Criteria:**
- Launcher returns runtime evidence without inventing acceptance, and every unresolved observation retains explicit reconciliation requirements.

### Task 4: Align active specification with executable contract

**Purpose:**
- Integrate accepted implementation changes, then make the active parallel-dispatch specification state the corrected lifecycle, grant, projection, and non-goal boundaries.

**Task Function:**
- Reconcile maintained contract text only after accepted Task 2 and Task 3 changes are locally integrated into one combined revision.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: narrow canonical documentation update with exact source/test evidence available from Tasks 2–3.

**Validator Profile (optional):**
- Controller-selected: `review`
- Selection basis: independent spec-to-source consistency check.

**Specification Coverage:**
- Covers active parent-spec requirements, SSOT ownership, expected versus observed Git identity, Runtime Grant binding, timeout ownership, and explicit optimization deferrals.

**Required Skills:**
- `skill-plan-document-reviewer`
- `skill-code-standards`

**Files And Symbols:**
- Inspect: `docs/superpowers/specs/2026-09-14-parallel-deepagents-dispatch-spec.md`, `scripts/herdr_parallel_dispatch.py`, `scripts/herdr_main_launcher.py`, focused test output
- Modify: `docs/superpowers/specs/2026-09-14-parallel-deepagents-dispatch-spec.md`
- Verify: active specification, repository search for stale lifecycle claims, and `git diff --check`

**Dependencies:**
- Tasks 2 and 3 accepted by CoS, locally integrated by the lead, and represented by one combined checkpoint with source and focused-test evidence.
- Keep historical completed plans unchanged.

**Authority:**
- Preauthorized local actions: edit only the active parent specification, run exact-text searches and `git diff --check`, and record accepted deferrals in the plan.
- Stop for: a source/spec contradiction requiring new behavior, generated-surface changes, new coordination state, or any documentation path outside the active parent specification.

**Steps:**
- [ ] Step 1: Confirm the lead’s combined checkpoint contains accepted Task 2 and Task 3 source/test changes; review the specification against that revision, not lane-only revisions.
- [ ] Step 2: State that `reported_completed` means runtime reporting complete while `accepted: null` keeps CoS acceptance pending.
- [ ] Step 3: State that missing/unknown descendant, cleanup, ownership, or observation evidence never proves retirement or retry safety.
- [ ] Step 4: Document normalized Runtime Grant propagation, digest matching, child-scope subset rules, and fail-closed mismatch behavior.
- [ ] Step 5: Document receipt-first wait ordering and bounded fallback without adding `agent wait` production integration.
- [ ] Step 6: Define CoS ephemeral projection as an explicit mapping from existing structured task, profile, Git, Herdr, and grant owners; reject missing/ambiguous values; validate `--lanes-file` through the same admission path; keep expected Git identity separate from observed identity. Do not add automated Markdown/prose derivation unless an existing structured caller is named and updated within this scope.
- [ ] Step 7: Add specification tests/search evidence for missing inputs, dependency readiness, grant conflicts, and expected-versus-observed Git identity.
- [ ] Step 8: Record executor-fitness reuse, streaming, Codex waits, native mutation idempotency, and concurrency expansion as deferred follow-up work requiring separate evidence.

**Verification:**
- [ ] `rg -n -i "missing.*retirement|reported_completed|accepted: null|grant_digest|descendant_state|wait-output|lanes-file|expected.*observed|fitness|streaming|idempotency" docs/superpowers/specs/2026-09-14-parallel-deepagents-dispatch-spec.md`
- Expected: active contract uses exact field names and does not claim unsupported enforcement or optimization.
- [ ] `git diff --check`
- Expected: no whitespace errors.

**Exit Criteria:**
- Active specification, source behavior, and focused tests describe one contract with no contradictory lifecycle or grant claims.

### Task 5: Integrate and perform final backend verification

**Purpose:**
- Reconcile accepted lane changes and prove the complete behavior at direct helper/launcher boundaries before any branch disposition.

**Task Function:**
- Perform serialized Codex integration, evidence review, runtime proof, and final plan verification.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: only lead Codex may integrate lanes, update coordination state, and make final acceptance decisions.

**Validator Profile (optional):**
- Controller-selected: `review`
- Selection basis: independent final plan and diff review before status transition.

**Specification Coverage:**
- Covers all implementation outcomes, task-local proof, exact combined revision review, backend failure/state evidence, and approved deferrals.

**Required Skills:**
- `skill-backend-verification`
- `skill-verification-before-completion`
- `skill-plan-document-reviewer`

**Files And Symbols:**
- Inspect: all plan targets, accepted lane commits, current Git status, Herdr capability output, and test output
- Modify: this plan only for accepted evidence, task ledger transitions, deviations, and final verification record
- Verify: `scripts/herdr_parallel_dispatch.py`, `scripts/herdr_main_launcher.py`, both focused test files, active parent specification, exact branch/base/HEAD identity

**Dependencies:**
- Tasks 1–4 accepted; no active lane, unresolved required blocker, or unreviewed lane commit remains.
- Lead workspace preserves `.playwright-mcp/` and `db/` without mutation.

**Authority:**
- Preauthorized local actions: integrate accepted lane commits, update this plan ledger, run named tests/validators/capability checks, and execute one bounded harmless runtime proof using isolated worktrees and panes.
- Stop for: failed required proof, stale or mismatched Herdr/runtime binding, live process ownership uncertainty, out-of-scope changes, credential/authentication need, destructive recovery, or any request to push/merge/clean.

**Steps:**
- [ ] Step 1: Inspect each lane diff and accept only declared paths, exact base identity, task-local proof, and no unresolved scope deviation.
- [ ] Step 2: Integrate accepted lane commits one at a time; update this ledger in the lead workspace after each accepted checkpoint.
- [ ] Step 3: Run focused lifecycle tests and confirm the new cases fail if any correction is reverted.
- [ ] Step 4: Run one bounded harmless two-lane runtime proof only after mock and sequential-control gates; capture launcher JSON, receipt JSON, process/ownership evidence, Git identity, and final task-result/cleanup state.
- [ ] Step 5: Run full repository tests and repository contract validation.
- [ ] Step 6: Re-run Herdr version/help/schema checks and inspect for unsupported `agent wait`, raw event transport, retry, ledger, or concurrency-expansion paths.
- [ ] Step 7: Run final diff/status checks, confirm unrelated untracked paths remain untouched, and request `skill-verification-before-completion` before any status transition to `completed`.
- [ ] Step 8: Keep lifecycle runtime trace separate from performance qualification; make no cost or latency claim without fresh paired measurements.

**Verification:**
- [ ] `python -m pytest -q tests/test_herdr_parallel_dispatch.py tests/test_herdr_main_launcher.py`
- Expected: focused lifecycle suite passes.
- [ ] `python -m pytest -q`
- Expected: full repository suite passes with no unrelated failure introduced.
- [ ] `python scripts/validate_repo_contracts.py`
- Expected: repository contract validation passes.
- [ ] `herdr --version`
- Expected: installed Herdr version is recorded in evidence.
- [ ] `herdr agent wait --help`
- Expected: informational capability check only; production launcher remains free of `agent wait` integration.
- [ ] `herdr pane wait-output --help`
- Expected: bounded marker-wait capability check passes.
- [ ] `herdr api schema --json | rg -n -F 'agent.wait'`
- Expected: schema contains `agent.wait`; evidence is informational and does not authorize production integration.
- [ ] `herdr api schema --json | rg -n -F 'pane.wait_for_output'`
- Expected: schema contains `pane.wait_for_output`; evidence is informational.
- [ ] `git diff --check`
- Expected: no whitespace errors.
- [ ] `git status --short --branch`
- Expected: only declared plan/source/test/spec changes appear; `.playwright-mcp/` and `db/` remain untouched.

**Exit Criteria:**
- `skill-verification-before-completion` returns `verified`; all required evidence is fresh, task ledger and Git state reconcile, no required blocker remains, and no branch push/merge/cleanup occurs without separate authorization.

## Verification

Final verification is serialized by the lead after accepted lane integration:

- `python -m pytest -q tests/test_herdr_parallel_dispatch.py tests/test_herdr_main_launcher.py`
- `python -m pytest -q`
- `python scripts/validate_repo_contracts.py`
- `herdr --version`
- `herdr agent wait --help`
- `herdr pane wait-output --help`
- `herdr api schema --json | rg -n -F 'agent.wait'`
- `herdr api schema --json | rg -n -F 'pane.wait_for_output'`
- `git diff --check`
- `git status --short --branch`

Backend evidence must include direct helper/launcher boundary results, success
and failure cases, final process/cleanup state, timeout/partial-failure
ownership, grant binding, attempt identity, and one representative bounded
runtime trace. Runtime trace proves lifecycle correctness only. Missing runtime
or cost telemetry is recorded as incomplete; it does not become a performance
success claim.

## Completion Criteria

The plan is ready for completion verification when:

1. timeout results preserve available partial stdout/stderr, attempt identity, process identity, and reconciliation ownership
2. explicit descendant and cleanup evidence controls capacity retirement; missing or unknown evidence stays occupied
3. Runtime Grant values and MCP selectors are forwarded from canonical lane input and returned evidence matches the grant digest
4. `reported_completed` remains distinct from CoS acceptance and no launcher path invents `task_result.accepted: true`
5. receipt-aware wait ordering is bounded, attempt-correlated, and fail closed on transport or observation uncertainty
6. file-backed and in-memory descriptor inputs share validation; missing or ambiguous canonical inputs block
7. active specification matches source and tests; historical completed plans remain unchanged
8. focused tests, full tests, contract validation, Herdr capability checks, and final Git checks pass
9. one bounded harmless runtime trace proves direct process, receipt, ownership, Git, and final state evidence, or an external limitation is recorded and the affected criterion remains incomplete
10. `skill-verification-before-completion` returns `verified` before the lead marks this plan `completed`

Deferred follow-up: executor-fitness evidence reuse, model-usage optimization
and concurrency expansion, incremental streaming, Codex `agent wait`, native
mutation idempotency, raw event transport, and any durable runtime ledger.
