# Intent Layer

This directory holds the project's stable what-and-why sources.

Use it for:

- the original problem the project is solving
- who the project is for
- what outcomes matter
- what promises should remain true
- what the project deliberately does not try to do

This layer governs by purpose.

It is different from `docs/operating_system/`, which governs by method.

It is also different from `docs/superpowers/specs/` and
`docs/superpowers/plans/`, which are execution-facing artifacts rather than
stable source docs.

## Files

- [project-charter.md](./project-charter.md)
  - core problem, project shape, and enduring promises
- [stakeholders.md](./stakeholders.md)
  - who depends on the project and what they need from it
- [success-outcomes.md](./success-outcomes.md)
  - what good looks like if the project succeeds
- [constraints-and-non-goals.md](./constraints-and-non-goals.md)
  - limits, boundaries, and deliberate exclusions

## Rules

- keep these docs stable and source-like
- do not turn them into execution logs or release notes
- treat them as source material for later README synthesis
- if a document is really about how the repo should build, govern, or route
  work, it belongs in `docs/operating_system/` instead
