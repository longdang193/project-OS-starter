# Workstream To Spec Prompt

Use this when you already know the workstream and want the next spec that
should advance it.

```text
Draft the next spec that should advance this workstream.

Workstream context:
- workstream id (use a valid ID from `docs/intent/workstreams/`):
- workstream doc:
- roadmap context:
- problem to solve next:
- desired outcome:
- constraints:
- invariants:

Please:
1. confirm the work belongs to this workstream
2. classify the bounded change
3. identify the owning docs and targets
4. draft the spec in docs/superpowers/specs/
5. recommend the next implementation step after the spec
```

Expected output:
- a spec in `docs/superpowers/specs/`
