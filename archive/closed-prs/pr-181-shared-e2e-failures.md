# PR 181: fix: two shared end-to-end failures (capture crash, empty-draft parking)

Private team repository `barq-sprints-agentic-incident-resolution-platform-g1`, authored by me. **Closed, not merged.**

- State: CLOSED (never merged)
- Base: `main`
- Head branch: `fix/snapshot-missing-service`
- Opened: 2026-09-28T22:59:29Z; closed: 2026-09-28T23:10:17Z
- Size: +76 / -4 in 5 files
- Diff: `pr-181-shared-e2e-failures.diff` (plain `git diff`-style, no author data)


## Description (as written on the PR)

Two failures found tracing UI-created tickets on the shared stack tonight (INC0010173/INC0010175): (1) accepting a suggestion crashed knowledge capture with AttributeError: 'Incident' object has no attribute 'service' — decision recorded, resolution written, but knowledge_capture failed and the fix never reached the KB. snapshot_from_incident now tolerates missing service/impact/urgency (numerics via the load path's _as_int). (2) the model returned zero steps for a solvable Outlook query; the node built an empty draft, verification passed vacuously, and safety_check parked it as escalated_blocked. Zero steps with supporting evidence is now RetryableError so the worker retries instead of stranding the ticket. Both carry regression tests: the capture one uses the real Incident model (the SimpleNamespace stub hid the crash).
