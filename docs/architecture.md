# Architecture

Project OS Starter is an operating layer around coding-agent execution. It
keeps authority, bounded work, evidence, recovery, and acceptance separate.

## Guided Story

The canonical Archify workflow source is
`docs/architecture/project-OS-starter-guided-story.workflow.json`.

Static preview: `docs/architecture/project-OS-starter-guided-story.svg`.
Interactive viewer: `docs/architecture/project-OS-starter-guided-story.html`.
GitHub Pages publishes both projections from
`.github/workflows/guided-story-pages.yml`.

Project OS selects the smallest execution structure that safely fits the task:

- direct execution for local, reversible, design-clear work
- one bounded executor for a contained task
- Git-tracked coordination for durable ownership, dependencies, resume, or
  parallel writers

Project Secretary is optional. When active, it routes attention into this
existing selection policy; when absent, all three paths remain directly
callable. Secretary does not become another CoS or acceptance authority.
Its optional Docket lives under execution-facing `docs/superpowers/` only when
unresolved attention cannot be reconstructed from canonical evidence. Adapter
receipts and event observations remain bounded evidence: they do not become
plan/Git truth, acceptance, or lifecycle state.

The Guided Story illustrates the coordinated multi-agent path:

```text
Task Request
  → Optional Project Secretary
  → Lead Controller
  → Git-Tracked Plan
  → Bounded Admission
  → Implementation Lanes
  → Selected Runtime
  → Accepted Evidence
  → Acceptance Decision
```

The path uses three boundaries:

- **Intent and control** — when coordination is selected, the controller
  coordinates one task; the Git-tracked plan owns order, dependencies,
  ownership, and proof requirements; admission narrows scope and capability
  before execution.
- **Bounded execution** — direct work, one bounded executor, or implementation
  lanes operate inside their assigned paths and workspace boundaries; selected
  runtimes execute only admitted work.
- **Evidence, recovery, and acceptance** — runtime output and bounded receipts
  become evidence before the controller decides `PASS`, `FAIL`, or `BLOCKED`.
  Receipts do not become durable coordination truth.

Recovery remains explicit. Unsafe admission or incomplete evidence enters
`BLOCKED`. `RECONCILE` settles plan and Git state; it does not silently return
to execution. The current attempt ends at reconciliation; a fresh attempt
restarts at bounded admission after settled evidence.

State namespaces stay separate: admission uses
`ADMITTED | DEFERRED | BLOCKED | REJECTED`; runtime facts use
`settled | unresolved | recovery-required`; CoS acceptance uses
`PASS | FAIL | BLOCKED`. All-deferred admission is normal scheduling output;
rejected, blocked, or unresolved execution is a nonzero dispatcher outcome.

## Shape Rationale

- One controller prevents competing acceptance authority.
- Git-tracked plans preserve durable coordination state when coordination is
  selected.
- Runtime completion stays distinct from acceptance.
- Unknown or incomplete evidence stays `BLOCKED` instead of becoming success.
