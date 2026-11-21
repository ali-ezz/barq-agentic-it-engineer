"""Leader -> (when resolved) safe follower + P1 follower, against the SHARED deployment as deployed."""
import sys, os, json, time, subprocess, datetime as dt; sys.path.insert(0, os.path.dirname(__file__))
from sn_admin import client, SCOPE, ENV
HOST = ENV["SHARED_BACKEND_HOST"]; TAG = "[AUDIT-2026-10-02]"
TEXT = ("VPN authentication fails after password reset", "Can reach the internet but the VPN client says invalid credentials since I reset my password this morning.")

def create(label, impact, urgency):
    r = client.post("/api/now/table/incident", json={"short_description": f"{TAG} {TEXT[0]}", "description": TEXT[1], "category": "network",
        "impact": impact, "urgency": urgency, f"{SCOPE}ai_enabled": "true", f"{SCOPE}ai_human_lock": "false"}, params={"sysparm_fields": "sys_id,number,priority"})
    res = r.json()["result"]; print(f"{label}: {res['number']} P{res['priority']} created {dt.datetime.now(dt.UTC):%H:%M:%S}Z", flush=True); return res

def db(numbers):
    q = ("select ev.incident_number, e.status, left(coalesce(e.termination_cause,''),34), round(extract(epoch from coalesce(e.ended_at,now())-e.started_at)::numeric,0) "
         "from executions e join events ev on ev.id=e.event_record_id where ev.incident_number in (" + ",".join(f"'{n}'" for n in numbers) + ") order by e.started_at;")
    cmd = f"docker exec barq-postgres sh -c 'psql -U \"$POSTGRES_USER\" -d \"$POSTGRES_DB\" -At -F\" | \" -c \"{q}\"'"
    out = subprocess.run(["ssh", "-i", os.path.expanduser("~/.ssh/barq-ec2"), "-o", "BatchMode=yes", f"ubuntu@{HOST}", cmd], capture_output=True, text=True, timeout=60).stdout
    return [l.split(" | ") for l in out.strip().splitlines() if l]

leader = create("LEADER ", "3", "2")
t0 = time.time()
while time.time() - t0 < 330:
    time.sleep(20); rows = db([leader["number"]])
    print(f"  +{int(time.time()-t0)}s leader:", rows, flush=True)
    if rows and rows[0][1] in ("succeeded", "awaiting_approval", "failed"): break
json.dump({"leader": leader}, open(os.path.join(os.path.dirname(__file__), "fixtures_cache.json"), "w"))
if not rows or rows[0][1] != "succeeded":
    print("leader did not resolve; followers NOT created"); sys.exit(0)
safe = create("SAFE FOLLOWER ", "3", "2")
risky = create("RISKY FOLLOWER (P1)", "1", "1")
json.dump({"leader": leader, "safe": safe, "risky": risky}, open(os.path.join(os.path.dirname(__file__), "fixtures_cache.json"), "w"))
t1 = time.time()
while time.time() - t1 < 240:
    time.sleep(15); rows = db([safe["number"], risky["number"]])
    print(f"  +{int(time.time()-t1)}s followers:", rows, flush=True)
    if len(rows) >= 2 and all(r[1] != "running" and r[1] != "queued" for r in rows): break
