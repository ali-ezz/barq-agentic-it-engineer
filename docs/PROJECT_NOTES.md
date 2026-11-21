# Project notes: technical history and decisions

Condensed from my working notes. Credentials, hosts, tunnel links and private chat have been removed.

## 1. Where the work lives

Work happens in `code/`, a copy of the team platform (PR 213 of the team repo, an admin KB chatbot)
plus my commits, run against my own ServiceNow developer instance with its own containers
(compose project `barqpdi`, ports 18000 API / 15432 Postgres / 16379 Redis / 16333 Qdrant) and a
quick tunnel (cloudflared) so the instance can reach the API. Tracing to Langfuse is switchable.
Settings are in a git-ignored `.env.pdi`. Helper scripts are in `tools/`; `trace.sh INC00xxxxx`
prints events, runs, steps with timings, failures, approvals and the worker log for one ticket.

## 2. Agentic engineer (built 4 October 2026)

Goal: a fully agentic, human-like IT engineer; chat-only UIs for callers (no buttons), an engineer
card with one button (Take over / Hand back), an instruction box and Undo; no approvals; desktop only.

- Backend `AGENT_GRAPH_BACKEND=engineer`: `src/agent/engineer/` (`turn.py` loop, `tools.py`, `policy.py`
  hard rules, `prompts.py`, `report.py`, `knowledge.py`).
- Models go through a LiteLLM proxy and fall back to an own Google AI Studio key (free tier,
  one model only).
- ServiceNow side (installer `tools/install_engineer_sn.py`; every created record is listed in
  `tools/servicenow_change_manifest.jsonl`): a scripted REST endpoint `/barq_account` (account facts
  and actions), a global helper script include for sign-in events and lock state, fields `ai_report`
  (JSON) and `ai_activity`, field ACLs, an Ajax back-end for the card, a UI script, a rewritten
  conversation rule, the chat widget; the old Approve/Reject/Take over/Hand back form buttons were
  deactivated. Test people `barq.*` come from `scripts/live/engineer_fixtures.py`.
- Tests: `tests/test_engineer_agent.py`; live scenario book `scripts/live/verify_engineer_book.py`
  (16 scenarios); browser walk `scripts/live/verify_ui_browser.py`. The older live suites test the
  old graph and do not apply in engineer mode.
- Speed: the live status line is written in the background (it used to be 26 s of a 44 s turn);
  turns are now about 15-45 s.
- Status at 4 Oct, 21:00: scenario book 16/16 across runs, browser walk 21/21, 2,144 unit tests.

## 3. Fixed-pipeline results on the developer instance (3-4 Oct 2026)

Core 7/7, triage 4/4, conversation 5/5, permissions 12/12, engineers' page 8/8, users' page 10/10,
22-case mix 22/22, real browser 18/18 (see `docs/RESULTS.md`). Fixes found on the way:

- Search models kept in a Docker volume: a rebuild made the first ticket download them (82 s) and hit
  the 150 s task limit.
- The `incident` table refused writes from the scoped app ("cross-scope access policy"); this was the real
  cause of the conversation failures. Fixed with table update/create access plus
  `GlideTableManager.invalidateTable('incident')`; a plain cache flush is not enough.
- App privileges requested at run time must be allowed (`tools/allow_privs.py`, rerun after new runs).
- An old build of the scoped app had no guard for a human rejection: the rejection set the AI state to
  failed, a retry rule re-sent the ticket and the agent parked it again. Installing the current build
  (`now-sdk install`, plain install, not `--reinstall`) fixed it; the install blanks one endpoint
  property, so rerun `setup_pdi.py` afterwards.
- A paused run is routed and the caller told before it is marked awaiting approval.
- Caller-message prompt: a final "if it still fails, IT checks X" step is needed when the caller
  already said X (locked account); the old prompt was 4/4 wrong, the new one 4/4 right.
- A leader whose incident closed releases its similar-ticket cluster at once.
- Workers: 3 -> 4 slots on the Mac (memory permitting). A shared 3.8 GB server with no swap ran out
  of memory under test bursts at 4; stay at 2 there.

## 4. Agentic platform design (3 Oct 2026)

`code/docs/barq_agentic_platform_design.md`: roles, lifecycle, autonomy levels, tools, remediation
(runbooks, standard changes, catalog, account unlock; a lab runner for infrastructure because the
instance has no MID Server), 88 scenarios, UI, memory, clean-up, reversibility, tests and plan.
Direction: very autonomous (the caller is the human check for low risk: the AI resolves, the caller
confirms or stays silent, a reopen goes to an engineer), clean ServiceNow, everything reversible.

Facts checked on the instance: out-of-box reopen on caller comment; `mark_resolved` sets "Resolved by";
auto-close after 7 days is instance-wide; email is off; portal ticket actions offer Close/Reopen;
closing a problem does not resolve its incidents; ITSM Spoke, standard-change catalog and Password Reset
are installed; no MID Server. The backend is plain HTTP on a bare IP in the shared setup, so a
ServiceNow page cannot call it from the browser (mixed content): calls go server-side through RESTMessageV2.

Defects found in a hidden, pre-existing ServiceNow UI layer (Approve/Refuse UI actions edited only
ServiceNow fields and never called the backend, so the run stayed parked; a capture action hard-coded
a secret and marked the incident complete even when the backend call failed; none required a role)
led to building the engineer view and card from scratch, with server-side calls and role checks.

## 5. System audit (2 Oct 2026)

Full record: `archive/audit-2026-10-02/` (`audit_2026-10-02.md`, `operations_runbook.md`, and two patches:
`audit-fixes.patch` for code/test/docs fixes, `infra-hardening.patch` for compose hardening).
Highlights: a follower of a reused answer completed without risk/approval (P1 bypass) and secrets in JSON
reached model inputs and traces; fixes were a follower-reuse governance gate, approvals returning 409
without an interrupt, 28/30 redaction gaps closed, hard/soft injection screening, ineligible incidents
skipping all model layers, a faithfulness backstop, security headers, bounded decision input, and a red-team
corpus and runner. 1,941 unit tests passed in random order. Compose: datastores bound to loopback,
admin tools behind a profile, log rotation, pinned images. Not done: live approve/reject loop on that
system, forced-crash test, CI evaluation gate, and several lower-severity findings listed in the audit.

## 6. Earlier retrieval, caching and HITL work (Sept-Oct 2026, merged into the team repo)

- Query rewriting that keeps complete negation/code/version anchors within a 600-character budget;
  reranker order preserved through article bundling; article-level MMR diversity selection (opt-in,
  measured: hybrid primary recall 95.7% -> 100% clean; MiniLM focused recall regressed, so default off).
- Semantic cache integration: governed ServiceNow read before admission; every follower runs its own
  gates, critic, approval and write; waiters are durable queued rows; session advisory locks stop duplicate
  worker delivery; migration 0005. Live checks: leader + follower complete with one approval each;
  Langfuse showed one original trace per execution, including resumed ServiceNow writes.
- Human-in-the-loop: a real LangGraph interrupt/resume with approval audit and crash recovery; a rejected
  attempt stays failed; an empty approval is rejected with 409; decisions come from the token, not the body.
- 12 incident bugs fixed (BUG-001..012) with regression tests.

## 7. Open items

- Per-engineer identity for operator routes (a shared operator client is used).
- CI evaluation gate and image build, and a forced-crash test, were never built.
- Remediation beyond account actions (runbooks, standard changes) is designed, not built.
