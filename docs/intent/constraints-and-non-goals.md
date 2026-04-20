# Constraints And Non-Goals

## Constraints

- the private repo remains the development source of truth
- the public repo, when used, is derived through curated publication rather than developed independently
- feature and stage source docs remain the owners of feature/stage meaning
- generated docs and lineage surfaces must stay generated rather than becoming hand-maintained forks
- README remains a synthesized orientation layer, not the deepest truth surface

## Non-Goals

- this starter is not trying to predetermine one product architecture for every project
- the operating-system layer is not meant to replace project intent
- the intent layer is not meant to replace execution specs and plans
- rules are not meant to duplicate the full judgment and workflow detail kept in skills
- this starter is not trying to reorganize every future project artifact in one pass

## Boundary Rules

- if the question is "what is this project for?" start in `docs/intent/`
- if the question is "how should this repo build and govern work?" start in `docs/operating_system/`
- if the question is "what does this feature or stage mean right now?" start in `docs/features/` or `docs/stages/`
- if the question is "what design or implementation slice are we doing now?" start in `docs/superpowers/specs/` or `docs/superpowers/plans/`
