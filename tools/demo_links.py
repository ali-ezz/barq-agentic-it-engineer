"""Print the 3 links (user page, engineer page, Langfuse) for every test ticket from INC >= argv[1]."""
import sys, json
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from sn import get, BASE
LF = "https://cloud.langfuse.com/project/cmutzvchb17w9ad0cqv6f11yb"
P = "x_2215032_ai_inc_0_ai_"
rows = get("incident", f"caller_id.user_nameSTARTSWITHbarq.^number>={sys.argv[1]}^ORDERBYnumber",
           f"sys_id,number,caller_id.name,caller_id.user_name,state,{P}report", 100, "false")
names = {r["number"]: r for r in get("incident", f"caller_id.user_nameSTARTSWITHbarq.^number>={sys.argv[1]}", "number,caller_id,state", 100, "true")}
print("| Ticket | Person (impersonate) | Result | User page | Engineer page | Langfuse |")
print("|---|---|---|---|---|---|")
for r in rows:
    rep = json.loads(r.get(f"{P}report") or "{}")
    d = names[r["number"]]
    print(f"| {r['number']} | {d['caller_id']} (`{r['caller_id.user_name']}`) | {rep.get('outcome') or d['state']} "
          f"| [chat]({BASE}/esc?id=barq_ai) | [card]({BASE}/incident.do?sys_id={r['sys_id']}) "
          f"| [session]({LF}/sessions/{r['number']}) |")
