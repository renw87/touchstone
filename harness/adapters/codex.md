# Codex Adapter

Use this adapter when running a Harness task with Codex.

Prompt pattern:

```text
Use $a-share-investment-research.
Read harness/runs/{run_id}/input.json and harness/runs/{run_id}/prompt.md.
Produce:
- harness/runs/{run_id}/report.md
- harness/runs/{run_id}/signal.json
- harness/runs/{run_id}/audit.json

Keep all signals conditional. If data is missing, mark insufficient_data and cap the signal at watch.
```

Codex should use the plugin Skill at:

```text
skills/a-share-investment-research/SKILL.md
```
