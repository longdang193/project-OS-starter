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

Its main path is:

```text
Task Request
  → Lead Controller
  → Git-Tracked Plan
  → Bounded Admission
  → Implementation Lanes
  → Selected Runtime
  → Accepted Evidence
  → Acceptance Decision
```

The path uses three boundaries:

- **Intent and control** — the controller coordinates one task; the Git-tracked
  plan owns order, dependencies, ownership, and proof requirements; admission
  narrows scope and capability before execution.
- **Bounded execution** — implementation lanes own work inside assigned paths
  and workspace boundaries; selected runtimes execute only admitted work.
- **Evidence, recovery, and acceptance** — runtime output becomes accepted
  evidence before the controller decides `PASS`, `FAIL`, or `BLOCKED`.

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
- Git-tracked plans preserve durable coordination state.
- Runtime completion stays distinct from acceptance.
- Unknown or incomplete evidence stays `BLOCKED` instead of becoming success.
