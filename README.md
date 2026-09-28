# Project OS Starter

> A starter kit for governed multi-agent development with AI coding agents.

Define how coding agents are assigned, bounded, equipped, observed, and accepted across multiple runtimes. Use it when one task needs explicit ownership, bounded execution, and evidence-backed acceptance.

**One controller. Bounded lanes. Evidence before acceptance.**

- Shared capability profiles
- Controlled tool access
- Explicit Git and workspace boundaries
- Observable lifecycle and acceptance evidence

[GitHub](https://github.com/longdang193/project-OS-starter) · [Issues](https://github.com/longdang193/project-OS-starter/issues) · [Setup](docs/setup.md) · [Usage](docs/usage.md)

## Requirements

- Git
- Python 3.12 or newer
- `requirements.txt` for core repository validation
- `requirements-benchmark.txt` for benchmark-only evaluation
- Optional Codex, DeepAgents, or Tura runtime setup for execution paths
- Optional Herdr setup for coordinated transport and diagnostics
- PowerShell 7 (`pwsh`) for optional DeepAgents Code setup

CI currently validates repository contracts on Ubuntu and runtime contracts on
Ubuntu and Windows. macOS support is not currently asserted.

## Get Started

### Understand the project

Read the [architecture](docs/architecture.md), [pipeline](docs/pipeline.md),
and [interactive Guided Story](https://longdang193.github.io/project-OS-starter/architecture/project-OS-starter-guided-story.html).

### Evaluate this source repository

Follow [Setup](docs/setup.md) for dependencies, then run the [Usage](docs/usage.md)
validation loop.

### Adopt Project OS

Start with [Setup](docs/setup.md) and [Usage](docs/usage.md), then adopt only
the layers your project can own, expose, and validate. Shared runtime and
starter-kit migration stays separate from project-specific docs, configuration,
code, and tests in the consuming repository.

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
Task Request → Planning / Execution Selection
                         │
          ┌──────────────┼─────────────────┐
          │              │                 │
   Direct execution  Single bounded   Git-tracked
                     executor         coordinated work
          └──────────────┼─────────────────┘
                         │
                 Runtime + Git evidence
                         │
                 Acceptance Decision
```

Project OS selects the smallest execution structure that safely fits the task.
The system separates task delivery, bounded execution, evidence, recovery, and
final acceptance. Runtime completion alone does not establish task acceptance.

In short: direct work stays direct, contained work uses one bounded executor,
and coordinated work uses Git-tracked ownership and lanes. All paths produce
evidence before acceptance.

Admission distinguishes `ADMITTED`, `DEFERRED`, `BLOCKED`, and `REJECTED`.
Deferred work is not yet runnable; blocked work requires reconciliation;
rejected work is invalid for requested admission. Reconciliation settles plan
and Git state before any fresh attempt; retry is never automatic.

Runtime state uses separate namespaces: admission is
`ADMITTED | DEFERRED | BLOCKED | REJECTED`; runtime facts are
`settled | unresolved | recovery-required`; Chief of Staff (CoS) acceptance is
`PASS | FAIL | BLOCKED`. Dispatcher exit `0` means no rejected/blocked admission
and no executed result has `unresolved: true` or a non-null `failure_kind`; all-
deferred scheduling is normal output.

[![Project OS Starter Guided Story](docs/architecture/project-OS-starter-guided-story.svg)](https://longdang193.github.io/project-OS-starter/architecture/project-OS-starter-guided-story.html)

Open the [interactive Guided Story](https://longdang193.github.io/project-OS-starter/architecture/project-OS-starter-guided-story.html), or read [`docs/architecture.md`](docs/architecture.md), [`docs/pipeline.md`](docs/pipeline.md), and [`docs/usage.md`](docs/usage.md). The Guided Story illustrates coordinated work; edit canonical sources and regenerate generated projections instead of hand-editing outputs.

## Coordinated Workflow Example

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
- **Runtime adapters** — conventions for Codex, DeepAgents, Tura, and related local execution paths.
- **Regression coverage** — tests for delivery, isolation, capability selection, lifecycle, and evidence contracts.

## Open-Source Ecosystem

Project OS Starter composes replaceable runtimes, providers, and validation tools.

- [Codex CLI](https://github.com/openai/codex) — native coding-agent runtime.
- [DeepAgents](https://github.com/langchain-ai/deepagents) — supported agent-harness SDK ecosystem.
- [Tura](https://github.com/Tura-AI/tura) — optional executor.
- Optional runtime integrations and overlays remain replaceable; this README
  does not define support guarantees for them.

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

For maintainers with source access, evaluate the project through its contracts
and tests. Install core dependencies first:

```powershell
python -m pip install -r requirements.txt
python scripts/validate_repo_contracts.py
git diff --check
```

For full test and benchmark evaluation, install the optional benchmark
dependencies:

```powershell
python -m pip install -r requirements.txt -r requirements-benchmark.txt
python -m pytest -q
```

Run adapter drift checks without regenerating outputs:

```powershell
python scripts/sync_agent_adapters.py --all-platforms --check
```

Run repository validation once; its owned drift checks run within that command.
Run explicit pytest modules for focused runtime and validator regressions. Run
adapter generation only after canonical adapter-source edits. Coordinated
DeepAgents requires the setup-owned, platform-specific wrapper generated by
`scripts/setup_deepagents_runtime.ps1` and fails closed when it is absent.

Adopt only the layers your project can own, expose, and validate. Keep project-specific setup and product code in the consuming repository.

## Local Adoption

- Native personal work follows `native-personal-local`; use `planning-dispatch.md` to choose an execution path.
- Native execution uses Codex, DeepAgents, or Tura, selected per bounded task.
- Shared operating-system docs, reusable scripts, and skills stay under a shared Project OS installation. Keep project-specific project-local folders such as `docs/intent/`, `repo_config/`, code, tests, and scripts in the consuming repository.
- When adopting this starter, create `docs/intent/` when durable project purpose needs more than `README.md`.
- DeepAgents Code runtime setup owns its version; version pinned by `scripts/setup_deepagents_runtime.ps1` is the source of truth. Use that setup path and its contract tests instead of copying numeric version values into project docs.
- Select runtime profiles explicitly, for example `--role <profile>`.

## Contributing

Keep changes focused. Update tests and documentation when behavior or contracts change. Edit canonical sources instead of generated projections. Open an issue before proposing broad changes.

## License

No license file is included yet. Review licensing before reuse or redistribution.
