# BARQ AI — how to record the 5-minute demo video (Arcade, no voice)

## 1. Get ready (10 minutes before)

1. Docker Desktop open. In Terminal:
   ```
   cd code && ./pdi.sh ps
   ```
   all five lines say "healthy". If not: `./pdi.sh up -d`.
2. Tunnel running (a Terminal window with `cloudflared`). If you restarted the Mac:
   `cloudflared tunnel --url http://127.0.0.1:18000`, then
   `python ../tools/setup_pdi.py <the new https link>`.
3. Make the busy desk (about 4 minutes, prints READY and the links):
   ```
   . ../liveenv.sh && uv run python scripts/live/demo_start.py --out ../ev8/demo.json
   ```
   Copy the "Engineer's desk" link it prints. Run this again before every new take.
4. Chrome: window 1440 x 900, zoom 100 %, bookmarks bar hidden (Cmd+Shift+B), other tabs closed.
   Tabs to open in order:
   - Tab 1: `https://dev434590.service-now.com/esc?id=barq_ai`
   - Tab 2: the Engineer's desk link
   - Tab 3: Langfuse, project "chatbot only" (cloud.langfuse.com) — log in now.
5. In ServiceNow (log in as admin) → your avatar → **Impersonate user** → **Lina Haddad**.

## 2. Record (Arcade extension → Record → this tab)

Arcade makes a picture on every click, so the agent's thinking time vanishes. For the steps
marked VIDEO, switch Arcade to video for that step (moving parts), then back.
After each click, give the page 1–2 s before the next click.

| # | Tab | Do this | Wait for | Caption to add in the editor |
|---|---|---|---|---|
| 1 | 1 | (cover step) | — | BARQ AI — an IT engineer, not a chatbot |
| 2 | 1 | click in the message box | the welcome screen | Employees just write, like to a colleague |
| 3 | 1 VIDEO | type: `I can't sign in this morning, it says my account is locked. I changed my password yesterday.` → Enter | the live lines ("Checking your account…") | It investigates and shows every step |
| 4 | 1 | click the answer bubble | the answer has typed in | Locked after 5 failed sign-ins → unlocked → checked again |
| 5 | 1 | type `Yes, I can sign in now. Thanks!` → Enter | status **Closed** | The caller confirms; the ticket closes |
| 6 | — | avatar → **End impersonation** → Impersonate **Beth Anglin** | — | (delete these steps in the editor) |
| 7 | 2 | open the desk link (refresh) | 15 tickets | A busy desk, worked at the same time |
| 8 | 2 | open **Omar Saleh**'s ticket | the BARQ AI card | It doesn't believe — it checks: not locked, nothing changed |
| 9 | 2 | back → **Karim Adel**'s ticket | card with red flags | Asked for a colleague's account → security, nothing leaked |
| 10 | 2 | back → **Yousef Ali**'s ticket | card | Hidden instructions are ignored |
| 11 | 2 | back → **Layla Youssef**'s ticket → scroll to comments | Arabic answer | Answers in the caller's language |
| 12 | 2 | back → **Ahmed Nabil**'s newer ticket | "Cancelled — duplicate of INC…" | Spots duplicates |
| 13 | 2 | open **Lina**'s ticket (top of list) | card | Engineers see everything it did |
| 14 | 2 | click **Show how BARQ AI worked** | the timeline | Every check and action, in order |
| 15 | 2 | hover **Undo** next to "Unlocked account" (don't click) | — | Every change can be undone |
| 16 | 2 | back → **Mona Fathy**'s ticket → **Take over** | button says **Hand back** | One button: the engineer takes control |
| 17 | 2 VIDEO | type in the box: `Tell her I will keep an eye on her account today and she can reply here if anything looks odd.` → **Hand back** | card shows "working" then the new reply | Engineers tell it what to do in plain words |
| 18 | 2 | back → **Nour Hassan**'s ticket → box: `Save this fix as knowledge.` → send | card shows the saved article | It learns from engineers |
| 19 | 2 | on any card, click **Open the full trace** | Langfuse opens (Tab 3 login) | Every step is traced |
| 20 | 3 | in the trace, click: an `llm` step, the `review` step, a `servicenow` step | the input/output panels | What it thought, the second-AI check, what it changed, how long |
| 21 | 3 | **Sessions** (left menu) → Lina's ticket number | all her turns | One ticket = one conversation |
| 22 | 3 | **Traces** → filter **Tags** = `outcome:security` | the 3 security tickets | Filter by result |
| 23 | — | (end step) | — | 16/16 scenarios · 21/21 browser checks · 2,147 tests |

## 3. Edit in Arcade

- Delete the impersonation steps (6) and any misclicks.
- Add the captions above (Arcade: click a step → "Add text / Callout").
- Steps 3 and 17 are video: trim the waiting parts, or set speed 2x.
- Cover (1) and end (23): Arcade "Chapter"/title slide.
- Aim for ~5:00 total: about 10–15 s per picture step.
- Share → Export → **Video (MP4)**, 1080p.

## 4. If something goes wrong

- A take went wrong: run the demo-start again (step 1.3) and record again.
- Lina's answer did not come within 1 minute: `../tools/trace.sh <ticket number>` shows why.
- The card says "working" for more than 2 minutes: refresh the page.
