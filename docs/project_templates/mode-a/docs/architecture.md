# Architecture

This document describes the system shape for `<project-name>`.

## Components

| Component | Responsibility | Interfaces |
| --- | --- | --- |
| `<component-one>` | `<responsibility>` | `<input-output-or-api>` |
| `<component-two>` | `<responsibility>` | `<input-output-or-api>` |
| `<component-three>` | `<responsibility>` | `<input-output-or-api>` |

## Data Flow

1. `<source>` provides `<input>`.
2. `<processor>` transforms it into `<intermediate-output>`.
3. `<consumer>` uses `<final-output>` for `<purpose>`.

## Runtime Boundaries

- Local execution: `<local-runtime-boundary>`
- CI execution: `<ci-runtime-boundary>`
- Deployment or hosted execution: `<deployment-boundary-or-none>`

## Dependencies

| Dependency | Version Or Source | Why It Exists |
| --- | --- | --- |
| `<dependency>` | `<version-or-source>` | `<purpose>` |

## Security And Privacy

Document what data is sensitive, which files must stay private, and which outputs are safe to publish. Keep private values out of tracked files.

## Change Notes

When architecture changes, update this document together with setup, configuration, usage, and pipeline docs if those workflows are affected.
