---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
layer: change
name: managed-invocation-semantic-provenance-closure
targets:
  - scripts/secretary_live_runtime.py
  - scripts/herdr_main_launcher.py
  - scripts/benchmark_secretary_architecture.py
  - scripts/benchmark_completion_monitoring.py
  - tests/test_secretary_live_runtime.py
  - tests/test_herdr_main_launcher.py
  - tests/test_secretary_benchmark.py
  - tests/test_benchmark_completion_monitoring.py
  - .github/workflows/runtime-contracts.yml
  - artifacts/completion-monitoring/normal-invocation-finalization-final.json
---

# Managed Invocation Semantic Provenance Closure

## Goal

Close the final semantic-truth gap in normal Secretary invocation without
starting another coordination convergence cycle. The final scope claim is
**“Managed Invocation Semantic Provenance Closure is complete.”** A semantic
answer is accepted only when it is attributable to the submitted attempt and assistant-owned;
diagnostic or cleanup failures cannot erase independently proven work; every
serialized result projection agrees; deterministic contract fixtures do not
claim measurement; and two bounded live probes provide fresh closure evidence.

This plan preserves the completed lifecycle, ownership, cleanup, identity, and
resource-recovery work recorded in
`docs/superpowers/plans/2026-10-12-normal-invocation-correlation-and-finalization-closure-plan.md`.

GitHub ruleset administration, formal GitHub review-state persistence, and
private launcher API decoupling remain separate follow-up work. They are not
required for this semantic-closure patch.

## Implementation Outcomes

### Attempt-bound assistant-response provenance

`_observe_submitted_codex()` and the existing semantic-content adapter use an
existing structured TaskResult/runtime result identity whenever available. The
terminal compatibility path may publish content only when assignment/attempt
identity, post-submit freshness, assistant/result ownership, and terminal
completion are all proven. Prompt wording, bullets, screen freshness, and
answer-like appearance never establish authorship.

The provenance hierarchy is explicit: (1) a correlated `TaskResult` with
matching `assignment_id`/`attempt_id`, an accepted producer/source, and a
semantic content/result reference is authoritative; (2) a structured runtime
result/message attributable to the current attempt with explicit
assistant/result ownership is authoritative; (3) an attempt-bound
result/completion identity that was absent or different at the pre-submit
anchor and resolves to semantic assistant content is authoritative; and (4)
terminal rendering is only a compatibility adapter after authorship is proven
elsewhere. If no structured ownership evidence exists, terminal-only output is
`unavailable`; wording, bullets, screen freshness, and answer-like appearance
never change that result.

### One canonical semantic decision and derived projections

`semantic_outcome` becomes the internal canonical semantic decision. The
compatibility `result` projection is derived from that decision once before
serialization. Observation, execution, and finalization errors remain separate
evidence scopes; an observation failure cannot downgrade a correlated reported
TaskResult, and cleanup uncertainty cannot erase its content.

### Truthful benchmark scope and evidence classification

The misleading Secretary `measure` mode is retired because its current fields
are not independently observed. `benchmark_secretary_architecture.py` remains
the deterministic contract fixture; `benchmark_completion_monitoring.py`
remains the fake-boundary baseline/candidate measurement harness and fails
nonzero on incorrect rows. The existing completion-monitoring artifact is
explicitly treated as fixture/fake-boundary correctness evidence, not as a
production performance claim.

### Fresh bounded live closure evidence

One simple exact-nonce invocation and one multiline/bullet parser-boundary
invocation run in a disposable task-owned worktree. Each records the exact
candidate SHA, runtime identities, submission anchor, semantic projections,
timings, poll/command counts, cleanup state, and owned-resource retirement.
The probes prove functionality and closure only; they do not support p95/p99
or other performance claims.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`, `skill-verification-before-completion`
- Isolation: `fresh managed worktree` from the verified `origin/main` base; use a separate disposable worktree for live probes
- Commit policy: `checkpoint commits are created by the lead after task-local acceptance`; no push, merge, GitHub ruleset mutation, or review-state publication is part of this plan
- Preauthorized local actions: create the implementation worktree, inspect and edit listed files, add focused regression tests, retire the declared local benchmark mode, run repository validators, generate sanitized local evidence, and run two bounded live probes without repository mutation
- User-approval actions: push, merge, GitHub ruleset or review-state changes, external authentication, destructive recovery, deletion of shared resources, dependency changes, or scope expansion
- Parallel ownership: none; provenance, normalization, benchmark, evidence, and live-probe tasks share contracts and execute sequentially
- Sequential fallback: complete Tasks 1 through 5 in order with the lead controller as the sole plan-ledger writer

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/managed-invocation-semantic-provenance-closure`
- Base commit: `f6f0bcf0bd5e4289eb872e1cce43038bcf7ece7d` (`origin/main` at plan drafting)
- Expected workspace: `clean implementation worktree`; preserve the primary checkout and all completed historical plans
- Next action: none; retain the exact candidate and sanitized live receipt as closure evidence
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | implementation worktree | `codex` | none | prompt/user text is never accepted without assistant provenance; fast attributed completion remains reported | `tests/test_secretary_live_runtime.py`; focused suite passed |
| Task 2 | `completed` | implementation worktree | `codex` | Task 1 | semantic projections agree; observation/finalization errors preserve authoritative work | `tests/test_secretary_live_runtime.py`; focused suite passed |
| Task 3 | `completed` | implementation worktree | `codex` | Task 2 | contract fixture and fake-boundary measurement modes are distinct; incorrect validation exits nonzero | contract exit `0`; completion-monitor exit `0`; CI measure mode retired |
| Task 4 | `completed` | implementation worktree | `codex` | Task 3 | existing artifact is classified without performance overclaim; exact-SHA evidence is reconciled | historical JSON parse passed; fake-boundary scope preserved |
| Task 5 | `completed` | disposable probe worktree | `codex` | Tasks 1–4 | both live probes satisfy semantic, cleanup, ownership, and no-mutation gates | candidate `c250342fefa36154513cf5cfb9c39b7ef13bec34`; Probe A and Probe B passed; sanitized evidence recorded outside repo |

## Task Breakdown

### Task 1: Enforce assistant-response provenance

**Purpose:**
- Replace prompt-phrase heuristics with attempt-bound authorship evidence while preserving fast valid completions.

**Task Function:**
- Trace and implement the semantic-admission predicate at the existing observation boundary.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: P0 correctness, shared runtime boundary, and high regression risk require direct controller ownership.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused deterministic regressions exercise the same production functions and fake only external Herdr/Codex calls.

**Specification Coverage:**
- Accept semantic output only when attempt identity matches, post-submit freshness is proven, assistant/result ownership is proven, and terminal completion is proven.
- Prefer correlated structured TaskResult/runtime result identity over terminal output.
- Apply the same provenance hierarchy to every normalization input, including `task_result`, assignment-level fields, and observed runtime evidence; accepted producer/source identity must be explicit before any content is admitted.
- Reject prompt bullets, old completion history, arbitrary multiline user text, and fresh screen changes without assistant provenance.
- Preserve a fast answer already complete before the first post-submit poll when its assistant/result identity is attributable to the submitted attempt.
- Terminal output without independently proven assistant/result ownership can never be semantic evidence, regardless of wording or freshness.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/secretary_live_runtime.py:_observe_submitted_codex`
- Inspect: `scripts/secretary_live_runtime.py:_extract_codex_semantic_content`
- Inspect: `scripts/secretary_live_runtime.py:_codex_initial_prompt_bullet`
- Inspect: `scripts/secretary_live_runtime.py:_submission_freshness_proven`
- Inspect: `scripts/herdr_main_launcher.py:_codex_completion_snapshot`
- Modify: `scripts/secretary_live_runtime.py:_observe_submitted_codex` and the smallest existing semantic-admission helpers required by the predicate
- Modify: `scripts/herdr_main_launcher.py:_codex_completion_snapshot` only if an existing assistant/result identity must be exposed
- Verify: `tests/test_secretary_live_runtime.py` and `tests/test_herdr_main_launcher.py`

**Dependencies:**
- Existing assignment/attempt identity and snapshot fields remain authoritative.
- No new receipt schema, polling service, prompt-language classifier, or orchestration layer is permitted.

**Authority:**
- Preauthorized local actions: inspect the listed symbols and add focused deterministic regressions for semantic admission
- Stop for: a new result schema, provider dependency, prompt-specific special case, or any change that weakens stale-output rejection

**Steps:**
- [x] Step 1: Trace every caller and existing test of the observer, semantic extractor, freshness helper, and launcher snapshot; record the current evidence precedence.
- [x] Step 2: Add failing tests for `Summarize these notes:` with user bullets, arbitrary multiline prompt text, old completion history, fresh screen without assistant provenance, missing identities, wrong attempts, unaccepted producers, assignment-level prompt content, and fast attributed completion.
- [x] Step 3: Implement the assistant-owned/attempt-bound predicate using the provenance hierarchy above, existing structured evidence first, and the terminal adapter only as a proven compatibility fallback.
- [x] Step 4: Remove prompt-phrase assumptions and keep the fast-completion path green.

**Verification:**
- [x] `py -B -m pytest -q tests/test_secretary_live_runtime.py tests/test_herdr_main_launcher.py`
- Expected: new regressions fail before the implementation change, then all focused tests pass with prompt-only content unavailable and attributed fast completion reported.

**Exit Criteria:**
- No user/prompt text can cross the semantic boundary without assistant-owned attempt evidence.
- The observer returns an explicit unavailable result when authorship cannot be proven.

### Task 2: Make semantic projections and error scopes canonical

**Purpose:**
- Ensure one semantic decision drives every result projection and independent diagnostic/finalization failures do not corrupt authoritative work.

**Task Function:**
- Normalize semantic evidence once, derive compatibility fields once, and preserve monotonic cleanup behavior.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: P0 cross-field consistency and backend failure semantics.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused runtime and reconciliation regressions provide independent field-level assertions.

**Specification Coverage:**
- `semantic_outcome` is the internal authority; `result.state` and `result.content` are derived immediately before serialization.
- The execution order is collect evidence, decide `semantic_outcome` once, collect/finalize resource evidence, derive the compatibility projection once, then serialize and return.
- Every input admitted by normalization (`task_result`, assignment-level fields, and observed runtime evidence) must satisfy the Task 1 provenance hierarchy; missing identity, wrong attempt, unaccepted producer/source, or assignment-level prompt content is non-authoritative.
- Correlated `reported_completed` TaskResult plus diagnostic `OSError` yields semantic `reported`, observability `unavailable`, and independent finalization status.
- Contradictory authoritative semantic evidence yields one `ambiguous`/unavailable decision reflected consistently in all projections.
- Execution, observation, and finalization errors remain distinguishable evidence scopes.
- Reported semantic content survives cleanup failure; unknown cleanup still blocks reuse and retains owned-resource identities.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/secretary_live_runtime.py:_normalize_invocation_outcome`
- Inspect: `scripts/secretary_live_runtime.py:run_normal`
- Inspect: `scripts/secretary_live_runtime.py:_reduce_resource_evidence`
- Inspect: `scripts/secretary_live_runtime.py:_owned_resources`
- Inspect: `scripts/secretary_live_runtime.py:main`
- Modify: `scripts/secretary_live_runtime.py:_normalize_invocation_outcome`, `scripts/secretary_live_runtime.py:run_normal`, `scripts/secretary_live_runtime.py:main`, and the smallest shared semantic-projection helper required to derive `result`
- Verify: `tests/test_secretary_live_runtime.py` and `tests/test_reconciliation.py`

**Dependencies:**
- Task 1 establishes the authoritative semantic evidence that normalization consumes.
- Existing ownership and monotonic resource-reduction rules remain unchanged unless a test proves a projection bug.

**Authority:**
- Preauthorized local actions: add failing normalization/failure-path regressions and modify only the listed runtime normalization/serialization symbols
- Stop for: a new lifecycle state, cleanup redesign, global quarantine registry, or resource ownership broadening

**Steps:**
- [x] Step 1: Trace all writers of `semantic_outcome`, `result`, `observability`, `resource`, and `recovery_required` from `run_normal()` through output serialization.
- [x] Step 2: Add failing tests for correlated TaskResult plus observation failure, conflicting evidence, cleanup timeout after reported answer, malformed close response, and the CLI exception path producing a consistent canonical failure envelope.
- [x] Step 3: Centralize the semantic decision and derive compatibility projections from it without post-normalization mutation; after that decision, no code path may mutate `result` independently of `semantic_outcome`.
- [x] Step 4: Preserve independent error scopes and rerun reconciliation/resource tests.

**Verification:**
- [x] `py -B -m pytest -q tests/test_secretary_live_runtime.py tests/test_reconciliation.py`
- Expected: every serialized fixture satisfies semantic equivalence between `result.state` and `semantic_outcome.state`; cleanup uncertainty never erases semantic content or permits reuse.
- Expected: the normal CLI exception path uses the same canonical projection and includes consistent semantic, execution, observability, and finalization evidence; process exit zero is never treated as live semantic acceptance by itself.

**Exit Criteria:**
- One canonical semantic decision produces all semantic projections.
- Observation and finalization failures cannot falsely downgrade or contradict independently proven semantic work.

### Task 3: Retire expectation-derived Secretary measurement mode

**Purpose:**
- Keep deterministic contract fixtures and fake-boundary measurements separate, removing the misleading Secretary `measure` path rather than maintaining pseudo-measurement fields.

**Task Function:**
- Simplify the benchmark CLI and CI contract while preserving the stronger completion-monitoring measurement harness.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded CLI/configuration change with direct CI compatibility impact.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: benchmark tests and subprocess exit-code assertions cover the public command behavior.

**Specification Coverage:**
- `benchmark_secretary_architecture.py contract 30` remains deterministic contract evidence with no production latency claim.
- `benchmark_secretary_architecture.py contract 30` is fixture generation only; its zero exit code does not validate correctness by itself.
- `run_measure_benchmark`, its expectation-derived fields, and the `measure` CLI mode are removed after confirming the repository callers are limited to the declared tests/CI surfaces.
- `benchmark_completion_monitoring.py` remains the fake-boundary baseline/candidate measurement path and returns nonzero when any correctness row is wrong.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/benchmark_secretary_architecture.py:ContractMetric`
- Inspect: `scripts/benchmark_secretary_architecture.py:run_contract_benchmark`
- Inspect: `scripts/benchmark_secretary_architecture.py:run_measure_benchmark`
- Inspect: `scripts/benchmark_secretary_architecture.py:build_parser` and `main`
- Modify: `scripts/benchmark_secretary_architecture.py`, `tests/test_secretary_benchmark.py`, and `.github/workflows/runtime-contracts.yml`
- Verify: `scripts/benchmark_completion_monitoring.py:main` and `tests/test_benchmark_completion_monitoring.py`

**Dependencies:**
- Task 2 must establish the runtime contract before benchmark expectations are removed.
- Existing workflow callers must be enumerated before deleting the mode.

**Authority:**
- Preauthorized local actions: remove only the declared `measure` API/CLI/tests/CI invocation and preserve contract/fake-boundary modes
- Stop for: an undiscovered production caller, a required public compatibility consumer, or a benchmark that still derives actual values from expectations

**Steps:**
- [x] Step 1: Trace all repository callers of `run_measure_benchmark`, `measure`, and measurement-only fields; record the compatibility conclusion in the plan evidence.
- [x] Step 2: Add or retain failing subprocess coverage proving the contract mode remains explicit and the fake-boundary harness exits nonzero on an injected mismatch.
- [x] Step 3: Remove the expectation-derived measure path and its CI invocation; keep `contract 30` and completion-monitoring validation in CI.
- [x] Step 4: Verify unavailable/unobserved fields are null or explicitly unavailable and never populated from expected dictionaries.

**Verification:**
- [x] `py -B -m pytest -q tests/test_secretary_benchmark.py tests/test_benchmark_completion_monitoring.py`
- [x] `$contractOutput = Join-Path ([System.IO.Path]::GetTempPath()) 'secretary-contract.json'; py -B scripts/benchmark_secretary_architecture.py contract 30 > $contractOutput`
- [x] `$monitorOutput = Join-Path ([System.IO.Path]::GetTempPath()) 'completion-monitoring.json'; py -B scripts/benchmark_completion_monitoring.py --baseline-revision f6f0bcf0bd5e4289eb872e1cce43038bcf7ece7d --repetitions 3 --output $monitorOutput`
- Expected: contract fixture generation exits `0`; the completion-monitoring harness uses the frozen baseline revision and its negative subprocess test exits nonzero on an injected mismatch; no Secretary architecture benchmark claims production performance.

**Exit Criteria:**
- There is one deterministic Secretary contract mode and one explicitly labeled fake-boundary measurement mode.
- CI no longer runs the retired expectation-derived mode.

### Task 4: Reconcile evidence scope and exact-SHA closure records

**Purpose:**
- Prevent the existing completion-monitoring artifact from being misread as production performance evidence and bind every accepted result to immutable source identity.

**Task Function:**
- Classify retained evidence and align artifact/report wording with what the harness actually observes.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: source-of-truth and evidence-contract reconciliation with no new runtime behavior.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: artifact JSON assertions, plan evidence, and repository validators.

**Specification Coverage:**
- `artifacts/completion-monitoring/normal-invocation-finalization-final.json` remains correctness/control-flow fixture evidence from a fake Herdr boundary, not candidate-vs-baseline production performance evidence.
- `artifacts/completion-monitoring/normal-invocation-finalization-final.json` is immutable historical evidence; a newer interpretation or missing machine-readable scope requires new evidence rather than rewriting this artifact.
- Any retained measurement fields identify their observed/unavailable status and exact baseline/candidate source hashes.
- No p95/p99, latency, token, or economics claim is accepted from the existing one-repetition artifact.

**Required Skills:**
- `skill-backend-verification`, `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: `scripts/benchmark_completion_monitoring.py:main`
- Inspect: `tests/test_benchmark_completion_monitoring.py`
- Inspect: `artifacts/completion-monitoring/normal-invocation-finalization-final.json`
- Modify: `scripts/benchmark_completion_monitoring.py` and its focused tests only if the scope cannot be expressed without rewriting the historical artifact; otherwise record the classification in the final plan evidence without changing that artifact
- Verify: `artifacts/completion-monitoring/normal-invocation-finalization-final.json` and exact candidate source hashes

**Dependencies:**
- Task 3 establishes the benchmark-mode boundary.
- Historical completed plans remain immutable evidence; do not rewrite them to make current claims appear newer.

**Authority:**
- Preauthorized local actions: inspect the historical artifact and update only the generator/tests or new evidence needed to express the current classification; never rewrite the historical artifact
- Stop for: modification or deletion of the historical artifact, a new evidence database, unbound source hashes, or any performance claim not supported by matched runs

**Steps:**
- [x] Step 1: Compare the artifact schema, generator output, tests, and current plan evidence; identify whether `evidence_kind` plus source hashes already express the required scope.
- [x] Step 2: Add the smallest machine-readable scope assertion in new evidence or the generator/tests if the current schema cannot distinguish fake-boundary correctness from production performance; do not rewrite the historical artifact.
- [x] Step 3: Record the exact baseline SHA, candidate SHA, harness, repetition count, and claim limitation in the plan evidence.

**Verification:**
- [x] `py -B -m pytest -q tests/test_benchmark_completion_monitoring.py`
- [x] `python -m json.tool artifacts/completion-monitoring/normal-invocation-finalization-final.json`
- Expected: artifact is parseable, source-bound, explicitly fake-boundary/correctness-scoped, and contains no unsupported production-performance claim.

**Exit Criteria:**
- Reviewers can distinguish deterministic fixture evidence, fake-boundary observations, and real live probes without inference.

### Task 5: Run two bounded live probes and close the plan

**Purpose:**
- Validate the corrected semantic boundary against a real disposable normal invocation and preserve sanitized closure evidence.

**Task Function:**
- Execute, inspect, and reconcile two task-owned live probes without changing the repository or using provider telemetry as a prerequisite.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: live external boundary and cleanup authority require direct controller ownership.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: final verification compares the recorded envelope against the declared probe matrix and repository state.

**Specification Coverage:**
- Probe A asks for exactly `SECRETARY_PROBE_<UTC nonce>` and forbids repository edits or child-worker creation.
- Probe B uses a multiline/bullet prompt containing user text and requests a distinct exact nonce answer.
- Both probes record exact candidate SHA, runtime versions, assignment/attempt identity, submission anchor, time to useful answer, total duration, remaining owned resources, semantic projections, and cleanup evidence. Poll count and launcher/Herdr command count are recorded only when existing instrumentation exposes them; otherwise they are `unavailable` and are not added solely for the probe.
- Both probes require the exact assistant nonce, no prompt/user bullet leakage, projection agreement, no duplicate dispatch, unchanged repository, answer preservation after cleanup, retirement of invocation-owned resources, and preservation of shared/pre-existing resources.
- A live probe passes only when every required predicate is directly present and true in the sanitized envelope or an existing read-only boundary observation; an absent predicate is `unavailable` and blocks completion rather than being inferred from process exit zero.
- If Herdr/Codex capability is unavailable, record a bounded `blocked` live-proof result and leave the plan non-completed; never fabricate live success.

**Required Skills:**
- `skill-backend-verification`, `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: `scripts/secretary_live_runtime.py:run_normal`
- Inspect: `scripts/secretary_live_runtime.py:main`
- Inspect: `scripts/secretary_live_runtime.py:_smoke_receipt`
- Verify: sanitized output in the OS temp directory resolved by `$env:TEMP` on Windows or `tempfile.gettempdir()` in Python, named `project-os-managed-invocation-semantic-provenance-final.json`
- Verify: disposable worktree state and owned-resource retirement through the existing Herdr boundary

**Dependencies:**
- Tasks 1–4 are complete and the candidate SHA is frozen before live execution.
- Use a unique UTC nonce generated immediately before each probe and a disposable task-owned worktree.

**Authority:**
- Preauthorized local actions: run the two declared disposable probes, inspect their bounded output, and write sanitized evidence outside the repository
- Stop for: missing capability, authentication, ambiguous resource ownership, shared-resource deletion risk, repository mutation, duplicate dispatch, or any live result that contradicts deterministic proof

**Steps:**
- [x] Step 1: Freeze the candidate SHA and verify the disposable worktree is clean and based on that SHA.
- [x] Step 2: Run Probe A through the existing normal invocation entry point with a unique exact-answer nonce.
- [x] Step 3: Run Probe B with multiline/bullet user content and a distinct exact-answer nonce.
- [x] Step 4: Use the bounded PowerShell command contract for each probe, with unique UTC nonces and strict semantic, projection, finalization, ownership, cleanup, and no-mutation gates. Both probes passed; dispatch count was unavailable and was not inferred.

  ```powershell
  $probeRoot = Join-Path ([System.IO.Path]::GetTempPath()) 'project-os-managed-invocation-probe'
  New-Item -ItemType Directory -Force -Path $probeRoot | Out-Null
  $probeWorktree = Join-Path $probeRoot 'worktree'
  $nonceA = 'SECRETARY_PROBE_{0}' -f (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssfffZ')
  $nonceB = 'SECRETARY_PROBE_{0}' -f (Get-Date).ToUniversalTime().AddMilliseconds(1).ToString('yyyyMMddTHHmmssfffZ')
  $probeTaskA = "Return exactly $nonceA. Do not edit the repository or create child workers."
  $probeTaskB = @"
User notes:
• The bullets are user-provided content.
• Do not echo these notes as the answer.
Return exactly $nonceB. Do not edit the repository or create child workers.
"@
  $outputPathA = Join-Path $probeRoot 'probe-a.json'
  $outputPathB = Join-Path $probeRoot 'probe-b.json'
  $candidateSha = (git -C $probeWorktree rev-parse HEAD).Trim()
  $deadlineSeconds = 300
  foreach ($probe in @(
      [pscustomobject]@{ Nonce = $nonceA; Task = $probeTaskA; Output = $outputPathA; Label = 'probe-a' },
      [pscustomobject]@{ Nonce = $nonceB; Task = $probeTaskB; Output = $outputPathB; Label = 'probe-b' }
  )) {
      $stdoutPath = Join-Path $probeRoot "$($probe.Label).stdout.txt"
      $stderrPath = Join-Path $probeRoot "$($probe.Label).stderr.txt"
      $arguments = @('-B', 'scripts/secretary_live_runtime.py', 'run', '--cwd', $probeWorktree, '--task', $probe.Task, '--output', $probe.Output)
      $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
      $startInfo.FileName = (Get-Command py).Source
      $startInfo.WorkingDirectory = $probeWorktree
      $startInfo.UseShellExecute = $false
      $startInfo.RedirectStandardOutput = $true
      $startInfo.RedirectStandardError = $true
      foreach ($argument in $arguments) { [void]$startInfo.ArgumentList.Add($argument) }
      $process = [System.Diagnostics.Process]::new()
      $process.StartInfo = $startInfo
      [void]$process.Start()
      $stdoutTask = $process.StandardOutput.ReadToEndAsync()
      $stderrTask = $process.StandardError.ReadToEndAsync()
      try {
          Wait-Process -Id $process.Id -Timeout $deadlineSeconds -ErrorAction Stop | Out-Null
      } catch {
          Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
          throw "bounded $($probe.Label) timeout; retain the disposable worktree and reconcile owned resources before cleanup"
      }
      $stdoutTask.Result | Set-Content -Encoding utf8 $stdoutPath
      $stderrTask.Result | Set-Content -Encoding utf8 $stderrPath
      if (-not (Test-Path $probe.Output)) { throw "probe output missing: $($probe.Output)" }
      $envelope = Get-Content -Raw $probe.Output | ConvertFrom-Json
      if ($envelope.semantic_outcome.state -ne 'reported' -or $envelope.result.state -ne 'reported' -or $envelope.result.status -ne 'completed') { throw "$($probe.Label) semantic result was not reported/completed" }
      if ($envelope.semantic_outcome.content -ne $probe.Nonce -or $envelope.result.content -ne $probe.Nonce) { throw "$($probe.Label) assistant nonce or projection content mismatch" }
      if ($envelope.finalization_outcome.state -ne 'settled' -or $envelope.finalization_outcome.recovery_required -ne $false -or $envelope.resource.state -ne 'settled' -or $envelope.resource.reuse_blocked -ne $false) { throw "$($probe.Label) resource finalization was not settled and reusable" }
      if ((git -C $probeWorktree status --porcelain)) { throw "$($probe.Label) mutated the disposable repository" }
      if (-not ($envelope.PSObject.Properties.Name -contains 'owned_resources')) { throw "$($probe.Label) owned-resource retirement evidence unavailable" }
      $owned = @($envelope.owned_resources)
      if (@($owned | Where-Object { $_.state -ne 'settled' }).Count) { throw "$($probe.Label) owned resource was not retired" }
      $dispatchCount = if ($envelope.preflight -and ($envelope.preflight.PSObject.Properties.Name -contains 'dispatch_count')) { $envelope.preflight.dispatch_count } else { 'unavailable' }
      if ($dispatchCount -is [int] -and $dispatchCount -ne 1) { throw "$($probe.Label) duplicate dispatch detected" }
  }
  ```

- [x] Step 5: Sanitize and keep raw probe output ephemeral. Record the sanitized evidence in the OS temp directory resolved by `$env:TEMP` on Windows or `tempfile.gettempdir()` in Python, and record durable facts in the plan ledger: candidate SHA, nonce or nonce digest, semantic verdict, projection-equivalence verdict, resource-retirement verdict, repository-unchanged verdict, elapsed duration, evidence-file digest, and unavailable capabilities.
- [x] Step 6: On timeout or any unavailable acceptance predicate, retain the disposable worktree and invocation-owned resource identities, run the existing ownership-safe reconciliation/close path, and record the live proof as `blocked`; never delete shared or ambiguous resources.
- [x] Step 7: Invoke `skill-verification-before-completion`; deterministic proof and both live gates verified, then update this plan to `completed`.

**Verification:**
- [x] `py -B -m pytest -q tests/test_secretary_live_runtime.py tests/test_herdr_main_launcher.py tests/test_secretary_benchmark.py tests/test_benchmark_completion_monitoring.py tests/test_skill_chief_of_staff.py tests/test_reconciliation.py` (`400 passed`)
- [x] `py -B scripts/validate_repo_contracts.py --repo-root . --fast`
- [x] `py -B scripts/validate_planning_lifecycle.py --repo-root .`
- [x] `py -B scripts/sync_agent_adapters.py --all-platforms --check`
- [x] `py -B scripts/validate_agent_runtime_drift.py --all-platforms --skip-deploy-check`
- [x] `git diff --check`
- Expected: all deterministic checks pass; both live probes meet the matrix or the plan remains explicitly blocked; accepted evidence is bound to the exact candidate SHA.
- Expected: each live command is bounded by the declared deadline, checks the semantic, projection, finalization, ownership, and repository predicates directly, and treats missing evidence or process exit zero alone as a failed/blocked acceptance.

**Exit Criteria:**
- The plan is `completed` only when **Managed Invocation Semantic Provenance Closure is complete** and all four closure statements are proven: no prompt leakage, one canonical semantic decision, monotonic resource safety, and fail-closed validation commands. This does not claim project-wide Normal Coordination or GitHub source-truth convergence is complete.
- A live capability gap is recorded as `blocked`, not converted into a completion claim.

## Verification

Final artifact-level verification must include the Task 5 focused suite, all
repository validators listed there, `git diff --check`, a clean/untracked-file
inventory, and a comparison showing the accepted evidence refers to the exact
candidate SHA. The final live evidence must remain outside the repository unless
the user separately authorizes a sanitized tracked artifact.

Current evidence: candidate `c250342fefa36154513cf5cfb9c39b7ef13bec34`; frozen-baseline fake-boundary harness passed with baseline `f6f0bcf0bd5e4289eb872e1cce43038bcf7ece7d` and three repetitions; historical artifact remained immutable; sanitized live evidence is at `C:\tmp\project-os-managed-invocation-semantic-provenance-final.json` with SHA-256 `71e3db255a8a8fbfc6ddc4fbfbd9cb1a026118bd30567dd0428fa42d1b16f634`. Probe A nonce SHA-256 is `727b5c12583676c300d0d80c49408bb213b6186824f82583e7d1d8cd604afd1b`; Probe B nonce SHA-256 is `caab04aeb1ba1123df9dbf1dcd8ecdde88aa7bad5e0d630ef37f0ad85ef1f936`.

Live closure: both probes returned `reported`/`completed` semantic and compatibility results with matching nonce content, `done` completion, no observation error, settled/reusable resources, removed cleanup state, three settled owned resources, and unchanged disposable repositories. Dispatch count was unavailable and remained explicitly unavailable.

Root causes patched: the launcher no longer reads terminal output while Herdr reports `working`; the semantic observer accepts only fresh terminal completions with a captured pre-submit anchor and completion marker when structured TaskResult evidence is absent; and the extractor selects the last completed bullet block so multiline user bullets cannot swallow the assistant answer. Focused and full deterministic suites pass.

## Completion Criteria

The plan is ready for completion verification when:

1. no user or prompt text can be published as assistant semantic output
2. one canonical semantic decision produces every compatibility projection
3. observation and finalization uncertainty cannot erase valid semantic work or permit unsafe reuse
4. Secretary contract fixtures, fake-boundary measurements, and live probes have distinct evidence scopes
5. every validation-bearing command fails when observed behavior violates its declared expectation
6. both bounded live probes are successful, or the plan records an explicit external-capability blocker and remains non-completed
7. historical evidence artifacts are immutable and newer interpretation uses new evidence
8. unobservable probe metrics are recorded as unavailable rather than instrumented solely for the probe
9. the final claim is limited to Managed Invocation Semantic Provenance Closure; no GitHub ruleset, review database, orchestration layer, or private-launcher refactor was introduced into this scope

Only `skill-verification-before-completion` may return `verified`; the lead
controller then changes `status` to `completed`. Push, merge, GitHub ruleset
administration, and formal review-state publication remain separate authorized
actions after verification.
