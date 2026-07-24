---
name: skill-full-stack-integration
description: Use when frontend features with matching integration notes need backend API contract reconciliation, route changes, typed client wiring, or end-to-end verification.
required_reads:
- docs/operating_system/tooling/code-intelligence-tools.md
distribution_tier: starter_kit
---

# Full-Stack Integration

## Role

Complete the smallest frontend-to-backend vertical slice while preserving one transport-contract owner. Colocated `*.integration.md` files describe temporary UI intent and required evidence; they never replace schemas, generated clients, backend routes, or tests.

## Sidecar Contract

Keep sidecars brief:

```md
# UserProfileCard Integration
Operation: `getUserProfile`
Contract owner: `openapi.yaml#getUserProfile`
Status: pending

## UI Behavior
- loading: `ProfileSkeleton`
- 403: `AccessDenied`
- 404: `UserNotFound`

## Required Evidence
- backend contract and authorization checks pass
- frontend documented states pass
- browser request and visible flow match contract
```

Reference request and response schemas; do not copy them.

## Core Method

1. Read the feature, matching sidecar, existing client or query, mocks, backend route, contract owner, and focused tests.
2. Use source, canonical contracts, security policy, routes, and tests to establish current behavior. If the sidecar requests conflicting behavior, report the exact mismatch and affected owners, present viable options, and ask the user to decide before implementation. Security and data-safety constraints remain non-negotiable; after approval, update all affected owners together.
3. Choose one code-intelligence path:
   - native tools for known local scope
   - Serena for exact symbols, references, implementations, and diagnostics
   - fresh GitNexus for unknown broad flow, route consumers, or cross-repo impact
4. Before changing an API route handler, use GitNexus `api_impact` when available and fresh. Use `route_map` only when route ownership or consumers remain unclear; use `shape_check` only when response fields change. Fall back to source search when unavailable.
5. Implement the smallest complete slice: canonical contract, backend validation and authorization, narrow route or service change, existing client generation command, frontend query or mutation, and documented UI states. Reuse existing mocks; do not add mock infrastructure by default.
6. Run focused backend and frontend checks. Use Playwright MCP for repeatable user flows and accessibility state. Use Chrome DevTools MCP only for network, console, payload, or runtime diagnosis; do not duplicate the same check.
7. Remove the sidecar when all acceptance evidence passes. If blocked, delete completed items and retain only exact unresolved work.
8. Store MCP Memory only for a verified recurring invariant or costly failure not already owned by source or documentation. Never store task progress, payloads, credentials, or user data.

## Common Mistakes

- copying transport schemas into frontend notes
- invoking every MCP instead of one tool per question
- changing shared authorization or error mapping without consumer impact
- adding OpenAPI, MSW, registries, validators, or status systems not already needed
- keeping completed sidecars as permanent parallel documentation
- treating browser MCP evidence as replacement for committed tests
