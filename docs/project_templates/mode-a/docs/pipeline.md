# Pipeline

This document explains the workflow or processing stages for `<project-name>`.

## Overview

Describe the end-to-end flow in plain language:

1. `<stage-one-name>`: `<what-enters-and-what-leaves>`
2. `<stage-two-name>`: `<what-enters-and-what-leaves>`
3. `<stage-three-name>`: `<what-enters-and-what-leaves>`

## Stage Details

| Stage | Owner | Inputs | Outputs | Validation |
| --- | --- | --- | --- | --- |
| `<stage-one-name>` | `<owner>` | `<inputs>` | `<outputs>` | `<checks>` |
| `<stage-two-name>` | `<owner>` | `<inputs>` | `<outputs>` | `<checks>` |
| `<stage-three-name>` | `<owner>` | `<inputs>` | `<outputs>` | `<checks>` |

## Handoffs

Document the contract between stages: file paths, schemas, service messages, naming conventions, and failure behavior. Keep this as prose or tables for Mode A.

## Recovery

- Retry point: `<retry-point>`
- Idempotent step: `<idempotent-step>`
- Manual cleanup: `<cleanup-command-or-policy>`

## Operational Checks

Before considering a run complete, verify:

- required inputs were present
- every stage completed or recorded an intentional skip
- outputs were written to the documented destination
- validation checks passed
