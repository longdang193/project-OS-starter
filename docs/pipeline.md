# Pipeline

For plan-bound or coordinated work, Project OS Starter uses five visible stages.
Direct local work may use a shorter path when planning dispatch identifies it as
local, reversible, and design-clear.

1. **Frame** — receive task request and establish lead-controller authority.
2. **Govern** — when coordination is selected, record the Git-tracked plan,
   ownership, dependencies, proof, and bounded admission.
3. **Execute** — run direct work, one bounded executor, or implementation lanes
   through selected runtimes inside admitted task and workspace boundaries.
4. **Prove** — settle runtime output into accepted evidence, then review and
   decide `PASS`, `FAIL`, or `BLOCKED`.
5. **Recover** — preserve blocked uncertainty, reconcile plan and Git state, and
   start only a fresh admitted attempt.

```text
Frame → Govern → Execute → Prove
  └────────────── failure or incomplete evidence ──→ Recover
```

`Recover` is not an automatic retry loop. It is a settlement boundary. The
next attempt must use reconciled plan and Git state, fresh evidence, and new
bounded admission.

Admission state is `ADMITTED | DEFERRED | BLOCKED | REJECTED`. Runtime facts use
`settled | unresolved | recovery-required`. CoS acceptance uses `PASS | FAIL |
BLOCKED`; these namespaces are not interchangeable. All-deferred scheduling
returns normally, while rejected, blocked, or unresolved execution returns a
nonzero dispatcher result.

Stage-specific detail belongs in the owning procedure, rule, or runtime
documentation rather than in this high-level pipeline.
