# BARQ on your PDI — the agentic IT engineer (plan, 2026-10-04)

Goal for Tuesday 2026-10-06: an agent that works like a real IT engineer — it talks like a
person, investigates the facts, checks the story, spots attacks, does small safe fixes itself,
closes the ticket, and gives engineers the full picture of how it worked. Three parts must be
excellent: **the user's screen, the engineer's screen, and the agent itself.**

Isolated from the team: our copy `PDI/barq`, your PDI `dev434590`, your Langfuse project
"chatbot only", your Google AI Studio key. Nothing touches the team repo or shared systems.

---

## 1. The agent (how it works)

Today it follows one fixed path (classify → search → write a fix → check → act). It becomes a
**working loop**, the way an engineer works:

```
 listen  →  investigate  →  compare story vs facts  →  decide  →  act  →  check result
   ↑                                                                          │
   └──────────── ask the caller / try the next option / hand over ◄───────────┘
```

**Its toolbox**

| Kind | Tools | Who |
|---|---|---|
| Look (read-only) | account status (locked, active, password must change), sign-in history (successes, failures, from where), groups and roles, the person's recent tickets, similar tickets from others in the last hour (outage?), knowledge articles | agent alone |
| Talk | ask a question, explain, confirm "did that work?", close with a summary | agent alone |
| Small fixes (caller's OWN account, each with an undo) | unlock account; set "must change password at next sign-in" | agent alone, after its own check |
| Hand over | assign to the right team with the full investigation report; security alert | agent alone |

**Rules enforced in code (the AI cannot talk its way past them)**
- Acts only on the caller's own account. Anything about another person → engineer.
- Never grants access or roles, never deletes, never changes more than one account.
- Suspicion (someone else's account, admin rights, pressure, odd sign-ins, attack text) → no
  action, polite reply, security alert to engineers, ticket marked so the agent can't be argued with.
- Before any fix a second AI reviews the plan; after it, the agent re-reads the account to
  confirm it worked; if not, it undoes and hands over.
- At most 3 questions to the caller, at most ~12 steps per turn, then it hands over.
- Personal-data hiding and attack screening stay on everything.
- Outages (P1): the agent investigates and alerts engineers immediately; no fix by itself.
- No approval waiting any more: approvals are replaced by these rules + the second-AI check.

**Model**: Gemini 3.5 Flash on your own key (free tier; Sprints key kept as a fallback).
**Tracing**: every step, tool call and decision visible in Langfuse ("chatbot only").

## 2. The user's screen (BARQ AI page, `/esc?id=barq_ai`)

A chat-first assistant, like talking to a helpful colleague:
- One conversation per problem; the agent answers in plain language (English or Arabic),
  asks short follow-up questions, shows what it is doing ("Checking your account…"
  → "Your account was locked after 5 wrong passwords. I've unlocked it.").
- Clear status chip on each ticket: Looking into it · Waiting for you · Fixed – please confirm
  · With an engineer · Closed.
- Buttons where they help: "It works, close it" · "Still not working" · "Talk to a person".
- Live: answers appear by themselves; works on a phone; clean, modern look.

## 3. The engineer's screen (BARQ AI view on the incident)

An **investigation report** an engineer would trust:
- **Summary**: what the caller said · what the agent found · conclusion + confidence.
- **Facts checked**: each check with its result and time (e.g. "Account locked at 14:02 after
  5 failed sign-ins from 10.0.0.5").
- **Red flags** (if any) and why.
- **What it did** and the result, each action with **Undo**.
- **Recommendation** for the engineer, when it handed over.
- **Timeline**: every step in order (think → check → act → verify), with a link to the
  Langfuse trace.
- **Take over** at any time (the agent stops and stays out).

## 4. How we test it (behaviour, not just code)

A **scenario book**: ~25 situations written as a good engineer would expect them —
what the agent must check, what it must decide, what it must say, what it must never do.
Examples: true lock · false lock claim · lock for someone else · admin request · VPN with an
article · unknown problem · angry caller · Arabic · attack text · outage burst · caller says
"still broken" · caller goes silent.
Each run is scored automatically (actions and facts exactly; wording by a second AI for
clarity, correctness, kindness), saved with history, and we read the results together and
improve. The existing 8 live suites and 2,122 unit tests are kept and updated.

## 5. Steps (each ends with something you can test)

| # | Step | You can test |
|---|---|---|
| 1 | Groundwork: backup point, Langfuse on, own Gemini key, check PDI password/MFA plugins, test users (locked, failed sign-ins, normal) | traces appear in Langfuse |
| 2 | Investigation tools (read-only) + PDI read access for the agent's account | the agent finds the real facts |
| 3 | The working loop (investigate → decide → act → check), rules in code, second-AI check | true vs false "locked" story |
| 4 | Small fixes with undo (unlock, must-change-password) | real unlock end to end |
| 5 | Suspicion + security alert | "unlock my colleague", admin request |
| 6 | Natural conversation + confirm + close with summary | full chat in English and Arabic |
| 7 | User screen redesign | on laptop and phone |
| 8 | Engineer screen: investigation report, timeline, Undo, Take over; approvals removed | engineer view |
| 9 | Scenario book + scoring; full run; fixes | the score sheet |
| 10 | Short demo guide | — |

Timing: steps 1–6 Sunday night–Monday, 7–9 Monday, Tuesday morning you test and I fix.
After Tuesday (not rushed now): practice lab for "restart a service", catalog orders,
password-reset link flow, bigger search models.

## 6. Changes on your PDI (all recorded in PDI/manifest.jsonl, admin used for setup only)
- Read access for the agent's account to user status, sign-in events, group membership.
- Write access for the agent's account to exactly two user fields (locked out, must change
  password), only through the new tools.
- New/updated: users' page widget, engineer report on the BARQ AI view, approval buttons removed.
- A few labelled test users.
