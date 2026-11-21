import sys, os, json, time, datetime as dt; sys.path.insert(0, os.path.dirname(__file__))
from sn_admin import client, SCOPE
from dbq import q
TAG = "[AUDIT-2026-10-02]"
TEXT = ("VPN authentication fails after password reset", "Can reach the internet but the VPN client says invalid credentials since I reset my password this morning.")
def create(label, impact, urgency):
    r = client.post("/api/now/table/incident", json={"short_description": f"{TAG} {TEXT[0]}", "description": TEXT[1], "category": "network", "impact": impact, "urgency": urgency,
        f"{SCOPE}ai_enabled": "true", f"{SCOPE}ai_human_lock": "false"}, params={"sysparm_fields": "sys_id,number,priority"})
    res = r.json()["result"]; print(f"{label}: {res['number']} P{res['priority']} at {dt.datetime.now(dt.UTC):%H:%M:%S}Z", flush=True); return res
def status(nums):
    rows, err = q("select ev.incident_number, e.status, left(coalesce(e.termination_cause,''),30), round(extract(epoch from coalesce(e.ended_at,now())-e.started_at)::numeric,1) from executions e join events ev on ev.id=e.event_record_id where ev.incident_number in (" + ",".join(f"'{n}'" for n in nums) + ") order by 1;")
    return rows
leader = create("LEADER", "3", "2"); t0 = time.time(); rows = []
while time.time() - t0 < 420:
    time.sleep(15); rows = status([leader["number"]]); print(f"  +{int(time.time()-t0)}s", rows, flush=True)
    if rows and rows[0][1] in ("succeeded", "awaiting_approval", "failed"): break
if not rows or rows[0][1] != "succeeded": print("leader not resolved -> stop"); sys.exit(0)
safe = create("SAFE FOLLOWER ", "3", "2"); risky = create("RISKY FOLLOWER", "1", "1")
json.dump({"leader": leader, "safe": safe, "risky": risky}, open(os.path.join(os.path.dirname(__file__), "fixtures_cache.json"), "w"))
t1 = time.time()
while time.time() - t1 < 300:
    time.sleep(10); rows = status([safe["number"], risky["number"]]); print(f"  +{int(time.time()-t1)}s", rows, flush=True)
    if len(rows) == 2 and all(r[1] not in ("running", "queued") for r in rows): break
