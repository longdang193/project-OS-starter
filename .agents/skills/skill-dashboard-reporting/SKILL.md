---
name: skill-dashboard-reporting
description: Use when turning an analytical or business decision need into a report, dashboard, scorecard, analysis, export, or semantic metric view that must be traceable to authoritative definitions and accepted through semantic, numerical, and presentation checks.
distribution_tier: starter_kit
---

# Dashboard Reporting

## Role

Turn analytical intent into the smallest correct report, dashboard, scorecard,
analysis, or export. Project OS owns the method for establishing meaning and
acceptance. The consuming project owns metric truth, semantic models, data,
provider implementation, generated artifacts, and deployment.

## When To Use

Use for:

- KPI, metric, report, dashboard, scorecard, or analytics requests
- recurring monitoring or interactive slicing
- drilldowns, comparisons, freshness requirements, or report exports
- Wren, Power BI, custom UI, notebook, CSV, SQL, or another provider

Do not use for:

- a one-off data answer with no report or reusable output
- visual styling with settled analytical meaning
- provider reference questions that do not change reporting behavior

## Core Invariant

Define business meaning once, consume it everywhere, and accept output only
when displayed conclusions trace to authoritative meaning and supporting data.

The skill requires one semantic SSOT. It never becomes that SSOT.

```text
canonical metric owner
          │
          ├── report
          ├── dashboard
          └── export
```

Do not duplicate a metric in provider formulas, dashboard-local code,
documentation, tests, or exports. Generated provider artifacts are derived
outputs, not edit targets.

## Workflow

### 1. Classify the smallest sufficient output

Do not turn every analytical request into an application.

```text
one-off question       → answer or table
investigation          → analytical report
fixed management view  → report or scorecard
recurring monitoring   → dashboard
interactive slicing    → interactive dashboard
machine consumption    → export or API
```

Ask only for decisions that change output shape, semantic meaning, data access,
or acceptance. Preserve a smaller output when it answers the request.

### 2. Resolve semantics before visualization

For every material metric, identify:

- metric identity and authoritative owner
- definition and aggregation behavior
- grain and compatible dimensions
- numerator, denominator, and included population
- exclusions, cancellations, refunds, and null semantics
- time field, timezone, date boundaries, and comparison period
- unit, currency, and conversion rules
- source and freshness expectation

Column names do not establish business meaning. If an approved definition is
missing, stop and request it before claiming a canonical KPI.

An explicitly approved prototype may use a provisional assumption. Label it
visibly as provisional, state the formula and scope, and never call it the
canonical business metric.

### 3. Define a logical reporting contract

For non-trivial work, establish the contract in the approved specification,
plan, project requirements, or existing data contract. Do not create a new
permanent `report-contract.yml` by default.

The contract states:

- audience and decision to support
- required metrics and their canonical owners
- time grain and comparisons
- dimensions, filters, and drilldowns
- freshness expectation and visible freshness behavior
- output type and deployment boundary
- required loading, empty, error, and unavailable-data behavior

Keep metric formulas in their semantic owner. The reporting contract references
them; it does not copy them.

### 4. Select provider after semantics

Reuse existing project capability:

- existing Wren context project → route to installed Wren workflow discovery
- existing Microsoft semantic model → reuse model measures and metadata
- product analytics → use existing application and contract boundaries
- one-time analysis → use table, report, notebook, or export
- no semantic definitions → resolve semantics before provider selection

Do not choose Wren, Power BI, or another provider because Project OS knows it.
When a provider is selected, retrieve its current local or installed workflow
guidance. Do not copy provider command inventories into this skill, and do not
invent provider fields, APIs, deployment steps, or generated-file formats.

### 5. Separate analytical interaction from frontend mechanics

This skill owns interaction meaning:

- what a filter means analytically
- which dimensions can filter which metrics
- whether comparisons and drilldowns preserve grain
- what a selection should recalculate

Use `skill-frontend-component-engineering` for state ownership, URL state,
async transitions, and UI mechanics. Use `skill-distinctive-frontend-design`
when visual direction is unresolved. Use `skill-full-stack-integration` when
frontend behavior crosses backend contracts or routes.

### 6. Treat freshness as a contract

Record expected freshness, last refresh, requested reporting date, and behavior
when data is stale or unknown. Do not claim current results when freshness is
not proven. Surface stale, delayed, partial, or unavailable data visibly.

### 7. Build the smallest sufficient output

Prefer existing semantic measures, components, filters, and provider features.
Do not add pages, charts, dimensions, filters, local formulas, adapters, or
deployment infrastructure without a requirement. Preserve existing behavior
outside the reporting scope.

## Acceptance

All material reporting outputs pass three layers.

### Semantic

- every metric maps to an authoritative definition
- grain, joins, filters, population, units, timezone, and null behavior are explicit
- relationships and drilldowns preserve meaning
- no unsupported business meaning is inferred from column names
- provider semantics are reused rather than duplicated

### Numerical

- representative values reconcile to the semantic definition
- numerator and denominator are correct
- cancellations, refunds, exclusions, duplicates, nulls, and empty data behave correctly
- time boundaries, comparisons, units, and currency are correct
- freshness and reporting date agree with the displayed claim

### Presentation

- charts encode the intended comparison and grain
- labels, units, currency, dates, and provisional status are visible
- loading, empty, stale, error, and unavailable states are understandable
- filters and drilldowns behave as defined by the reporting contract
- accessibility, keyboard use, focus, contrast, responsive containers, and supported themes pass the applicable frontend rule

Visual polish never overrides semantic or numerical failure.

## Composition

Invoke only applicable supporting skills:

- `skill-distinctive-frontend-design` for unresolved visual direction
- `skill-frontend-component-engineering` for stateful UI and filter mechanics
- `skill-full-stack-integration` for frontend/backend contract work
- `skill-performance-optimization` for measured performance problems
- `skill-verification-before-completion` for final completion proof

Do not add all supporting skills to `required_reads`. Keep workflow focused.

## Common Failures

- labeling `SUM(amount)` as Revenue without an approved definition
- copying a semantic metric into dashboard-local code
- using a polished mockup as numerical proof
- hiding stale or unknown freshness
- treating an ambiguous column as a business definition
- building a full BI application for a one-off table request
- adding a permanent contract artifact that duplicates an existing owner
- hardcoding provider commands that can change with installed versions

## Completion

Before claiming completion, report:

- selected output type and provider
- canonical semantic owners used
- metric, grain, filter, comparison, and freshness checks
- numerical reconciliation and representative edge cases
- presentation and accessibility evidence
- preview or deployment result, including unverified states

Final completion proof belongs to `skill-verification-before-completion`.
