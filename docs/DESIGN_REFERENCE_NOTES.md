# Design Reference Notes

This note records Touchstone's internal product shape and integration boundaries.

## Repository Shape

- root-level Skill/Plugin project.
- multi-agent entries for Codex, Claude Code, and Cursor.
- `commands/` for reusable workflows.
- `skills/` for separate capabilities: full research, investor panel, LHB analysis, trap detection, and data collection.
- `harness/` for auditable runs, schemas, evaluation, and replay.
- root `run.py` as the obvious execution entry.
- business code below the relevant Skill rather than hidden in a generic scripts folder.

## Adopted Patterns

- staged stock research pipeline rather than a single prompt.
- preflight profile plus 22 research dimensions.
- quick/standard/deep depth modes.
- data-gap acknowledgement and agent self-review before report finalization.
- machine-checkable gates before trade-level signals.
- separate trap detection, LHB interpretation, and investment-panel review.
- rule families and local evidence contracts instead of copied named-person rules.

## Applied Here

- repository root is the plugin root.
- `skills/a-share-investment-research` is the main research Skill.
- auxiliary skills separate trap detection, LHB analysis, data collection, and panel review.
- `harness/` is the engineering layer for auditable runs and evals.
- `references/research-quality-gates.md` captures 22-dimension coverage, depth profiles, and self-review gates.
- `signal_orchestrator.py` writes quality gate status into `audit.json`.

## Boundaries

- Do not vendor external source code, report renderers, personas, or private rule text.
- Rewrite every rule as a local Touchstone contract aligned to the A-share dynamic-alert objective.
- Keep all signal outputs conditional and evidence-based.
