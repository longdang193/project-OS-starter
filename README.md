# Project OS Starter

## A starter kit for governed multi-agent development with AI coding agents.

Define how coding agents are assigned, bounded, equipped, observed, and accepted across multiple runtimes. Use it when one task needs explicit ownership, bounded execution, and evidence-backed acceptance.

**One controller. Bounded lanes. Evidence before acceptance.**

- Shared capability profiles
- Controlled tool access
- Explicit Git and workspace boundaries
- Observable lifecycle and acceptance evidence

[GitHub](https://github.com/longdang193/project-OS-starter) · [Issues](https://github.com/longdang193/project-OS-starter/issues) · [Setup](docs/setup.md) · [Usage](docs/usage.md) · [Adoption guide](docs/operating_system/adoption/project-adoption-migration-guide.md)

## Why Project OS Starter?

Individual coding agents can write useful code. Multi-agent development adds harder problems:

- Who owns each task?
- Which tools and runtimes may each worker use?
- How do concurrent changes avoid colliding?
- What counts as running, finished, or accepted?
- Which evidence survives retries, replacement attempts, and review?

Project OS Starter supplies repository structure and contracts for answering those questions consistently.

## How It Works

```text
Task Request → Lead Controller → Git-Tracked Plan → Bounded Admission
                                                        │
                                              Implementation Lanes
                                                        │
                                               Selected Runtime
                                                        │
                                              Runtime Evidence
                                                        │
                                             Acceptance Decision
```

The system separates task delivery, bounded execution, evidence, recovery, and final acceptance. Runtime completion alone does not establish task acceptance.

If admission or evidence fails, work enters `BLOCKED`. Reconciliation settles plan and Git state before any fresh attempt; retry is never automatic.

Runtime state uses separate namespaces: admission is
`ADMITTED | DEFERRED | BLOCKED | REJECTED`; runtime facts are
`settled | unresolved | recovery-required`; CoS acceptance is
`PASS | FAIL | BLOCKED`. Dispatcher exit `0` means no rejected/blocked admission
and no unresolved executed result; all-deferred scheduling is normal output.

[![Project OS Starter Guided Story](docs/architecture/project-OS-starter-guided-story.svg)](https://longdang193.github.io/project-OS-starter/architecture/project-OS-starter-guided-story.html)

Open the [interactive Guided Story](https://longdang193.github.io/project-OS-starter/architecture/project-OS-starter-guided-story.html), or read [`docs/architecture.md`](docs/architecture.md), [`docs/pipeline.md`](docs/pipeline.md), and the [canonical Archify workflow source](docs/architecture/project-OS-starter-guided-story.workflow.json). Edit canonical sources; regenerate SVG, HTML, adapters, and kit outputs; never hand-edit generated projections.

## Example Workflow

```text
Request: implement an API change, update its frontend usage, and review it.

Controller
 ├─ Lane A: backend change, selected profile, bounded workspace
 ├─ Lane B: frontend change, selected profile, bounded workspace
 ├─ Validate dependencies and collect runtime evidence
 └─ Review combined result and decide PASS / FAIL / BLOCKED
```

Workers own engineering inside assigned scope. The controller owns orchestration boundaries, evidence requirements, and acceptance.

## What It Governs

| Concern | Contract |
| --- | --- |
| Assignment | Roles, profiles, ownership, and task boundaries stay explicit. |
| Execution | Workers run through selected runtimes with bounded scope. |
| Capabilities | Tool and MCP access is selected deliberately, not inherited implicitly. |
| Workspace | Git and workspace boundaries make concurrent changes inspectable. |
| Lifecycle | Preparation, delivery, execution, observation, cleanup, and result state stay distinct. |
| Acceptance | Required evidence drives `PASS`, `FAIL`, or `BLOCKED`; worker claims do not. |

## Included Structure

- **Agent profiles** — reusable role and capability definitions.
- **Canonical sources** — one owning layer for rules, procedures, templates, and configuration.
- **Generated projections** — downstream instruction and starter-kit outputs derived from canonical sources; edit canonical sources, then regenerate outputs.
- **Validation tooling** — repository, metadata, configuration, lifecycle, and package-boundary checks.
- **Runtime adapters** — conventions for Native Codex, DeepAgents, Tura, and related local execution paths.
- **Regression coverage** — tests for delivery, isolation, capability selection, lifecycle, and evidence contracts.

## Open-Source Ecosystem

Project OS Starter composes replaceable runtimes, providers, and validation tools.

- [Codex CLI](https://github.com/openai/codex) — native coding-agent runtime.
- [DeepAgents](https://github.com/langchain-ai/deepagents) — supported agent-harness SDK ecosystem.
- [Tura](https://github.com/Tura-AI/tura) — optional executor.
- [LightRSI](https://github.com/zjunlp/LightRSI) — optional Tura runtime layer.
- [9router](https://github.com/decolua/9router) — model-routing provider.
- [LangGraph](https://github.com/langchain-ai/langgraph) — DeepAgents runtime support.
- [OpenCodeReview](https://github.com/alibaba/open-code-review) — optional advisory code-review overlay.

The setup script installs `deepagents-code` as a separate optional coding-agent runtime. Its public repository and license are distinct from the DeepAgents ecosystem project above.

## Design Principles

- **Evidence before acceptance** — completion is a claim until required proof exists.
- **Explicit authority** — controllers, workers, reviewers, and cleanup actions have separate responsibilities.
- **Repository as source of truth** — Git state, tests, contracts, and recorded evidence outrank chat output.
- **Canonical over copied** — generated surfaces are rebuilt from their owners.
- **Unknown stays unknown** — missing or ambiguous runtime evidence does not become success.

## Where It Fits

```text
Coding runtime
Codex / DeepAgents / Tura
          │
          ▼
Project OS Starter
assignment · boundaries · tools · lifecycle · evidence · acceptance
          │
          ▼
Project repository
code · tests · Git history · review
```

Project OS Starter is not a foundation model, IDE, memory database, or application framework. It is the operating layer around coding-agent execution.

## Scope And Status

This repository is an active starter/reference implementation. Runtime integrations, contracts, and generated surfaces may change as the system is hardened.

It does not promise autonomous engineering, zero-configuration deployment, universal runtime support, or performance gains without matching measurements.

Public distribution is curated separately from deeper implementation and runtime internals. The current public surface is an overview, not a complete drop-in product distribution.

## Evaluation Path

For maintainers with source access, evaluate the project through its contracts and tests:

```powershell
python scripts/validate_repo_contracts.py
python -m pytest -q
git diff --check
```

Adopt only the layers your project can own, expose, and validate. Keep project-specific setup and product code in the consuming repository.

## Local Adoption

- Native personal work follows `native-personal-local` and `docs/operating_system/planning/planning-dispatch.md`.
- Native execution uses Codex, DeepAgents, or Tura, selected per bounded task.
- Shared operating-system docs, reusable scripts, and skills stay under the shared Project OS installation: `~/.agents/project-os` and `~/.agents/skills`.
- Keep project-specific project-local folders such as `docs/intent/`, `docs/superpowers/`, `repo_config/`, code, tests, and scripts in this repository when adopting this starter.
- When adopting this starter, create `docs/intent/` when durable project purpose needs more than `README.md`.
- DeepAgents Code runtime setup owns its version; version pinned by `scripts/setup_deepagents_runtime.ps1` is currently `deepagents-code==0.1.74`, which brings `deepagents==0.7.18`.
- DeepAgents uses `OPENAI_API_KEY` from the same `~/.codex/tokenpilot.env` file used by Codex; do not use a separate project secret file.
- DeepAgents runtime version bumps require compatibility proof for `scripts/patch_deepagents_runtime.py`; do not bump package version alone.
- Select runtime profiles explicitly, for example `--role <profile>`.
- DeepAgents MCP is opt-in through explicit Herdr selection. Herdr accepts `--mcp-select` and forwards selected servers to `dcode-project`.
- MCP `headers` values must be `${VAR}` references. MCP `env` values may be `${VAR}` references or non-sensitive literals.

## Contributing

Keep changes focused. Update tests and documentation when behavior or contracts change. Edit canonical sources instead of generated projections. Open an issue before proposing broad changes.

## License

No license file is included yet. Review licensing before reuse or redistribution.
