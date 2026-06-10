# UZI-Skill Reference Notes

Reference repository: `https://github.com/wbh604/UZI-Skill`.

Observed structure:

- root-level product layout.
- multi-platform entries: `CLAUDE.md`, `CODEX.md`, `GEMINI.md`, plugin manifests.
- `commands/` for user-facing workflows.
- `skills/` for separate capabilities: deep analysis, investor panel, LHB analyzer, trap detector.
- `hooks/` for session behavior.
- root `run.py` as the obvious execution entry.
- business code below the relevant Skill rather than hidden in a generic scripts folder.

Applied here:

- repository root is now the plugin root.
- `skills/a-share-investment-research` is the main research Skill.
- auxiliary skills mirror UZI's separation of trap detection, LHB analysis, and investor panel.
- `harness/` is kept as our additional engineering layer for auditable runs and evals.

Not copied:

- UZI source code, assets, investor personas, report renderer, or proprietary rule text.
- Any rules were rewritten as local contracts aligned to our A-share dynamic-alert objective.
