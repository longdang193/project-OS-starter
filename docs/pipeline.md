# Pipeline

Project OS Starter moves each task through five visible stages:

1. **Frame** — receive task request and establish lead-controller authority.
2. **Govern** — record Git-tracked plan, ownership, dependencies, proof, and
   bounded admission.
3. **Execute** — dispatch implementation lanes through selected runtimes inside
   admitted task and workspace boundaries.
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

Stage-specific detail belongs in the owning procedure, rule, or runtime
documentation rather than in this high-level pipeline.
