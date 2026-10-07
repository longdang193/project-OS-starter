---
layer: change
artifact_type: plan
contract_version: "1"
status: active
template_id: implementation-plan
name: secretary-live-organizational-probe
targets:
  - docs/superpowers/plans/2026-10-07-secretary-live-organizational-probe-plan.md
  - probe_artifacts/alpha.md
  - probe_artifacts/beta.md
  - probe_artifacts/integration-a.md
  - probe_artifacts/follow-up-b.md
  - probe_artifacts/bypass.md
  - scripts/dcode_project.py
  - scripts/herdr_main_launcher.py
  - tests/test_dcode_project.py
  - tests/test_herdr_main_launcher.py
---

# Secretary Live Organizational Probe Plan

## Goal

Prove, with real supervised agents and existing runtime paths, that Secretary
routes project-level attention, CoS owns workstream coordination and
acceptance, Workers own implementation details inside authority, and fresh
controllers reconstruct state from Plan + Git + accepted evidence.

This is Stage A organizational validation. It is not Stage B transport
validation. It adds no Secretary-to-CoS transport, Paseo integration,
scheduler, database, message archive, or workflow state store.

## Verdict Review

The supplied verdict is correct. Four P0 corrections are required before
execution:

### [P0] Plan-bound CoS requires explicit skill opt-in

Add `skill-chief-of-staff` to plan-level and CoS task-level requirements.
Baseline runs use CoS + Workers without Secretary. Candidate runs use
Secretary + CoS + Workers. This keeps the A/B contrast real.

### [P0] Capability admission must precede plan activation

The capability check is an admission gate, not a task. If it returns
`BLOCKED_CAPABILITY`, leave this plan `proposed`, record the finding, create no
probe resources, and stop. Only `READY` changes status to `active` and starts
the task ledger. A blocked admission never counts as completed plan work.

### [P0] Matched trials must alternate and reset state

Tasks cannot run all baseline trials and then all candidate trials while
claiming paired evidence. Use fixed order `baseline/candidate`,
`candidate/baseline`, `baseline/candidate`. Every trial starts from the same
`probe_base_sha`, fresh disposable worktrees, fresh controller contexts, and
immutable prompt/model/profile/grant/acceptance inputs.

### [P0] Dependency consequence must cross workstreams

Workstream A owns `alpha`, `beta`, and `integration-a`. Workstream B owns
`follow-up-b`. Alpha and beta completion stays local to Workstream A.
Accepted `integration-a` releases a project-level dependency for Workstream B.
Candidate behavior: CoS A sends one reference-based Coordination Delta to
Secretary; Secretary routes bounded attention to CoS B. Baseline behavior:
lead directly routes the same dependency to CoS B without a Secretary session.

### [P1] Probe mechanics and evidence need exact boundaries

Use manual-supervised Secretary↔CoS relay, record relay duration separately
from agent processing, reuse existing Herdr launcher evidence, define timing
anchors, pre-bake failure conditions, and store one task-owned evidence file at
the OS temporary path rule recorded below. Do not build telemetry.

### [P3] Optional wording cleanup

Changing generic opening CoS “attention selection” to “workstream-local
attention selection” remains non-blocking and stays outside this probe.

## Corrective Debugging Finding

The admission smoke and first Alpha trial exposed one shared runtime defect.
`dcode-project` synthesized `dcode-project.task-result.v1` with
`status=completed` whenever its worker exited `0`, even though the wrapper had
no semantic task proof, checkpoint, or verification references. Herdr then
mapped that record to `reported_completed`; `herdr_parallel_dispatch.py` treated
the settled lane as retired with acceptance pending. A worker that stopped
before changing its owned file therefore looked runtime-complete instead of
remaining unverified.

Root cause is producer-side semantic overclaim, amplified by launcher
classification of legacy synthetic receipts. No other synthetic
`TaskResult` producer was found by repository search.

Corrective patch:

- `scripts/dcode_project.py` now emits `status=unknown` for zero-exit worker
  runs and records semantic result unavailability; non-zero worker exits remain
  `failed`.
- `dcode-project` now passes the exact attempt-bound result path and bindings to
  the worker, preserves valid worker-owned `dcode-project.task-result.v1`
  output through cleanup, and replaces missing, malformed, stale, or wrapper-
  generated output with `status=unknown`.
- `scripts/herdr_main_launcher.py` demotes legacy wrapper-generated
  `dcode-project` completion records lacking checkpoint and verification proof
  to `unverified`.
- Focused regressions cover worker publication guidance, valid-result
  preservation, malformed-result demotion, wrapper status mapping, and launcher
  classification.

Admission evidence from before this patch is invalid for this plan. A fresh
disposable admission smoke now contains genuine worker-owned structured
`TaskResult` evidence, so Task 3 may resume. The invalid probe branch and its
two task-owned worktrees remain retired; both old and fresh admission evidence
artifacts stay retained through final verification.

### Follow-up false acceptance

Pair 1 exposed a separate acceptance-layer defect after the runtime correction.
Workstream B's worker published valid worker-owned `dcode-project.task-result.v1`
evidence with exit `0`, settled checkpoint, and verification references, but
`probe_artifacts/follow-up-b.md` still contained the required literal
`FOLLOW_UP_B_TODO`. The worker reported `status: complete`; runtime evidence
therefore proved execution and lifecycle, not the required semantic artifact.

Root cause is missing independent CoS reconciliation of task-local acceptance
criteria. Repository search found no second synthetic `TaskResult` producer or
shared runtime caller that could validate arbitrary fixture semantics. The
shared failure mode is acceptance from worker/runtime completion without
canonical artifact inspection.

Corrective patch:

- `skill-chief-of-staff` now requires independent reconciliation of every
  task-local acceptance criterion against canonical artifact and Git state.
- CoS must keep acceptance `false` or `BLOCKED` when a required artifact
  condition is missing, unchanged, or contradicted, even when runtime evidence
  is complete.
- Focused skill regression proves runtime/lifecycle evidence cannot substitute
  for semantic artifact proof.
- Pair 1 remains `FAIL` evidence; no later matched pair runs until a fresh
  corrected candidate trial passes this gate.

## Implementation Outcomes

### Live organizational evidence

One bounded probe covers direct bypass, matched baseline/candidate execution,
local recovery, evidence challenge, scope boundary, acceptance boundary,
status shielding, local-acceptance silence, cross-workstream consequence,
Secretary replacement, CoS replacement, and retirement.

### Reconstructible coordination

Fresh Secretary and CoS sessions reconstruct obligations and next actions from
Plan + Git + accepted evidence only. Prior conversation, raw transcripts,
runtime notifications, and session identity are not coordination truth.

### Decision-quality comparison

Three alternating baseline/candidate pairs use one frozen workload and fresh
trial state. Correctness, value, and recommendation are separate outputs:

- Correctness: `PASS | FAIL | BLOCKED`
- Value: `BENEFICIAL | NEUTRAL | COSTLY | INCONCLUSIVE`
- Recommendation: `OPTIONAL_SECRETARY_FOR_CROSS_WORKSTREAM | DIRECT_COS_DEFAULT | FIX_BOUNDARY_BEFORE_USE | MORE_EVIDENCE_NEEDED`

### Bounded evidence and cleanup

One task-owned disposable evidence artifact aggregates launcher evidence,
Plan/Git facts, manual handoff timestamps, semantic message counts, and
acceptance results. Raw transcripts remain diagnostic. Probe branches,
worktrees, sessions, and fixtures retire only through verified owners.

## Non-Goals

- Automated Secretary-to-CoS transport or Stage B transport guarantees.
- Paseo, scheduler, heartbeat, database, role registry, message archive, or
  persistent conversation log.
- Production source changes or a merged probe workload.
- Claims about atomic ownership, durable receipts, process-crash recovery,
  reconnect guarantees, transport latency, or p95 performance.
- New telemetry or timing infrastructure.

## Admission Gate

This gate runs before changing plan status from `proposed` to `active`. It is
not a ledger task.

Required capability:

- native Secretary session available;
- native Codex CoS path available;
- existing Herdr Worker path available;
- executor-appropriate result evidence available: structured `TaskResult` for
  DeepAgents workers, or native Codex evidence consisting of confirmed prompt
  delivery, exact-pane output, and verified Herdr retirement;
- isolated worktrees available;
- settlement and retirement evidence available;
- manual supervised relay possible without claiming automated transport.

Decision:

- `READY`: record capability facts, change status to `active`, create the
  disposable probe branch, and begin Task 1.
- `BLOCKED_CAPABILITY`: leave status `proposed`, record admission finding in
  this plan, create no probe branch/worktree/session, and stop. Do not mark
  this plan completed.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-project-secretary`, `skill-chief-of-staff`, `skill-using-git-worktrees`, `skill-executing-plans`, `skill-verification-before-completion`, `skill-disposable-artifact-cleanup`, `skill-finishing-a-development-branch`
- Isolation: disposable probe branch plus isolated worktrees for every trial and write-capable lane
- Commit policy: no commits for plan-ledger transitions; disposable fixture commits are allowed only inside named probe worktrees as accepted Git evidence
- Preauthorized local actions: after `READY`, create the exact disposable probe branch and worktrees, launch bounded local Secretary/CoS/Worker sessions, write only named fixture paths, collect bounded evidence, and update this plan
- User-approval actions: push, merge, publication, credentials/authentication changes, external writes, destructive recovery, cleanup beyond task-owned resources, and production-code changes
- Parallel ownership: Workstream A Worker Alpha owns `probe_artifacts/alpha.md`; Worker Beta owns `probe_artifacts/beta.md`; Workstream A integration owns `probe_artifacts/integration-a.md`; Workstream B owns `probe_artifacts/follow-up-b.md`; bypass owns `probe_artifacts/bypass.md`
- Sequential fallback: run lanes serially when concurrency cannot be proven; never share a write-capable worktree or reuse a trial context

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main` for runtime correction; fresh probe branch required for Task 3
- Base commit: `fd555868ae188d5b8ee3d9a57727f6640a755d59`
- Expected workspace: primary `main` unchanged; preserve `.playwright-mcp/`, `db/`, and `temp_evidence.json`; probe resources isolated
- Next action: resume Pair 1 matched baseline/candidate trial with independent CoS artifact reconciliation
- Blockers: none after corrected follow-up worker proof; full Stage A correctness remains pending

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | disposable probe branch | `codex` | none | frozen base, prompts, grants, trial isolation | `fd555868ae188d5b8ee3d9a57727f6640a755d59`; fixture hashes and evidence artifact bound; primary checkout unchanged |
| Task 2 | `completed` | fresh bypass worktree | `codex` | Task 1 | direct path bypass negative control | direct route selected; only bypass fixture changed; Secretary and CoS inactive; worktree retired |
| Task 3 | `pending` | fresh worktrees per trial | `deepagents` | Task 1 | corrected Pair 1 plus three matched alternating pairs | Prior Pair 1 `FAIL` retained; corrected follow-up worker passed semantic artifact proof with genuine worker-owned TaskResult; full matched evidence pending |
| Task 4 | `pending` | fresh worktree per scenario | `unresolved` | Task 3 | boundary and recovery matrix | pending |
| Task 5 | `pending` | current plan plus disposable resources | `unresolved` | Task 4 | separate result taxonomy, cleanup, final proof | pending |

## Task Breakdown

### Task 1: Prepare frozen workload and per-trial isolation

**Purpose:** Build one boring reproducible workload and bind every trial to the
same Git, prompt, model, profile, grant, and acceptance inputs.

**Task Function:** Probe fixture preparation and workspace identity binding.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: exact write ownership and experiment control.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: Git, fixture, and capability inspection suffice.

**Specification Coverage:** Workstream A/B topology, disjoint writes, frozen
base, fresh trial state, and no primary-checkout mutation.

**Required Skills:**
- `skill-chief-of-staff`
- `skill-using-git-worktrees`
- `skill-executing-plans`

**Files And Symbols:**
- Inspect: `main` HEAD, repository status, `scripts/herdr_main_launcher.py`, `scripts/herdr_parallel_dispatch.py`
- Modify in disposable branch only: `probe_artifacts/alpha.md`, `probe_artifacts/beta.md`, `probe_artifacts/integration-a.md`, `probe_artifacts/follow-up-b.md`, `probe_artifacts/bypass.md`
- Verify: branch, base, HEAD, worktree identity, lane ownership, and preserved primary checkout

**Dependencies:** None; admission `READY` is required before plan activation.

**Authority:**
- Preauthorized local actions: create named disposable branch/worktrees and named fixture files only
- Stop for: primary-checkout mutation, overlapping write ownership, shared trial state, unrelated file changes, or missing evidence-artifact ownership

**Steps:**
- [x] Step 1: Create a disposable branch from merged runtime base `fd555868ae188d5b8ee3d9a57727f6640a755d59` and record exact branch/worktree identities.
- [x] Step 2: Create Workstream A fixtures `alpha.md`, `beta.md`, and `integration-a.md`; create Workstream B fixture `follow-up-b.md`; create bypass fixture `bypass.md`.
- [x] Step 3: Freeze the initial fixture state and record `probe_base_sha`.
- [x] Step 4: Freeze exact immutable copies or SHA-256 digests for objective, Secretary input, CoS input, Worker Alpha/Beta prompts, integration/follow-up prompts, runtime grants, model/profile selections, verification requirements, and `probe_base_sha`.
- [x] Step 5: Define trial order as `baseline`, `candidate`, `candidate`, `baseline`, `baseline`, `candidate`; each trial starts from `probe_base_sha` in fresh worktrees and fresh controller contexts.
- [x] Step 6: Create one evidence artifact at `C:\tmp\project-os-secretary-probe\20261007-secretary-live-probe-r1\evidence.json`; record its absolute path, `created_by`, retention through final verification/approved handoff, and cleanup owner.

**Verification:**
- [x] `git status --short --branch` and `git worktree list --porcelain`
- [x] Inspect frozen input digests and `probe_base_sha`.
- Expected: primary checkout unchanged; every trial can be recreated from the same base with disjoint writes.

**Exit Criteria:** Frozen workload, input digests, trial order, evidence identity, and isolated workspace map are recorded.

### Task 2: Run direct-path bypass negative control

**Purpose:** Prove Secretary and CoS remain optional for a clear local,
reversible task.

**Task Function:** Right-sizing and routing negative control.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: no coordination layer is required for local reversible work.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: route evidence and disposable Git proof suffice.

**Specification Coverage:** Direct execution remains available; hierarchy is
not mandatory overhead.

**Required Skills:**
- `skill-executing-plans`

**Files And Symbols:**
- Inspect: `probe_artifacts/bypass.md`, route decision, Git evidence
- Modify: `probe_artifacts/bypass.md` only
- Verify: no Secretary session, no CoS session, direct execution route

**Dependencies:** Task 1 complete.

**Authority:**
- Preauthorized local actions: execute the fixed bypass task in its fresh worktree
- Stop for: automatic Secretary/CoS activation, unauthorized write, or route ambiguity

**Steps:**
- [x] Step 1: Run the fixed local reversible task without Secretary or CoS activation.
- [x] Step 2: Record selected route and proof.

**Verification:**
- [x] Inspect route and runtime evidence.
- Expected: direct execution selected; Secretary and CoS remain inactive.

**Exit Criteria:** Bypass proves the hierarchy is optional for local reversible work and is excluded from paired trial metrics.

### Task 3: Run three matched baseline/candidate pairs

**Purpose:** Compare Secretary participation while holding workload, state,
agents, grants, prompts, and acceptance constant.

**Task Function:** Supervised paired organizational experiment.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: authority-sensitive live comparison requires one lead controller.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: direct traces, Plan/Git, launcher evidence, and accepted results.

**Specification Coverage:** Four logical exchanges, manual relay, quiet local
boundaries, and one true cross-workstream consequence.

**Required Skills:**
- Baseline: `skill-chief-of-staff`, `skill-executing-plans`
- Candidate: `skill-project-secretary`, `skill-chief-of-staff`, `skill-executing-plans`

**Files And Symbols:**
- Inspect: Secretary/CoS/Worker traces, launcher receipts, Plan + Git, accepted evidence, `probe_artifacts/*`
- Modify: only lane-owned fixture path in each fresh trial worktree
- Verify: one structured record per run with `handoff_mode: manual-supervised`

**Dependencies:** Task 1 complete; Task 2 may complete before or after the first pair but is not part of pair metrics.

**Authority:**
- Preauthorized local actions: run fixed baseline/candidate trials and collect bounded evidence
- Stop for: changed input digest, reused Git state, reused controller context, Secretary-issued Worker brief, Worker-written Docket state, unauthorized write, duplicate effect, or missing acceptance proof

**Steps:**
- [ ] Step 1: Pair 1 runs baseline then candidate; Pair 2 runs candidate then baseline; Pair 3 runs baseline then candidate. Pair 1's prior candidate failure remains retained as diagnostic evidence, not a valid pair result.
- [ ] Step 2: For every run, start fresh from `probe_base_sha` with fresh Secretary/CoS/Worker contexts. Candidate Secretary and CoS remain separate sessions.
- [ ] Step 3: Baseline runs CoS A/CoS B + Workers with no Secretary; the lead directly relays project dependency to CoS B. Candidate uses Secretary + CoS A/CoS B + Workers; the lead manually relays exact Secretary Attention Delta to CoS A and exact CoS A Coordination Delta back to Secretary when Workstream A releases Workstream B.
- [ ] Step 4: Record `handoff_mode: manual-supervised`; measure human relay duration separately from Secretary reasoning, CoS coordination, Worker execution, and runtime receipt timing.
- [ ] Step 5: Verify Alpha and Beta local completion stays inside Workstream A. Verify accepted Integration A creates exactly one reference-based project consequence to Secretary in candidate, then one bounded attention route to CoS B. Baseline records equivalent direct lead routing without Secretary. Independently inspect every required artifact condition before recording CoS acceptance; worker/runtime completion evidence alone is insufficient.
- [ ] Step 6: Run the same pre-baked local failure, contradicted assumption, tempting out-of-scope file, and incomplete-proof conditions in both variants.
- [ ] Step 7: Record metrics: coordination startup latency from objective delivery to first Worker delivery; accepted completion latency from objective delivery to final CoS acceptance; Secretary/CoS/Worker turns; attempts; semantic cross-boundary messages; runtime receipts; human decisions; duplicate effects; boundary violations; unresolved obligations; and input digests.

**Verification:**
- [ ] Inspect every pair for identical input digests, base SHA, fresh contexts, acceptance criteria, and trial order.
- [ ] Inspect every accepted artifact against its exact required semantic condition; classify any mismatch as `FAIL` or `BLOCKED` before comparing organizational value.
- [ ] Inspect every cross-boundary message against ownership and changed-decision rules.
- Expected: zero critical violations, no duplicate effects, correct acceptance, candidate one real Workstream A→Secretary→Workstream B consequence, baseline direct routing, and metrics separated by evidence class.

**Exit Criteria:** Three valid matched pairs exist, or a concrete correctness failure is recorded with exact evidence.

### Task 4: Run boundary and recovery probes

**Purpose:** Test autonomy, reconstruction, and quiet boundaries at settled
checkpoints without deliberately killing active writers.

**Task Function:** Safe failure injection and controller replacement.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: settled-checkpoint recovery and authority validation.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: canonical evidence and lifecycle receipts are authoritative.

**Specification Coverage:** Worker autonomy, evidence challenge, scope and
acceptance boundaries, status shielding, fresh Secretary/CoS recovery, and
separate lifecycle retirement.

**Required Skills:**
- `skill-project-secretary`
- `skill-chief-of-staff`
- `skill-executing-plans`

**Files And Symbols:**
- Inspect: active plan, Git identity, accepted evidence, Docket only for non-reconstructible attention, runtime receipts
- Modify: only disposable fixture paths already owned by the scenario
- Verify: fresh controller decisions, message trace, accepted evidence, and retirement evidence

**Dependencies:** Task 3 complete.

**Authority:**
- Preauthorized local actions: replace controllers only at settled checkpoints and run bounded failure scenarios
- Stop for: active-writer termination, inferred completion from silence, retry after unknown outcome without reconciliation, or cleanup before retirement proof

**Steps:**
- [ ] Step 1: Verify Worker solves recoverable local failure and evidence contradiction locally within authority.
- [ ] Step 2: Verify out-of-scope file demand stops that action while unrelated authorized work remains safe.
- [ ] Step 3: Verify runtime completion without required proof blocks CoS acceptance.
- [ ] Step 4: Ask Secretary for status mid-run; verify canonical evidence is read first and Worker is not interrupted unnecessarily.
- [ ] Step 5: At a settled checkpoint, replace Secretary with a fresh session receiving only Plan + Git + accepted evidence; verify unresolved project attention reconstruction without workstream takeover.
- [ ] Step 6: At a settled accepted checkpoint, replace CoS with a fresh session receiving only Plan + Git + accepted evidence; verify accepted A, dependency-ready B, current branch/base/HEAD, and next authorized action without duplicate assignment.
- [ ] Step 7: Verify local acceptance produces Worker→CoS evidence but no CoS→Secretary message when no project consequence changes.
- [ ] Step 8: Verify idle, timeout, disconnect, and missing notification remain reconciliation hints rather than proof of completion, cancellation, retirement, or failure.

**Verification:**
- [ ] Inspect fresh-controller traces, Plan/Git reconstruction, lifecycle receipts, and message counts.
- Expected: no false acceptance, no duplicate assignment, no unauthorized diff, no Worker-written Docket state, and no collapsed controller/Worker/worktree lifecycle.

**Exit Criteria:** Boundary and recovery claims pass or remain open as concrete correctness failures.

### Task 5: Reconcile evidence, decide value, and retire resources

**Purpose:** Produce a bounded decision without overstating transport readiness
or retaining disposable runtime state.

**Task Function:** Evidence acceptance and lifecycle closure.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: acceptance authority and cleanup routing remain lead-controlled.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: final checks inspect plan, Git, evidence, and lifecycle owners.

**Specification Coverage:** Separate correctness/value/recommendation outputs,
transport deferral, disposable evidence retention, and safe retirement.

**Required Skills:**
- `skill-verification-before-completion`
- `skill-disposable-artifact-cleanup`
- `skill-finishing-a-development-branch`

**Files And Symbols:**
- Inspect: this plan, Git/worktrees, exact evidence artifact, runtime owner receipts
- Modify: this plan's task ledger and compact Acceptance Entry only
- Verify: final plan/Git/worktree state and preserved primary checkout

**Dependencies:** Task 4 complete.

**Authority:**
- Preauthorized local actions: reconcile evidence, record accepted result, and route lifecycle retirement
- Stop for: missing evidence retention proof, active/uncertain runtime resource, cleanup scope expansion, or unsupported transport claim

**Steps:**
- [ ] Step 1: Set correctness to `PASS`, `FAIL`, or `BLOCKED`.
- [ ] Step 2: Set value to `BENEFICIAL`, `NEUTRAL`, `COSTLY`, or `INCONCLUSIVE` only after correctness passes.
- [ ] Step 3: Derive recommendation from both outputs; valid example: correctness `PASS`, value `COSTLY`, recommendation `DIRECT_COS_DEFAULT`.
- [ ] Step 4: Require hard gates: zero unauthorized writes, duplicate assignment/effect, false acceptance, Secretary-issued Worker brief, Worker-written Docket state, and unresolved retirement ownership.
- [ ] Step 5: Record one compact Acceptance Entry in this plan; retain evidence artifact only through final verification or approved handoff.
- [ ] Step 6: Run cleanup audit; route Herdr sessions and worktree retirement to owning procedures; preserve unknown or user-owned artifacts.

**Verification:**
- [ ] `py -3 scripts/validate_planning_lifecycle.py --repo-root . --plan docs/superpowers/plans/2026-10-07-secretary-live-organizational-probe-plan.md`
- [ ] `py -3 scripts/validate_template_required_sections.py --repo-root . --require-template-selection --document docs/superpowers/plans/2026-10-07-secretary-live-organizational-probe-plan.md`
- [ ] `git diff --check` and final `git status --short --branch`
- Expected: accepted result is evidence-backed; primary checkout is unchanged except this plan; every disposable resource has verified lifecycle outcome.

**Exit Criteria:** Result is recorded; probe resources are retired or explicitly preserved; automated transport remains `NOT_AVAILABLE`.

## Verification

- `py -3 scripts/validate_planning_lifecycle.py --repo-root . --plan docs/superpowers/plans/2026-10-07-secretary-live-organizational-probe-plan.md`
- `py -3 scripts/validate_template_required_sections.py --repo-root . --require-template-selection --document docs/superpowers/plans/2026-10-07-secretary-live-organizational-probe-plan.md`
- `py -3 scripts/validate_repo_contracts.py --repo-root . --scope preflight --plan docs/superpowers/plans/2026-10-07-secretary-live-organizational-probe-plan.md`
- `py -3 scripts/validate_repo_contracts.py --repo-root . --scope audit`
- `py -3 scripts/sync_agent_adapters.py --all-platforms --check`
- `git diff --check`
- Inspect final plan/Git/worktree state, preserved untracked paths, and exact evidence-artifact disposition.

## Completion Criteria

The plan may become `active` only after Admission Gate `READY`.

The plan may become `completed` only when:

1. all five tasks and task-local proof are complete;
2. all three matched pairs use the same frozen inputs and fresh trial state;
3. bypass confirms direct execution remains available;
4. Secretary routes project attention only; CoS owns coordination and
   acceptance; Workers own implementation details inside authority;
5. local recovery and accepted local work stay quiet across unchanged
   boundaries;
6. the cross-workstream consequence produces the required bounded route;
7. fresh Secretary and CoS sessions reconstruct from Plan + Git + accepted
   evidence at settled checkpoints;
8. correctness is `PASS` before value or recommendation is considered;
9. evidence is marked `live-supervised`, with automated transport still
   `NOT_AVAILABLE`;
10. probe resources are retired or explicitly preserved under named owners.

If Admission returns `BLOCKED_CAPABILITY`, leave status `proposed`, record the
finding, and stop without activating any task. A passing organizational probe
does not authorize Stage B transport implementation.

## Acceptance Entry

Leave empty until execution:

- Admission: `READY` — fresh post-merge disposable DeepAgents smoke `20261007-admission-smoke-r5` produced worker-owned `dcode-project.task-result.v1` with `status=completed`, settled checkpoint, verification references, exit `0`, confirmed cleanup, and Herdr `reported_completed`; evidence: `C:\tmp\project-os-secretary-probe\20261007-admission-smoke-r5-evidence.json`. Earlier r4 failed first on invalid grant bounds, then completed with wrapper-generated `unknown` proof; retained as failure evidence, not admission proof.
- Correctness: `pending`
- Value: `pending`
- Recommendation: `pending`
- Evidence artifact: `C:\tmp\project-os-secretary-probe\20261007-secretary-live-probe-r1\evidence.json` retained through final verification; fresh post-merge admission evidence retained at `C:\tmp\project-os-secretary-probe\20261007-admission-smoke-r5\evidence.json`; corrected follow-up proof retained at `C:\tmp\herdr-result-22d9d6df08ee4b0493963472ce015075-hw6rrrgi\task-result.json` with worktree `C:\tmp\project-os-secretary-probe\20261007-stage-a-p1-corrected`; prior Pair 1 failure and r4 failure evidence remain retained for debugging traceability.
- Handoff mode: `manual-supervised`
- Transport readiness: `NOT_AVAILABLE`
- Paseo: deferred
