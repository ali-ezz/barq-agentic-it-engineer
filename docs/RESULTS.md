# BARQ on Ali's PDI — test results, 2026-10-04

Everything below ran live on the PDI `dev000001` against our own backend (Mac + tunnel),
on the final copy (`code`, branch `pdi`, commit `36793ad`). Raw output: `evidence/pdi-live-runs/ev6/`.

| Suite | What it checks | Result |
|---|---|---|
| Core | solve a ticket, hand a fix to engineers, P1 waits then approved, P1 rejected, attack blocked, no caller, locked ticket untouched | 7/7 |
| Triage | attack goes to a person, burst = likely outage, P1 for one user re-assessed, repeat needs approval | 4/4 |
| Conversation | agent asks then continues, engineer takes over and hands back, caller reopens, approve on the page, take over a waiting ticket | 5/5 |
| Permissions | caller / engineer / approver / admin see and change only what they should | 12/12 |
| Engineers' page | BARQ AI view, card, right buttons for each role and state | 8/8 |
| Users' page | chat, ticket created as the caller, agent answer visible, other people's tickets refused | 10/10 |
| 22-case mix | every KB article, personal data, Arabic, injection, unknown problem, wrong category, long logs, page flows, two callers, speed | 22/22 |
| Real browser (Chrome) | page opens, working banner, answer without Refresh (10 s), confirm closes, chat, phone size, engineer card | 18/18 |

Unit tests: 2,122 passed. Slowest ticket in the 22-case burst: 52 s; alone: 10–22 s.
AI cost of all testing today: about $4.70 of the $10 daily budget.

## Fixed on the way (in the copy / on the PDI only)

1. Search models kept across rebuilds (a rebuild made the first ticket time out).
2. PDI: the incident table refused writes from the app (conversation rule, page) — allowed.
3. PDI: app permissions requested at run time allowed (`tools/allow_privs.py`).
4. PDI: old app build (16 Sep) re-sent rejected tickets to the AI — current app installed.
5. A waiting ticket is routed and the caller told before it can be approved.
6. "My account is locked" now goes to an engineer instead of self-service steps.
7. A leader whose ticket closed releases the similar tickets waiting on it at once.
8. Users' page no longer says "an engineer is working on it" while the AI posts its fix.
9. Worker slots 3 -> 4 (the Mac has the memory).

## Running it

- Start: `code/pdi.sh up -d`, then `cloudflared tunnel --url http://127.0.0.1:18000`;
  if the tunnel link changed: `python tools/setup_pdi.py <link>`.
- Team updates: taken automatically at 09:00 and 21:00 (a scheduled task), only if
  every check passes; log in `sync.log`.


---

# The agentic engineer — results, 2026-10-04 evening (copy commit `380da1b`, raw output `evidence/pdi-live-runs/ev7/`)

| Check | Result |
|---|---|
| Scenario book (16 real situations: true / false lock, someone else's account, admin rights, injection, password seen, VPN, Outlook, hardware, vague, Arabic, talk to a person, cancel, still broken, engineer instruction, duplicate ticket) | all 16 passed (last full run 15/16; the one miss — invented deep fix — fixed and re-run green) |
| Reply quality (second model grades every reply: natural, correct, safe, language) | 4–5 / 5 on every reply, all safe |
| Real-browser walk (chat, live line, typing answer, engineer card, take over / hand back with instruction, live card, caller confirms, closes) | 21 / 21 |
| Unit tests | 2,144 passed |
| Speed per agent turn | about 15–45 s (was 25–80 s; the live status line no longer blocks the agent) |
| Tracing | every turn in Langfuse project "chatbot only", linked from the card |
