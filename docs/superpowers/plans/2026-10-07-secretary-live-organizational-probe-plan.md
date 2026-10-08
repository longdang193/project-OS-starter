---
layer: change
artifact_type: plan
contract_version: "1"
status: completed
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
runtime trial base plus the same frozen fixture snapshot, fresh disposable
worktrees, fresh controller contexts, and immutable
prompt/model/profile/grant/acceptance inputs. The runtime trial base must
contain the corrected wrapper and launcher; the fixture snapshot may come from
the earlier disposable probe commit.

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

### Probe launch working-directory defect

The first fresh Pair 2 Alpha attempt was invalid: the command supplied the
candidate path as `--repository-identity` but launched `dcode-project` from the
primary checkout. `dcode-project` resolves its active repository from process
CWD; `--repository-identity` binds attempt evidence and does not select the
worker checkout. The worker therefore saw no `probe_artifacts/alpha.md`,
published a genuine failed result, and changed no file.

Root cause is launch-boundary misuse, not worker or runtime behavior. The same
caller pattern is unsafe for every worker and controller session. Corrective
guard: launch each process with its target worktree as CWD, then assert
`git -C <cwd> rev-parse --show-toplevel` equals the bound repository identity
before accepting output. Retain the invalid attempt as diagnostic evidence and
do not reuse its attempt or worktree state.

### Worker publication instruction gap

Pair 2 Alpha r10 changed its owned artifact and reported publication in final
text, but the result path contained only the wrapper-generated `unknown`
record. No worker-owned receipt or publisher error existed. The successful
Pair 1 prompt named `scripts.project_os_runtime.results.publish_task_result`
explicitly; the weaker prompt did not. Treat final text as untrusted: require
the task to call the existing publisher, preserve exact bindings, and reread
the result path before reporting completion. Retain r10 as invalid evidence and
restart from fresh state.

### Probe grant-binding typo

The next Pair 2 Beta attempt used a manually copied 63-character grant digest.
The worker completed and changed only its owned fixture, but the result
publisher rejected the binding and emitted no valid worker TaskResult. This is
invalid evidence and the mutated worktree must not be reused.

Root cause is unvalidated manual launch input. Before every launch, compare the
grant digest against the frozen 64-character value and reject the command when
length or value differs. Treat missing or malformed publication as a failed
trial, preserve its receipt/logs, and restart from fresh state.

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

### Composite trial-base mismatch

The first rerun after PR #56 used the recorded fixture commit
`c5f70076b6b0e3f5e8c9bccb75662f5d9433c61e` as the whole trial base. That commit
contains the frozen fixtures but predates the corrected runtime on PR head
`a170b759eecbe8b4cf6fd70a319daa8bf2977f55`. Workers therefore ran against an
old `dcode_project.py`; wrapper context did not include the attempt-bound
semantic-result publication contract, and receipts were synthetic
`producer=dcode-project` records with no checkpoint or verification references.
The Alpha artifact change is retained as invalid diagnostic evidence.

Root cause is conflating fixture snapshot identity with runtime trial-base
identity. No product behavior change is authorized by this finding.

Corrective patch:

- Every trial worktree starts at runtime trial base
  `a170b759eecbe8b4cf6fd70a319daa8bf2977f55` or its later accepted descendant.
- Copy only the five frozen fixture files from the fixture snapshot commit
  `c5f70076b6b0e3f5e8c9bccb75662f5d9433c61e` into that worktree before launch.
- Record both `runtime_trial_base_sha` and `fixture_snapshot_sha` in each
  evidence record; never call the fixture commit alone `probe_base_sha`.
- Reject any run whose receipt lacks worker-owned producer, settled checkpoint,
  non-empty verification references, or exact bindings, even when artifact Git
  proof passes.

### Controller write-boundary violation

The first candidate CoS acceptance session was instructed to inspect only, but
it rewrote `probe_artifacts/integration-a.md` in the worker worktree. The
resulting acceptance output is invalid because controller inspection changed
canonical evidence. The invalid candidate worktree and transcript remain
retained as diagnostic evidence.

Root cause is relying on task wording to make a write-capable controller
session read-only. The same dcode-project filesystem tools remain available to
Secretary and CoS sessions, so instruction-only isolation is not sufficient.

Corrective patch:

- Run every Secretary/CoS inspection or acceptance session from a separate
  disposable audit snapshot populated from the candidate worktree at a settled
  checkpoint; never run controller inspection in a worker write worktree.
- Hash audit snapshot inputs before the session and verify no audit file changes
  afterward. Controller output is valid only when snapshot integrity passes.
- Keep worker sessions as the only write-capable agents for fixture paths;
  independently reconcile their artifacts from the unchanged candidate
  worktree after controller output.
- Classify any controller write, even semantically harmless, as a candidate
  correctness failure and rerun the pair from fresh state.

### Task 3 semantic acceptance mismatch

Task 4 CoS replacement exposed a prior evidence contradiction. The recorded
Pair 3 candidate output claimed Integration A acceptance and routed
`follow-up-b-ready`, but its canonical `probe_artifacts/integration-a.md`
still contained `status: pending`. The artifact also lacked the required
`integration-a-complete` replacement; the matching text appeared only in the
requirement sentence. The fresh CoS repeated the false acceptance when given
the same Plan plus artifact state.

Root cause is evidence assembly and controller reconciliation: the prior
candidate snapshot was treated as accepted from runtime/plan claims without
checking the exact artifact status and replacement condition. Repository-wide
inspection found the same contradictory pending fixture in Pair 1 fresh,
Pair 2 failed attempts, and Pair 3 candidate/audit snapshots; accepted Pair 1
`r7`, Pair 2 `r13`, and baseline snapshots contain the completed condition.
This is not a runtime producer defect, and no production-code change is
justified.

Corrective action:

- invalidate Pair 3 candidate acceptance and all downstream evidence that
  depends on its Integration A consequence;
- require exact semantic checks (`status: complete`, required replacement,
  evidence references, and dependency marker) before CoS acceptance;
- rerun the matched Pair 3 candidate/baseline sequence from fresh state before
  resuming Task 4 Step 6 or later;
- retain the false-acceptance transcripts and contradictory snapshots as
  diagnostic evidence, never as accepted proof.

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
- Base commit: `a170b759eecbe8b4cf6fd70a319daa8bf2977f55` (runtime trial base)
- Fixture snapshot: `c5f70076b6b0e3f5e8c9bccb75662f5d9433c61e`
- Expected workspace: primary `main` unchanged; preserve `.playwright-mcp/`, `db/`, and `temp_evidence.json`; probe resources isolated
- Next action: preserve accepted evidence and defer Git/runtime retirement to owning procedures
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | disposable probe branch | `codex` | none | frozen base, prompts, grants, trial isolation | `fd555868ae188d5b8ee3d9a57727f6640a755d59`; fixture hashes and evidence artifact bound; primary checkout unchanged |
| Task 2 | `completed` | fresh bypass worktree | `codex` | Task 1 | direct path bypass negative control | direct route selected; only bypass fixture changed; Secretary and CoS inactive; worktree retired |
| Task 3 | `completed` | fresh worktrees per trial | `deepagents` | Task 1 | corrected Pair 1 plus three matched alternating pairs | Pair 3 rerun passed with identical Integration A and Follow-up B task hashes, worker-owned receipts, semantic reconciliation, and fresh audit snapshots |
| Task 4 | `completed` | fresh worktree per scenario | `deepagents` | Task 3 | boundary and recovery matrix | Prior Steps 1–3 retained; fresh status/recovery/silence probes passed; lifecycle classification suite `19 passed, 169 deselected` |
| Task 5 | `completed` | current plan plus disposable resources | `codex` | Task 4 | separate result taxonomy, cleanup, final proof | correctness `PASS`; value `INCONCLUSIVE`; recommendation `MORE_EVIDENCE_NEEDED`; evidence and retirement ownership reconciled |

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
- [x] Step 3: Freeze the initial fixture state at `fixture_snapshot_sha` and record the runtime trial base separately.
- [x] Step 4: Freeze exact immutable copies or SHA-256 digests for objective, Secretary input, CoS input, Worker Alpha/Beta prompts, integration/follow-up prompts, runtime grants, model/profile selections, verification requirements, `runtime_trial_base_sha`, and `fixture_snapshot_sha`.
- [x] Step 5: Define trial order as `baseline`, `candidate`, `candidate`, `baseline`, `baseline`, `candidate`; each trial starts from `runtime_trial_base_sha` in a fresh worktree, receives only the frozen fixture snapshot, and uses a fresh controller context.
- [x] Step 6: Create one evidence artifact at `C:\tmp\project-os-secretary-probe\20261007-secretary-live-probe-r1\evidence.json`; record its absolute path, `created_by`, retention through final verification/approved handoff, and cleanup owner.

**Verification:**
- [x] `git status --short --branch` and `git worktree list --porcelain`
- [x] Inspect frozen input digests, `runtime_trial_base_sha`, and `fixture_snapshot_sha`.
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
- [x] Step 1: Pair 1 runs baseline then candidate; Pair 2 runs candidate then baseline; Pair 3 runs baseline then candidate. Pair 1's prior candidate failure remains retained as diagnostic evidence, not a valid pair result.
- [x] Step 2: For every run, start fresh from `runtime_trial_base_sha`, restore only the frozen fixture snapshot, and use fresh Secretary/CoS/Worker contexts. Candidate Secretary and CoS remain separate sessions.
- [x] Step 2a: Launch every worker, Secretary, and CoS process with its target disposable worktree as process CWD; verify `git -C <cwd> rev-parse --show-toplevel` matches `--repository-identity` before launch and before accepting output. A matching binding without matching CWD is invalid evidence.
- [x] Step 2b: Validate exact task, assignment, attempt, and 64-character grant bindings against the frozen input record before launch; never hand-copy an unverified digest.
- [x] Step 3: Baseline runs CoS A/CoS B + Workers with no Secretary; the lead directly relays project dependency to CoS B. Candidate uses Secretary + CoS A/CoS B + Workers; run Secretary/CoS inspection sessions from integrity-checked audit snapshots, and manually relay exact Secretary Attention Delta to CoS A and exact CoS A Coordination Delta back to Secretary when Workstream A releases Workstream B.
- [x] Step 4: Record `handoff_mode: manual-supervised`; retain separate Secretary, CoS, Worker, and runtime evidence classes. Human relay timing remains qualitative because no automated transport is available.
- [x] Step 5: Verify Alpha and Beta local completion stays inside Workstream A. Verify accepted Integration A creates exactly one reference-based project consequence to Secretary in candidate, then one bounded attention route to CoS B. Baseline records equivalent direct lead routing without Secretary. Independently inspect every required artifact condition before recording CoS acceptance; worker/runtime completion evidence alone is insufficient. Reject controller output when its audit snapshot changed.
- [x] Step 6: The fixed local-recovery, contradicted-assumption, out-of-scope, and incomplete-proof conditions were exercised in both variants through fixture instructions and independent CoS reconciliation.
- [x] Step 7: Record available metrics by evidence class: worker receipts, attempts, relay mode, boundary violations, duplicate effects, unchanged audit snapshots, and input identities. Exact latency comparison is deferred because relay is manual and automated transport is unavailable; Task 5 owns final value/recommendation judgment.

**Verification:**
- [x] Inspect every pair for identical input digests, base SHA, fresh contexts, acceptance criteria, and trial order.
- [x] Inspect every accepted artifact against its exact required semantic condition; classify any mismatch as `FAIL` or `BLOCKED` before comparing organizational value.
- [x] Inspect every cross-boundary message against ownership and changed-decision rules.
- Expected: zero critical violations, no duplicate effects, correct acceptance, candidate one real Workstream A→Secretary→Workstream B consequence, baseline direct routing, and metrics separated by evidence class.

**Exit Criteria:** Three valid matched pairs exist, or a concrete correctness failure is recorded with exact evidence.

**Pair 1 Evidence:**

- Baseline: `C:\tmp\project-os-secretary-probe\20261007-stage-a-p1-baseline-r5`; runtime base `a170b759eecbe8b4cf6fd70a319daa8bf2977f55`; fixture snapshot `c5f70076b6b0e3f5e8c9bccb75662f5d9433c61e`.
- Candidate: `C:\tmp\project-os-secretary-probe\20261007-stage-a-p1-candidate-r7`; same runtime base and fixture snapshot; Secretary → CoS A → Workers and CoS A → Secretary → CoS B relay observed.
- Controller audit: `C:\tmp\project-os-secretary-probe\20261007-stage-a-p1-candidate-r7-cos-audit`; snapshot integrity passed before and after CoS A, Secretary, and CoS B sessions; no audit writes.
- Worker receipts: `C:\tmp\herdr-result-p1a-r5-202610072245`, `C:\tmp\herdr-result-p1b-r5-202610072255`, `C:\tmp\herdr-result-p1i-r5-202610072305`, `C:\tmp\herdr-result-p1f-r5-202610072315`, `C:\tmp\herdr-result-p1ra-r7-202610072400`, `C:\tmp\herdr-result-p1rb-r7-202610072410`, `C:\tmp\herdr-result-p1ri-r7-202610072420`, and `C:\tmp\herdr-result-p1rf-r7-202610072430`; all are worker-owned `deepagents-worker` receipts with settled checkpoints and non-empty verification evidence.
- Acceptance: `PASS` for Pair 1. Invalid diagnostics retained: PR-head-missing-fixtures baseline attempts and candidate `r6` controller-write violation.

**Pair 2 Evidence:**

- Baseline: `C:\tmp\project-os-secretary-probe\20261007-stage-a-p2-baseline-r14`; candidate: `C:\tmp\project-os-secretary-probe\20261007-stage-a-p2-candidate-r13`; both use runtime base `a170b759eecbe8b4cf6fd70a319daa8bf2977f55` and fixture snapshot `c5f70076b6b0e3f5e8c9bccb75662f5d9433c61e`.
- Candidate controller audits: `...p2-candidate-r13-secretary-audit`, `...p2-candidate-r13-cosa-audit`, `...p2-candidate-r13-secretary-relay-audit`, and `...p2-candidate-r13-cosb-audit`; all remained unchanged after read-only sessions.
- Worker receipts: `C:\tmp\herdr-result-p2ca-r13-202610080150`, `C:\tmp\herdr-result-p2cb-r13-202610080210`, `C:\tmp\herdr-result-p2ci-r13-202610080230`, `C:\tmp\herdr-result-p2cf-r13-202610080310`, `C:\tmp\herdr-result-p2ba-r14-202610080330`, `C:\tmp\herdr-result-p2bb-r14-202610080350`, `C:\tmp\herdr-result-p2bi-r14-202610080410`, and `C:\tmp\herdr-result-p2bf-r14-202610080430`; all are worker-owned `deepagents-worker` receipts with completed status, settled checkpoints, non-empty verification references, and empty remaining work.
- Baseline audits: `...p2-baseline-r14-cosa-audit` and `...p2-baseline-r14-cosb-audit`; both remained unchanged. Acceptance: `PASS`.
- Invalid diagnostics retained: candidate `r8` wrong CWD, candidate `r8` malformed grant digest, candidate `r10` missing worker publication, and empty failed setup `r11`; none reused.

**Pair 3 Evidence:**

- Baseline: `C:\tmp\project-os-secretary-probe\20261007-stage-a-p3-baseline-r18b`; candidate: `C:\tmp\project-os-secretary-probe\20261007-stage-a-p3-candidate-r17b`; both use runtime base `a170b759eecbe8b4cf6fd70a319daa8bf2977f55` and fixture snapshot `c5f70076b6b0e3f5e8c9bccb75662f5d9433c61e`.
- Fresh candidate audits: `...p3-rerun-candidate-secretary-audit`, `...p3-rerun-candidate-cosa-audit`, and `...p3-rerun-candidate-cosb-audit`; fresh baseline audits: `...p3-rerun-baseline-cosa-audit` and `...p3-rerun-baseline-cosb-audit`. Plan, fixture, and runtime content matched source snapshots after each read-only session.
- Worker receipts: `C:\tmp\herdr-result-p3-rerun-candidate-integration\task-result.json`, `C:\tmp\herdr-result-p3-rerun-baseline-integration\task-result.json`, `C:\tmp\herdr-result-p3-rerun-candidate-follow-up\task-result.json`, and `C:\tmp\herdr-result-p3-rerun-baseline-follow-up\task-result.json`; all are worker-owned `deepagents-worker` receipts with completed status, settled checkpoints, non-empty verification references, and empty remaining work.
- Matched input proof: Integration A task hash `bf3059eeff0f166e39adf3ee43c88335077e7c6aad69524a5affa7f9832ae0b0`; Follow-up B task hash `53191242c22ff160e676a60dd69fd1cca6085165c97d76495b703fbe51555e9a`; candidate and baseline hashes match exactly.
- Acceptance: `PASS`. Three matched pairs pass organizational correctness; Task 4 boundary/recovery evidence also passes.

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
- [x] Step 1: Verify Worker solves recoverable local failure and evidence contradiction locally within authority.
- [x] Step 2: Verify out-of-scope file demand stops that action while unrelated authorized work remains safe.
- [x] Step 3: Verify runtime completion without required proof blocks CoS acceptance.
- [x] Step 4: Ask Secretary for status mid-run; verify canonical evidence is read first and Worker is not interrupted unnecessarily.
- [x] Step 5: At a settled checkpoint, replace Secretary with a fresh session receiving only Plan + Git + accepted evidence; verify unresolved project attention reconstruction without workstream takeover.
- [x] Step 6: At a settled accepted checkpoint, replace CoS with a fresh session receiving only Plan + Git + accepted evidence; verify accepted A, dependency-ready B, current branch/base/HEAD, and next authorized action without duplicate assignment.
- [x] Step 7: Verify local acceptance produces Worker→CoS evidence but no CoS→Secretary message when no project consequence changes.
- [x] Step 8: Verify idle, timeout, disconnect, and missing notification remain reconciliation hints rather than proof of completion, cancellation, retirement, or failure.

**Verification:**
- [x] Inspect fresh-controller traces, Plan/Git reconstruction, lifecycle receipts, and message counts.
- Expected: no false acceptance, no duplicate assignment, no unauthorized diff, no Worker-written Docket state, and no collapsed controller/Worker/worktree lifecycle.

**Exit Criteria:** Boundary and recovery claims pass with no unresolved correctness failure.

**Task 4 Evidence:**

- Prior Steps 1–3: `C:\tmp\project-os-secretary-probe\20261007-task4-r1`; local recovery passed, out-of-scope write was refused, and proof-less runtime exit classified as `unknown` rather than accepted completion.
- Fresh status and recovery: `C:\tmp\project-os-secretary-probe\20261008-task4-r2-status\session-output.txt`, `C:\tmp\project-os-secretary-probe\20261007-stage-a-p3-rerun-candidate-secretary-audit\session-output.txt`, `C:\tmp\project-os-secretary-probe\20261007-stage-a-p3-rerun-candidate-cosa-audit\session-output.txt`, `C:\tmp\project-os-secretary-probe\20261007-stage-a-p3-rerun-candidate-cosb-audit\session-output.txt`, `C:\tmp\project-os-secretary-probe\20261007-stage-a-p3-rerun-baseline-cosa-audit\session-output.txt`, and `C:\tmp\project-os-secretary-probe\20261007-stage-a-p3-rerun-baseline-cosb-audit\session-output.txt`; active ownership preserved, accepted state reconstructed, and no controller writes occurred.
- Fresh quiet boundary: `C:\tmp\project-os-secretary-probe\20261008-task4-r2-silence\session-output.txt`; `NO_ATTENTION`, `message_count=0`, and `reason=local_acceptance_without_project_consequence`.
- Lifecycle classification: focused `tests/test_herdr_main_launcher.py` selection passed `19 passed, 169 deselected`; idle, timeout, disconnect, and missing-notification states remain reconciliation hints.
- Aggregate evidence: `C:\tmp\project-os-secretary-probe\20261008-task4-r2\evidence.json`; handoff mode `manual-supervised`; automated transport `NOT_AVAILABLE`.
- Acceptance: `PASS`.

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
- [x] Step 1: Set correctness to `PASS`, `FAIL`, or `BLOCKED` — `PASS`; Tasks 3 and 4 passed all hard correctness gates.
- [x] Step 2: Set value to `BENEFICIAL`, `NEUTRAL`, `COSTLY`, or `INCONCLUSIVE` only after correctness passes — `INCONCLUSIVE`; no transport latency, relay overhead, or performance value was measured or in scope.
- [x] Step 3: Derive recommendation from both outputs — `MORE_EVIDENCE_NEEDED`; correctness passed, but value remains unmeasured while automated transport is `NOT_AVAILABLE`.
- [x] Step 4: Require hard gates — passed: zero unauthorized writes, duplicate assignment/effect, false acceptance, Secretary-issued Worker brief, Worker-written Docket state, and unresolved retirement ownership.
- [x] Step 5: Record one compact Acceptance Entry in this plan; retain evidence artifact through final verification and approved handoff.
- [x] Step 6: Run cleanup audit; preserve accepted and diagnostic evidence, preserve unknown/user-owned paths, and route Herdr session retirement to Herdr plus worktree retirement to `skill-finishing-a-development-branch`; no destructive cleanup performed.

**Verification:**
- [x] `py -3 scripts/validate_planning_lifecycle.py --repo-root . --plan docs/superpowers/plans/2026-10-07-secretary-live-organizational-probe-plan.md`
- [x] `py -3 scripts/validate_template_required_sections.py --repo-root . --require-template-selection --document docs/superpowers/plans/2026-10-07-secretary-live-organizational-probe-plan.md`
- [x] `git diff --check` and final `git status --short --branch`
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

Record during execution:

- Admission: `READY` — fresh post-merge disposable DeepAgents smoke `20261007-admission-smoke-r5` produced worker-owned `dcode-project.task-result.v1` with `status=completed`, settled checkpoint, verification references, exit `0`, confirmed cleanup, and Herdr `reported_completed`; evidence: `C:\tmp\project-os-secretary-probe\20261007-admission-smoke-r5-evidence.json`. Earlier r4 failed first on invalid grant bounds, then completed with wrapper-generated `unknown` proof; retained as failure evidence, not admission proof.
- Correctness: `PASS`
- Value: `INCONCLUSIVE` — correctness passed, but transport latency, relay overhead, and performance value were explicitly out of scope; automated transport is `NOT_AVAILABLE`.
- Recommendation: `MORE_EVIDENCE_NEEDED` — do not promote Secretary routing to a default or authorize Stage B transport from this probe.
- Pair evidence: Task 3 `PASS` across Pairs 1–3; Task 4 boundary/recovery `PASS`; Task 5 cleanup audit passed.
- Hard gates: `PASS` — no unauthorized writes, duplicate assignment/effect, false acceptance, missing Secretary-issued Worker brief, Worker-written Docket state, or unresolved retirement owner.
- Cleanup disposition: accepted aggregate evidence and invalid diagnostics remain retained through approved handoff; `.playwright-mcp/`, `db/`, and `temp_evidence.json` remain preserved as unknown/user-owned paths; Herdr sessions and Git worktrees remain routed to their owning procedures because no destructive retirement authorization was supplied.
- Evidence artifact: `C:\tmp\project-os-secretary-probe\20261007-secretary-live-probe-r1\evidence.json` retained through final verification; fresh post-merge admission evidence retained at `C:\tmp\project-os-secretary-probe\20261007-admission-smoke-r5\evidence.json`; Pair 3 and Task 4 aggregate evidence retained at `C:\tmp\project-os-secretary-probe\20261008-task4-r2\evidence.json`; corrected follow-up proof retained at `C:\tmp\herdr-result-22d9d6df08ee4b0493963472ce015075-hw6rrrgi\task-result.json` with worktree `C:\tmp\project-os-secretary-probe\20261007-stage-a-p1-corrected`; prior invalid diagnostics remain retained for debugging traceability.
- Handoff mode: `manual-supervised`
- Transport readiness: `NOT_AVAILABLE`
- Paseo: deferred
- Task 5 result: correctness `PASS`; value `INCONCLUSIVE`; recommendation `MORE_EVIDENCE_NEEDED`; plan status `completed`.
