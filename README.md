# barq-agentic-it-engineer

An agentic IT engineer for ServiceNow incidents. A ticket arrives, the agent investigates it
like a human engineer would (reads the ticket, searches the knowledge base, checks the caller's
account, asks the caller questions in chat), decides what is safe to do on its own, acts, verifies,
and hands the ticket to a person when it should not decide alone.

This repository holds my own work for the BARQ x Sprints programme. It **builds on the programme's
team repository** (the incident-resolution platform the whole team wrote: webhook, queue,
retrieval, tracing, the scoped ServiceNow app). That base is included under `code/` because my
changes live inside it; see [Provenance and licence](#provenance-and-licence).

## What it does

```
ServiceNow incident
   | business rule (scoped app) sends a minimal event
   v
FastAPI webhook (202, no model on the request thread)
   | Redis / Celery
   v
Engineer loop  (src/agent/engineer)
   |  turn.py    the loop: observe, think, call a tool, observe again
   |  tools.py   tools the agent may call (read ticket, search KB, account facts, reply, route, resolve ...)
   |  policy.py  hard rules in code, not in the prompt (security, P1, locked tickets, personal data)
   |  report.py  the structured report shown on the engineer card
   |  knowledge.py  engineer-approved fixes become knowledge articles
   v
Postgres (state, audit)  Qdrant (hybrid retrieval)  Langfuse (one trace per turn)
   |
   v
ServiceNow: chat-only page for callers, "BARQ AI" view + card for engineers
```

- **Chat-only for callers.** No approve/reject buttons for the person who raised the ticket: they talk to the agent.
- **Engineer card with one button.** *Take over* / *Hand back*, an instruction box and *Undo*. No approval queue.
- **Hard policy.** Anything touching security, a priority-1 ticket, a locked ticket, or personal data is
  decided by code in `policy.py` and goes to a person; the model cannot talk its way past it.
- **Everything traced.** Every agent turn is a Langfuse trace linked from the card.
- Backend is selected with `AGENT_GRAPH_BACKEND=engineer`; the older fixed LangGraph pipeline from the team repo is still there.

## Run it

Needs Docker, [`uv`](https://docs.astral.sh/uv/), Python 3.12+ and a ServiceNow instance (I used a personal developer instance).

```bash
cd code
cp .env.engineer.example .env.pdi        # fill in the placeholders; never commit it
./pdi.sh up -d                           # api, worker, postgres, redis, qdrant (own containers, ports 18000/15432/16379/16333)
# ServiceNow must reach the API: expose it, e.g. cloudflared tunnel --url http://127.0.0.1:18000
python ../tools/setup_pdi.py <public-url>        # point the instance's event and token addresses at it
python ../tools/install_engineer_sn.py           # install the engineer UI pieces on the instance
```

The scoped ServiceNow app is in `code/servicenow/ai_incident_orchestrator` (built with the ServiceNow SDK).
`docs/DEMO_GUIDE.md` is the walk-through I used for the demo; `docs/HOW_IT_WORKS.md` explains the flow.

Unit tests (no Docker, no ServiceNow needed):

```bash
cd code
uv sync --all-extras --dev --locked
uv run ruff check . && uv run ruff format --check .
uv run pytest -q
```

## How it was tested

All numbers are from `docs/RESULTS.md` and the raw output in `evidence/` (live runs on my developer instance, October 2026):

| Check | Result |
|---|---|
| Scenario book, 16 real situations (true/false account lock, someone else's account, injection, password in the ticket, VPN, Outlook, hardware, vague, Arabic, talk to a person, cancel, still broken, engineer instruction, duplicate) | 16/16 (across runs) |
| Reply quality, a second model grades every reply | 4-5 / 5, all safe |
| Real-browser walk (chat, live status line, engineer card, take over / hand back, caller confirms) | 21/21 |
| Earlier fixed-pipeline suites: core, triage, conversation, permissions, engineer page, users' page, 22-case mix, real browser | 7/7, 4/4, 5/5, 12/12, 8/8, 10/10, 22/22, 18/18 |
| Unit tests at the time | 2,144 passed |
| Agent turn time | about 15-45 s |

The live suites need a configured instance and are in `code/scripts/live/`. The unit-test count in this repo is reported in the PR/commit that published it.

## Layout

| Path | What |
|---|---|
| `code/` | The working system: `src/` (API, workers, agent, engineer loop), `tests/`, `migrations/`, `servicenow/` (scoped app), `docker-compose*.yml`, `pdi.sh`, team docs under `code/docs/` |
| `tools/` | Instance setup and ops helpers: `setup_pdi.py`, `users_pdi.py`, `install_engineer_sn.py`, `allow_privs.py`, `trace.sh` (follow one ticket end to end), `sync_team.sh`, `servicenow_change_manifest.jsonl` (what the installer created) |
| `docs/` | `DEMO_GUIDE.md`, `HOW_IT_WORKS.md`, `PLAN.md`, `RESULTS.md`, `VIDEO_PLAN.md`, `PROJECT_NOTES.md` (technical history and decisions) |
| `evidence/` | Raw output of the live test runs |
| `slides/` | The demo-day deck |
| `archive/` | Earlier work kept for reference: `audit-2026-10-02/` (system audit, fixes as patches, runbook), `shared-instance-audit/`, `servicenow-revert/`, `servicenow-research/` |

Demo video: link to be added.

## Provenance and licence

The base platform is the BARQ x Sprints team repository; its contributors wrote most of the original
pipeline, retrieval, tracing and ServiceNow app. My additions are the engineer loop and its policy
and report layers, the chat-only UI and engineer card, the ServiceNow installers in `tools/`, the
live scenario book and browser walk, and the audit work in `archive/`. The team repository carries
no licence file, so **no licence is granted here yet**; all rights stay with the respective authors.

## Path map for the notes

Documents under `docs/` and some scripts were written when my working folder was called `PDI/`.
Read `PDI/barq` as `code/`, `PDI/tools` as `tools/`, `PDI/ev*` as `evidence/pdi-live-runs/`, and
`PDI/manifest.jsonl` as `tools/servicenow_change_manifest.jsonl`. `tools/sync_team.sh` and
`tools/trace.sh` expect that old layout and need their paths adjusted before use.
