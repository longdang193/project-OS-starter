---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
name: controller-deepagents-codex-mcp-handoff
targets:
  - scripts/dcode_project.py
  - tests/test_dcode_project.py
  - tests/test_native_personal_local_workflow.py
  - docs/operating_system/procedures/personal-local-worktree-procedure.md
  - docs/operating_system/runtime/runtime-surfaces.md
  - docs/operating_system/tooling/code-intelligence-tools.md
  - README.md
  - repo_config/starter-kit-manifest.json
---

# Controller DeepAgents Codex MCP Handoff Plan

## Goal

Extend existing `dcode-project` into one handoff validator and launcher. The
lead controller, running in Codex, remains responsible for MCP calls. It reads
the user-local Codex configuration as SSOT, narrows selected server/tool IDs
for provenance, writes a sanitized handoff, and invokes DeepAgents with only
bounded runtime controls. Keep DeepAgents launched with `--no-mcp` until its
Windows MCP discovery path is fixed upstream.

## Implementation Outcomes

### Codex-bound controller manifest

The Codex controller reads active provider, model, configured MCP server IDs,
and configured MCP tool names from the user-local Codex config path already
owned by `[paths]` in local `dcode-project` config. `dcode-project
--print-config` emits stable JSON without endpoints, credentials, raw command
arguments, environment values, cookies, or headers. `dcode-project` validates
an optional subset selection for provenance only; it never executes MCP calls
and never expands capability beyond Codex configuration.

### Sanitized handoff and bounded DeepAgents launch

The adapter accepts one controller-produced handoff JSON file under
`%USERPROFILE%\.local\share\dcode-project\handoffs`, validates a versioned
schema, rejects symlinks, traversal, stale, credential-bearing, oversized, or
malformed payloads, and passes its validated absolute path plus bounded task
instruction to DeepAgents. DeepAgents receives `--no-mcp`; it uses native
filesystem, shell, task, and other executor-local tools only within its existing
launcher contract. Controller owns handoff cleanup; launcher never deletes it.

### Symmetric guidance and proof

Codex and DeepAgents use same role templates, Git scope, plan coordination, and
acceptance rules. Executor containment, approval, shell, filesystem, and MCP
capabilities remain executor-specific. Difference is represented by one
adapter manifest and one handoff contract rather than duplicate permission
systems. Focused tests cover parsing, subset validation, redaction, handoff
validation, launch argument bounds, cleanup, and live low-profile execution.

## Execution Approach

- Mode: `inline sequential`
- Executor: `codex`
- Required skills: `skill-writing-plans`, `skill-code-standards`, `skill-test-driven-development`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Parallel ownership: `none`
- Sequential fallback: implement and test adapter before guidance, then run generated-surface sync and live probes.

## Coordination State

- Coordination owner: `single lead controller`
- Branch: `main`
- Base commit: `d15b7e4`
- Active task: `none`
- Last checkpoint: `fresh full-suite, starter, drift, and live-probe verification`
- Expected workspace: `in-scope unstaged changes; no repository handoff artifacts`
- Next action: `explicit Git disposition`
- Blockers: `none`

Only lead controller updates coordination state. Git and this plan own resume
state; Codex and DeepAgents thread IDs remain runtime-local.

| Task | State | Executor | Depends On | Checkpoint | Evidence |
| --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | `codex` | none | working tree | capability projection tests pass; redacted manifest probe passes |
| Task 2 | `completed` | `codex` | Task 1 | working tree | handoff schema, security, path, age, digest, and symlink tests pass |
| Task 3 | `completed` | `codex` | Task 2 | working tree | bounded-control and rejection tests pass; child receives forced `--no-mcp` |
| Task 4 | `completed` | `codex` | Task 3 | working tree | guidance sync, full suite, starter validation, drift checks, and live probes pass |

## Task Breakdown

### Task 1: Add Codex MCP capability projection

**Purpose:**
- Add read-only projection of configured Codex MCP capability without creating a second permission owner.

**Specification Coverage:**
- Codex `config.toml` remains SSOT for provider, MCP server, and tool availability.
- Controller may narrow capability but may not grant absent capability.
- Sensitive runtime values never enter manifest output.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `scripts/dcode_project.py:_runtime_binding`, `scripts/dcode_project.py:main`
- Modify: `scripts/dcode_project.py:_runtime_binding`, `scripts/dcode_project.py:main`
- Add tests: `tests/test_dcode_project.py`
- Verify: user-local Codex config through temporary redacted fixtures; never commit private config.

**Dependencies:**
- Existing local `[paths]` config points to Codex config.
- Existing role loading and fixed `--no-mcp` launch path remain unchanged.

**Steps:**
- [ ] Step 1: Parse only `[mcp_servers]` table names and nested `.tools` table names from Codex TOML; ignore endpoint, command, args, environment, and tool values in output.
- [ ] Step 2: Add `runtime_binding_digest` over canonical JSON containing provider name, model, and endpoint, and `mcp_capability_digest` over sorted server/tool IDs; emit neither endpoint nor raw config.
- [ ] Step 3: Add exact repeatable `--mcp-select SERVER[.TOOL][,SERVER[.TOOL]...]` syntax. Empty selection means all configured IDs; duplicate IDs collapse; server-only selection means server provenance without tool claims. Reject unknown IDs before handoff validation or child launch.
- [ ] Step 4: Keep DeepAgents invocation unchanged: selected MCPs are provenance for Codex controller calls, not arguments or environment passed to `dcode`.

**Verification:**
- [ ] `py -3 -m pytest -q tests/test_dcode_project.py -k "mcp or config or capability or manifest"`
- Expected: fixtures expose only configured IDs and stable digests; endpoint, command, args, env, and secret-like values are absent; unknown selection raises `RuntimeError`.

**Exit Criteria:**
- `--print-config` emits stable redacted capability JSON and no private values; existing role and launch tests remain green.

### Task 2: Add versioned sanitized MCP handoff

**Purpose:**
- Establish one bounded file contract from Codex MCP calls to DeepAgents.

**Specification Coverage:**
- Codex performs MCP calls; DeepAgents consumes sanitized findings.
- Handoff carries facts and source metadata, not authority or credentials.
- Handoff validation is symmetric for all roles and executor runs.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`

**Files And Symbols:**
- Modify: `scripts/dcode_project.py` with handoff schema constants and `_load_handoff`, `_validate_handoff`, `_sanitize_handoff`, `_handoff_prompt` helpers.
- Modify: `tests/test_dcode_project.py` with handoff fixtures and rejection cases.
- Verify: `C:\tmp` handoff file during live probe; do not add it to repository.

**Dependencies:**
- Task 1 capability projection defines source/tool identifiers and digest format.

**Steps:**
- [ ] Step 1: Define exact `codex.mcp.handoff.v1`: required `schema` string, RFC3339 `generated_at`, `mcp_capability_digest`, `sources` array, `facts` array, and optional `constraints` array. Each source has `server` and optional `tool`; each fact has `source` and `value`, where value is string, number, boolean, null, or object/array containing only those scalar values.
- [ ] Step 2: Enforce 262144-byte file size, maximum 64 sources, 256 facts, 4096-character strings, 16 nesting levels, and 24-hour handoff age. Reject unknown top-level fields and source/tool IDs outside selected projected capability.
- [ ] Step 3: Reject keys or values matching credential, cookie, authorization, secret, token, password, raw header, or raw network-body fields; reject ambiguous payloads rather than attempting partial redaction.
- [ ] Step 4: Add exact controller-only `--handoff-file PATH` syntax. Require an absolute regular file under `%USERPROFILE%\.local\share\dcode-project\handoffs`; reject symlinked file, resolved path outside root, directory, missing file, stale file, and malformed content. Controller creates and deletes handoff; launcher never deletes it.
- [ ] Step 5: Require `--handoff-file` with `-n`/`--non-interactive`, append one bounded read instruction to that task text, preserve caller task text, force `--no-mcp`, and never pass raw handoff contents as CLI arguments.

**Verification:**
- [ ] `py -3 -m pytest -q tests/test_dcode_project.py -k "handoff or sanitize"`
- Expected: valid handoff accepted; malformed, oversized, stale, symlinked, traversal, unknown-source, secret-bearing, and out-of-scope paths rejected before child launch.

**Exit Criteria:**
- One versioned handoff contract exists in code and tests; no raw Codex config or MCP response is passed to DeepAgents.

### Task 3: Expose bounded controller controls

**Purpose:**
- Let controller adapt DeepAgents task execution without duplicating DeepAgents configuration or Codex authority.

**Specification Coverage:**
- Controller can adjust only flags exposed by current `dcode` CLI.
- Role/model selection stays tied to canonical `agents/*.toml` and local Codex binding.
- Unsupported authority-changing controls remain rejected.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`

**Files And Symbols:**
- Modify: `scripts/dcode_project.py:_ALLOWED_RUNTIME_FLAGS`, `_ALLOWED_RUNTIME_VALUE_OPTIONS`, `_reject_unmanaged_runtime_options`, `main`
- Modify: `tests/test_dcode_project.py` bounded-control and rejection parametrization
- Verify: `dcode --help` on installed runtime before updating allowlist.

**Dependencies:**
- Tasks 1–2 complete.

**Steps:**
- [ ] Step 1: Keep allowlist limited to `--max-turns`, `--timeout`, `--goal`, `--rubric`, `--rubric-max-iterations`, `--recursion-limit`, output controls, task text, and forced `--no-mcp`.
- [ ] Step 2: Add explicit role selector only if current `dcode` exposes a supported role/config option; otherwise retain role selection through bounded task delegation naming `low`, `normal`, or `high`.
- [ ] Step 3: Reject `--model`, `--agent`, `--resume`, MCP config/trust flags, approval/Yolo, sandbox, shell/filesystem/interpreter, install, startup, and ACP controls.
- [ ] Step 4: Ensure selected MCP IDs/tools affect only controller manifest and handoff provenance, never DeepAgents executable arguments.

**Verification:**
- [ ] `py -3 -m pytest -q tests/test_dcode_project.py -k "runtime_options or bounded or rejects"`
- Expected: bounded controls reach child unchanged; forbidden controls fail before role-view writes or child launch.

**Exit Criteria:**
- Controller has one narrow supported control surface; no duplicate model, permission, MCP, approval, or sandbox config is introduced.

### Task 4: Align documentation, starter surfaces, and live proof

**Purpose:**
- Make runtime behavior discoverable and preserve one SSOT/symmetry contract across guidance and generated starter output.

**Specification Coverage:**
- Guidance states broad user-local Codex MCP config is authority.
- Codex MCP research → sanitized handoff → DeepAgents `--no-mcp` is canonical workflow.
- Windows DeepAgents MCP discovery limitation and fallback are accurately documented.

**Required Skills:**
- `skill-verification-before-completion`
- `skill-code-standards`

**Files And Symbols:**
- Modify: `README.md`
- Modify: `docs/operating_system/procedures/personal-local-worktree-procedure.md`
- Modify: `docs/operating_system/runtime/runtime-surfaces.md`
- Modify: `docs/operating_system/tooling/code-intelligence-tools.md`
- Modify: `docs/operating_system/templates/agents/root-AGENTS.template.md`
- Regenerate: `AGENTS.md`, `generated_agents/codex/**`, `generated_agents/claude/**`, `generated_agents/antigravity/**` through `scripts/sync_agent_adapters.py`
- Modify: `tests/test_native_personal_local_workflow.py`, `tests/test_starter_kit_generation.py` only when assertions change.

**Dependencies:**
- Tasks 1–3 complete.

**Steps:**
- [ ] Step 1: Document Codex config as broad user-local MCP SSOT; controller may select only a subset and cannot pass credentials or raw config to DeepAgents.
- [ ] Step 2: Document manifest/handoff lifecycle and retention boundary using absolute examples outside Git, without adding runtime state to starter kit.
- [ ] Step 3: Remove stale claims that DeepAgents can receive Codex MCP permissions or that `--with-mcp` exists.
- [ ] Step 4: Run adapter sync from canonical sources; inspect generated diffs and confirm no generated surface was edited directly.
- [ ] Step 5: Run live low-profile probe: Codex Context7 lookup, controller writes handoff under approved user-local root, `dcode-project --handoff-file ... --mcp-select ... --no-mcp` validates and launches, DeepAgents reads handoff, exact marker returns, and Git clean-scope check passes.

**Verification:**
- [ ] `py -3 scripts/sync_agent_adapters.py --check --all-platforms`
- [ ] `py -3 scripts/validate_repo_contracts.py --fast`
- [ ] `py -3 -m pytest -q tests/test_dcode_project.py tests/test_native_personal_local_workflow.py tests/test_starter_kit_generation.py`
- [ ] `git diff --check`
- [ ] Live probe returns `CODEX_HANDOFF_OK` and records no MCP config, credential, cookie, header, or handoff payload in Git.

**Exit Criteria:**
- Code, tests, guidance, generated adapters, and starter manifest agree; live probe proves fallback workflow; unresolved upstream Windows MCP defect remains explicitly deferred.

## Verification

- [x] `py -3 -m pytest -q` — `127 passed`.
- [x] `py -3 scripts/sync_agent_adapters.py --check --all-platforms` — generated outputs current.
- [x] `py -3 scripts/validate_agent_runtime_drift.py --all-platforms` — deployed runtime current.
- [x] `py -3 scripts/validate_repo_contracts.py --fast` — repository contracts pass.
- [x] `py -3 scripts/validate_starter_kit.py` — starter kit validation passes.
- [x] `py -3 scripts/validate_generated_header_format.py` and `py -3 scripts/validate_planning_lifecycle.py` — pass.
- [x] `git diff --check` — no whitespace errors.
- [x] Live high-controller probe with `context7,chrome-devtools` handoff — `CODEX_HANDOFF_OK`; DeepAgents `gpt-5.6-terra`.
- [x] Live low-controller probe with `context7` handoff — `CODEX_HANDOFF_LOW_FINAL_OK`; DeepAgents `gpt-5.4-mini-2026-03-17`.
- [x] Negative selection probe — unknown MCP server rejected before child launch.

## Completion Criteria

The plan is ready for completion verification when:

1. `dcode-project --print-config` reports provider, role models, configured MCP IDs/tools, `runtime_binding_digest`, and `mcp_capability_digest` without private values.
2. Unknown MCP selections and unsafe handoff payloads fail closed before DeepAgents launch.
3. Supported DeepAgents task controls pass through; authority-changing flags remain rejected.
4. DeepAgents always launches with `--no-mcp` and uses only validated handoff facts for Codex MCP research results; no MCP tool is projected into DeepAgents.
5. Canonical roles, generated adapters, starter manifest, guidance, tests, and runtime behavior agree.
6. Fresh live probe passes with low profile and exact marker output.
7. No repository credentials, MCP endpoints, raw tool config, cookies, headers, or handoff payloads are tracked.
8. Windows direct DeepAgents MCP discovery remains an approved deferral; Codex owns MCP calls until upstream fixes `Path.resolve()` blocking in MCP discovery.

## Deviations And Residual Risks

- Direct DeepAgents MCP remains disabled because `deepagents-code 0.1.55` still
  fails Windows MCP discovery at `mcp_tools.py:1054` with `BlockingError`.
- Live-probe handoff files remain in user-local handoff storage because current
  shell policy blocked deletion outside workspace. They are outside Git and
  contain only sanitized facts; remove them manually before reuse if desired.
