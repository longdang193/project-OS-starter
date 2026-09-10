# Runtime Adapter Procedure (Cross-Tool)

## Contract

1. `AGENTS.md` is the generated shared global baseline contract.
2. `~/.codex`, `~/.claude`, `~/.gemini` are runtime targets.
3. Runtime targets are generated and deployed only.
4. Canonical edits happen in repo sources only:
   - scoped `AGENTS.md` files, when present
   - `docs/operating_system/`
   - `.agents/skills/`
   - `agents/*.toml`
   - `docs/operating_system/templates/agents/root-AGENTS.template.md`

Scoped `AGENTS.md` files are canonical instructions for their directories.
`docs/operating_system/rules/` is canonical rule source. Adapter sync mirrors it
to `.agents/rules/` for supported local runtimes.

## Runtime Recovery and Proof

For a local MCP or daemon-backed runtime:

1. Discover the live endpoint through its IPC or status channel. Do not trust a
   stale port, PID, or marker file without probing it.
2. If IPC is missing or the parent process died, restart the owning runtime and
   reconnect the client. Do not edit generated runtime files to hide stale
   state.
3. Prove transport with one successful tool call. `active:false` alone is not a
   transport result.
4. For asynchronous work, preserve the run ID, poll to terminal state, and
   verify artifacts or output paths. Tool-call success is not completion proof.
5. If shutdown cancels active work, preserve the run record and lifecycle logs.
   Fix ownership in the runtime provider; do not patch the consuming project.
6. Treat closed-parent `EPIPE` and missing-pipe errors as transport incidents.
   Keep logging best-effort so diagnostic output cannot terminate its owner.

Shared skills deployed to `~/.agents/skills/<skill>` carry a
`.project-os-managed` JSON marker with schema, source root, and source-relative
skill path. Deploy updates and removes only markers owned by the current repo.
Unmarked byte-identical skills are adopted automatically; differing unmarked
skills require `--adopt-shared-skill <name>`. `--force` remains for provider
runtime overwrite protection and is not shared-skill adoption authorization.

`agents/*.toml` is the canonical agent-profile registry. It owns delegated
provider alias, model, optional rank, and prompt. Positive ranks order only
ranked profiles; unranked profiles are explicit-only and non-orderable. Current
ranked profiles are ordered by registry rank; specialized profiles may use
another name and model.
Select executor and validator profiles independently from their bounded task
contracts. A validator may be lower, equal, or higher than its executor when
reliable for the validation task.
Sync renders Codex TOML into
`generated_agents/codex/agents/`. User-local `dcode-project` generates ignored
DeepAgents project views at launch. Keep provider endpoints, credentials, MCP
configuration, and provider definitions out of role templates and tracked
outputs.

## DeepAgents MCP Projection

DeepAgents may use MCP only through explicit Herdr selection. Herdr accepts
`--mcp-select <server[.tool][,server[.tool]...]>` and forwards it to
`dcode-project`; `dcode-project` validates selection against approved Codex
`[mcp_servers]`. No selection keeps the child on `--no-mcp`. Selecting a server
exposes all tools exposed by that server. Selecting a tool limits access to that
tool. Direct mode needs no per-task `.mcp.json`: launcher writes temporary
launcher-owned config, isolates child state with `DEEPAGENTS_HOME`, and removes
it after launch. Project MCP configs stay untouched and untrusted; never pass
`--trust-project-mcp`.

Headless `-n` runs MCP tools automatically only when their protocol metadata
proves read-only. Other MCP calls fail closed because no approval UI exists.
The local compatibility patch permits only `playwright_browser_tabs` with
`action=list`; navigation, tab changes, form actions, uploads, and script
execution remain blocked.

MCP `headers` values must be `${VAR}` references. MCP `env` values may be
`${VAR}` references or non-sensitive literals. Raw credentials,
config secrets, and tool configuration never enter task text, logs, or tracked
files. `codex.mcp.handoff.v1` carries validated facts and provenance only; it
does not grant MCP tool access.

## Herdr Observation

Controller inspection uses existing Herdr pull commands, not a new supervisor
or runtime ledger. For Codex, inspect `agent get` and `agent read`; for
DeepAgents, inspect `pane process-info` and `pane read`. Tura remains outside
this Herdr launcher path and uses `project-delegate`. Record executor, session,
pane, agent identity, task hash, state, and
evidence source; keep state `unknown` when evidence is missing or stale.
Treat `pane read` and `agent read` output as disposable probe data: metadata-only
by default, explicitly bounded and redacted when raw output is required. Never
treat silence as completion or trigger automatic kill, retry, or plan advance.
Native Codex CoS may use `--session auto --pane auto` through the repository
launcher. The launcher discovers all eligible existing matching-cwd panes from
the default Herdr server, validates workspace-qualified pane IDs, and uses the
default server session for target commands; workspace IDs are not session
names. It filters panes with no agent state and shell-only foreground process,
sorts candidates deterministically, and selects the first. Candidate evidence
records the full eligible set; no matching target returns
`target_resolution:not_found`, while
candidate rejection or incomplete discovery remains observable as `blocked` or
`incomplete`. Mixed
exact/`auto` selectors fail closed. `HERDR_ENV` is not a CoS dispatch gate and
is removed from launcher child environments.

## Delivery Reconciliation

Launcher delivery evidence distinguishes `delivered`, `delivery_failed`, and
`delivery_uncertain`. Codex prompt acknowledgement is delivery evidence;
completion observation is separate. Transport timeout or missing observation
produces `delivery_uncertain` only before acknowledgement; a later observation
timeout does not rewrite confirmed delivery as rejection and does not authorize
automatic kill or replay. Reconcile the existing lane through Herdr observation
before retrying any uncertain write-capable delivery.
Replay requires plausible transient failure, an idempotent operation, and
fresh evidence that the original delivery did not succeed. The launcher keeps
the original task hash, projected Runtime Grant digest, and delivery-task hash
together so the observed lane can be matched to the exact task brief.

## Generate

```bash
python scripts/sync_agent_adapters.py --all-platforms
```

Outputs:

- `generated_agents/codex/`
- `generated_agents/claude/`
- `generated_agents/antigravity/`
- `.agents/rules/`

## Deploy

```bash
python scripts/deploy_agent_runtime.py --target all
```

Targets:

- `~/.codex`
- `~/.claude`
- `~/.gemini`

DeepAgents is not an adapter-sync target. User-local `dcode-project` derives
ignored project subagents from `agents/*.toml` at launch. Every task execution
launch requires `--role <profile>`; `--print-config` may omit it. Launcher
consumes this selector and
uses the selected profile's model for its primary `dcode -M` binding. Its
provider endpoint, credentials, provider definition, and mutable state remain
local. Each selected profile's `model_provider` must match active local Codex provider
binding. `dcode-project` also reads that provider's canonical `wire_api` and
projects it to DeepAgents' native `use_responses_api` model parameter:
`chat` maps to `false`, `responses` maps to `true`. Unsupported protocols fail
before child launch. Agent profiles do not duplicate protocol compatibility;
the active provider binding owns that fact, so every profile using that provider
follows the same launch mapping while Tura and Native Codex remain independent
paths.

`dcode-project` loads Codex configuration once per invocation. `--print-config`
does not read credentials, generate role views, acquire role ownership, or
launch a worker. Execution evidence separates controller model from selected
worker model and omits worker binding evidence when no role is selected. Tura
keeps its existing provider configuration and credential behavior; only the
DeepAgents path validates `wire_api` and derives `use_responses_api`.

Launcher performance evidence records monotonic durations for preflight, target
discovery, worker initialization, delivery, observation, and retirement,
alongside launcher subprocess counts. Each phase has explicit measured,
not-attempted, or unavailable status; final evidence includes total duration and
per-attempt retry attribution. Any optimization requires a matching workload
baseline; otherwise reduction stays deferred.

DeepAgents role views are one same-worktree attempt resource. Launcher acquires
non-blocking ownership before mutation and holds it through worker exit and
cleanup. Ownership key uses canonical resolved worktree identity. Lock-file
presence is not live-owner evidence, and user-owned `.deepagents` content is
preserved. Crash cleanup is allowed only when worker process lifetime is
proven; otherwise generated views remain and launcher reports recovery blocked.

`project-delegate` is the one bounded Native Codex-to-Tura adapter. Its wrapper
rejects `--executor` and forces `--executor tura`; `[delegation].default_executor`
is only an internal launcher fallback. It reuses the same role and handoff
sources and passes one bounded task with fixed Git root, native `--sandbox`, and
fresh session id. Tura output remains opaque JSONL plus exit status.
`dcode-project` remains an explicit DeepAgents launcher; no recursive or
cross-runtime fallback exists. Tura routing uses
`TURA_PROVIDER_CONFIG` and must remain `Tura -> LightRSI -> 9router -> provider`.

For upgrade admission, run `project-delegate --role normal --print-config` and
record the reported `tura_executable_sha256` when the executable exists. The
receipt contains no credentials. Replacing the binary at the configured path
needs no setup rerun; moving it needs one setup rerun. Run one bounded,
read-only TL smoke after every binary replacement before reusing compatibility
or performance evidence. A changed hash invalidates old performance evidence,
not necessarily the adapter contract.

Current `dcode-project` defaults DeepAgents to `--no-mcp`, fixes child CWD to selected
Git root, and rejects direct runtime-authority flags. It does not translate Codex
`mcp_servers`, approval policy, sandbox mode, profiles, or threads. It supplies
fixed launcher-owned built-ins: filesystem tools plus `git` and `py` shell
commands; task input cannot widen them. Launcher injects exact native file-tool
root into every bounded task. On Windows it looks like
`/Users/<user>/repos/<repo>`; append repository-relative paths. Never guess
`/workspace/...` or use Windows drive syntax. It also injects filesystem safety:
read source, test, and text files only; inspect SQLite only through `py` with
stdlib `sqlite3` read-only URI mode and direct `py` commands only. `py -c` must
use one expression with no `;`. Call MCP through Codex, then let
`dcode-project` validate `codex.mcp.handoff.v1` and inject only sanitized
sources, facts, and constraints into task text. Setup rejects a
user-local `~/.deepagents/.mcp.json` to prevent an accidental direct MCP path.
The setup script owns the tested `deepagents-code` version, requires Python
3.12 or newer, verifies `dcode --version`, and disables automatic child updates. Use the setup
script for upgrades; do not rely on floating `uv tool install deepagents-code`
or `dcode --update`.

Launcher prefers the pinned executable under the user-local `dcode-project`
runtime root, then falls back to user-local or `PATH` `dcode`. Current
DeepAgents may load project `.env` files. Launcher-owned provider
environment values override inherited project values. Setup applies a narrow
local compatibility patch for Windows MCP config resolution and one unannotated
read-only Playwright probe; direct MCP remains disabled unless `--mcp-select`
is explicit.
Treat project `.env` and `.deepagents/` content as untrusted runtime input.

## Drift Checks

Adapter generation and adapter drift checks apply only to the source repository;
consumer projects use shared Project OS contract validation instead.

Generated drift:

```bash
python scripts/sync_agent_adapters.py --all-platforms --check
```

Factory adapter drift:

```bash
python scripts/validate_agent_runtime_drift.py --all-platforms
```

Consumer contract validation uses the shared Project OS validator:

```bash
python "$HOME/.agents/project-os/scripts/validate_repo_contracts.py" --repo-root . --fast
```

Switchyard auto runtime:

```bash
py scripts/manage_switchyard_runtime.py check --codex-config "$HOME/.codex/config.toml" --codex-home "$HOME/.codex" --switchyard-home "$HOME/.switchyard"
py scripts/manage_switchyard_runtime.py deploy --codex-config "$HOME/.codex/config.toml" --codex-home "$HOME/.codex" --switchyard-home "$HOME/.switchyard"
```

`repo_config/switchyard-routing.toml` owns automatic policy. `agents/*.toml`
own provider aliases and model IDs. Generated `$HOME/.switchyard/routes.toml`
and `$CODEX_HOME/auto.config.toml` are runtime outputs; deploy refuses drift
unless explicit migration uses `--replace-existing`. The generated upstream
client names `SWITCHYARD_API_KEY` as its credential environment variable but
never stores its value. `low` and `xhigh` remain fixed/manual. `normal` and
`high` may be selected directly or serve as the endpoints underneath `auto`.

`auto` is an opt-in runtime routing mode, not a capability or validator profile.
Policy v1 routes only between `normal` and `high`; no cost-savings claim is
established. The current runtime uses `capable_first` pending calibration, and
the compatibility smoke—not the version field alone—is the compatibility gate.

`auto` is eligible only for the Native Codex controller. It changes model
endpoint selection inside that controller route; it never selects Codex,
DeepAgents, or Tura and is not consumed by `dcode-project` or
`project-delegate`. The generated `auto.config.toml` is a separate explicit
Codex launch overlay; deploying it does not change fixed delegated-role
bindings.

| Executor or surface | Fixed profiles | `auto` |
| --- | --- | --- |
| Native Codex controller | discovered profile | yes |
| Native Codex delegated worker | discovered profile | no |
| DeepAgents task or internal worker | discovered profile | no |
| Tura worker | discovered profile | no |

Executor selection answers who executes. Profile selection answers the bounded
capability contract. `auto` answers which eligible ranked model endpoint to use.

Factory CI-safe adapter check (skip home-directory check):

```bash
python scripts/validate_agent_runtime_drift.py --all-platforms --skip-deploy-check
```

## Metadata Schema Validation

```bash
python scripts/validate_agent_metadata_schema.py
```

Schema source:

- `docs/operating_system/runtime/agent-runtime-metadata-schema.md`
