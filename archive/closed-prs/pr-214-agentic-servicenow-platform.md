# PR 214: Agentic ServiceNow platform: autonomous fulfilment, engineer actions, critical fixes

Private team repository `barq-sprints-agentic-incident-resolution-platform-g1`, authored by me. **Closed, not merged.**

- State: CLOSED (never merged)
- Base: `main`
- Head branch: `feat/barq-agentic-servicenow`
- Opened: 2026-10-03T02:32:11Z; closed: 2026-10-03T03:28:15Z
- Size: +13035 / -103 in 101 files
- Diff: `pr-214-agentic-servicenow-platform.diff` (plain `git diff`-style, no author data)

## Relationship to this repository

This PR was closed unmerged (draft, built on the admin-chatbot PR of the team repository). Most of its work lives on in `code/`:
of its 11,223 added non-blank lines, **10,305 (91.8 %)** are present in the matching file of `code/`; 74 of its 101 files are fully
present, 23 partly (mostly later edits of the same files, `uv.lock`, Docker files) and 4 are absent: the Streamlit chat UI
(`src/app/chat_ui/__init__.py`, `app.py`, `state.py`, `tests/chat/test_ui_state.py`), which was dropped on purpose because
the ServiceNow-native pages replaced it. The full diff is kept next to this note.

## Description (as written on the PR)

## What and why

**Draft — work in progress. Do not merge.** This branch builds on #213 (admin chatbot, Kerolos's commits are included unchanged) and turns the platform into an agentic one that works incidents inside ServiceNow. The full target design, every scenario and the task plan are in [`docs/barq_agentic_platform_design.md`](docs/barq_agentic_platform_design.md).

Done so far (tasks T0–T3 of the design's §16):

- **Critical fixes** (from the 2026-10-02 audit, re-reviewed and re-tested): a semantic-cache follower must pass its own eligibility, injection and risk gates before reusing a cluster's fix, and a failed follower write is no longer reported as success; no approval or rejection can be recorded on a run with no paused interrupt; secrets inside JSON and other key=value spellings are redacted before any model or trace; `act` fails closed outside a compiled graph.
- **Autonomy** (`AGENT_AUTONOMY_LEVEL`: off / suggest / assist / autonomous, default `suggest` so behaviour is unchanged until switched on): the agent routes an incident to its category's group, sets it In Progress, gives the caller the cited fix and resolves it; the caller can reopen. Only an applied fix is fulfilled (low-risk draft that passed every gate, or a fix a person approved); incidents with no real caller are never resolved; high risk, low confidence, no evidence and guardrail blocks always wait for a person. New registered tools `assign_incident` and `resolve_incident` re-read the incident, refuse a Human Lock, keep a group a person chose, leave an incident a person moved on, and never repeat after a crash.
- **ServiceNow side** (shared instance `dev407364`, tracked in update sets and a rollback manifest): field-level write ACLs for the agent role only while the incident is not human-locked; the agent shows as *BARQ AI Agent*; a `BarqBackend` bridge script include (credential from system properties, engineer identity passed with every decision); *Approve AI fix*, *Reject AI fix*, *Take over from AI* actions replacing the old field-only actions (deactivated, not deleted).

## How it was verified

- `ruff check .`, `ruff format --check .`, `mypy src` (193 files): clean. `pytest`: 1,979 passed, 44 skipped (services), 0 failed.
- Live on `dev407364` as the integration user: start + route + resolve applied, repeat skipped as already applied, Resolved by = the agent; a human-locked incident refused by the code and, on a raw PATCH, by the ACLs (all fields dropped). Bridge called from a scoped background script: token + executions read OK and the paused run found.
- Not yet: CI on this PR, deployment to the shared EC2, live end-to-end incident runs (tasks T4–T5).

## Checklist

- [x] Lint, format, type-check and tests pass locally
- [x] No credential, token or instance secret added
- [x] ServiceNow scripts use internal choice values
- [x] New ServiceNow artifacts are in scope `x_2215032_ai_inc_0`
- [x] Docs updated (design, tool registry, `.env.example`)
