# PR 179: docs: note the restricted retrieval level in the demo runbook

Private team repository `barq-sprints-agentic-incident-resolution-platform-g1`, authored by me. **Closed, not merged.**

- State: CLOSED (never merged)
- Base: `main`
- Head branch: `fix/consolidated-sprint3-work`
- Opened: 2026-09-28T22:36:52Z; closed: 2026-09-28T23:09:38Z
- Size: +7 / -0 in 1 files
- Diff: `pr-179-demo-runbook-retrieval-note.diff` (plain `git diff`-style, no author data)


## Description (as written on the PR)

Small follow-up on latest main (ec72fb8). Records in docs/demo_runbook.md that the shared EC2 and the application default run AGENT_MAX_SECURITY_LEVEL=restricted since 2026-09-28, and why the old internal default hid 5 of 11 corpus articles. No code changes; CI gate verified locally (ruff, format, mypy clean; 1380 unit + 20 integration passed).
