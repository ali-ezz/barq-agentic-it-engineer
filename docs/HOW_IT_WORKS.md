# BARQ on your PDI — how it all works, and how we run it without editing anything

## The one rule

**We never edit anything that exists.** Not the team repo, not PR #213, not the shared
ServiceNow, not the shared EC2. We take a **copy** of the code exactly as it is (PR #213 at
`90a4985`) and run it as-is. Everything that is different on your PDI is a **setting**, not code.

## 1. What the project is (5 + 1 parts)

| Part | What it does | Where its code is (read only) |
|---|---|---|
| **ServiceNow app** (on the PDI) | the AI fields on incidents, the buttons (Approve / Reject / Take over / Hand back), the engineers' BARQ AI view, the users' BARQ AI page, the rule that sends "something happened" messages | `servicenow/ai_incident_orchestrator/` (app) and `.../live/` (buttons, rule, page) |
| **API** | receives the message from ServiceNow, checks it, answers "OK" in milliseconds, puts the job in the queue | `src/app/api/` |
| **Queue** (Redis) | holds the jobs | — (standard program) |
| **Worker** (the AI agent) | takes a job and does the thinking: read ticket → privacy + attack checks → classify → urgency → search knowledge → diagnose → write fix → check fix → decide → write back to ServiceNow | `src/agent/` (the steps), `src/app/workers/` (running them) |
| **Database** (PostgreSQL) | remembers every run, every step, approvals, the learning record | `migrations/` (its structure) |
| **Search index** (Qdrant) | the knowledge articles, searchable | `scripts/seed_qdrant*.py`, `data/` |
| + **AI model** | Gemini through the Sprints LiteLLM key | settings only |

## 2. What happens to one ticket

```
Caller opens a ticket on the PDI (or on the BARQ AI page)
   │  ServiceNow rule sends "incident.created INC…"  (no ticket text, just the number)
   ▼
API  ──►  Queue  ──►  Worker
                         1. reads the ticket with the agent's own login (never admin)
                         2. hides personal data, blocks attacks
                         3. works out the problem type and how urgent it is
                         4. searches the knowledge articles
                         5. writes a fix, a second AI checks every step against the articles
                         6. decides: solve it for the caller, ask the caller a question,
                            give it to a team, or wait for an engineer's approval
                         7. writes back to ServiceNow: steps for the caller, the team, notes
   ▼
Caller sees the answer on the page · engineers see the BARQ AI card and buttons
```

## 3. What is different on your PDI — settings only

**Backend settings file `.env`** (git ignores it; never committed):

| Setting | Shared (before) | Your PDI |
|---|---|---|
| `SERVICENOW_INSTANCE_URL` | dev407364 | `https://dev434590.service-now.com` |
| `SERVICENOW_USERNAME` / password / client id+secret | shared agent login | the PDI's own `ai_orchestrator_svc` + OAuth client (already exist, in `.secrets` as `PDI_SERVICENOW_*`) |
| `AGENT_ASSIGNMENT_GROUPS` | shared group ids | your PDI's Network / Software / Hardware / Service Desk group ids |
| `AGENT_SERVICE_ACCOUNT_IDS` | shared ids | your PDI's agent user id |
| `SERVICENOW_KB_ID`, KB publisher login | shared | your PDI's knowledge base |
| `WEBHOOK_AUTH_TOKEN`, operator secret | shared | new values made for us only |
| Database / queue / search passwords | shared EC2 | new, local to us |
| `TRACING_ENABLED` / Langfuse keys | team project | your own project, or off |

**ServiceNow system properties on your PDI** (5 values the installers set):
`ec2_endpoint` (our backend address), `s1_3_event_endpoint` (where tickets are sent),
`operator_client_id`, `operator_client_secret`, `agent_user_name`.

Nothing else changes. The same installers (`scripts/servicenow_apply_*.py`) read the PDI address
and admin login from the environment.

## 4. Where it runs

Your PDI must be able to reach the backend over the internet.

- **Now:** your Mac. Docker runs the 5 programs (`docker compose up -d`, the same file the
  team's server uses). A free Cloudflare tunnel gives your Mac a public secure link.
  Works while the Mac is on.
- **Later (optional):** a small server of your own, same Docker setup, always on.

## 5. The steps, in order

1. Copy the code (PR #213 as it is) into `code/` — a copy, the original is untouched.
2. Write the `.env` with the PDI values above.
3. Start the programs on the Mac; create the empty database; load the knowledge articles.
4. Start the tunnel; note the link.
5. On the PDI: run the installers (admin login for setup only) and set the 5 properties to the link.
6. Test: open a ticket on the PDI, watch the answer arrive; then the full test list.

## 6. What I need from you

- OK to install `cloudflared` (free, from Cloudflare, via Homebrew).
- Wake your PDI at developer.servicenow.com.
- Langfuse: your own free project, or tracing off.
