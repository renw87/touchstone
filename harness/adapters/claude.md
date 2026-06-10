# Claude Code Adapter

Use `CLAUDE.md` as the entry point.

Prompt pattern:

```text
Read harness/runs/{run_id}/input.json and prompt.md.
Follow CLAUDE.md.
Write report.md, signal.json, and audit.json into the same run directory.
```

Do not output unconditional trading instructions.
