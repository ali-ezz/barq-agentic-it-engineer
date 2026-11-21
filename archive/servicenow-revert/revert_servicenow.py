"""Undo every BARQ 2026-10-03 change on dev407364 from the change manifest.

Rules (per record, keyed by table + sys_id, in manifest order):
  first op 'create' -> the record did not exist this morning: delete it.
  first op 'update' -> restore each field to the 'before' value of its first update.
  first op 'delete' -> only our own records / history were deleted: nothing to restore.
Plus the field ACLs committed through update sets (deleted) and our update sets.
Admin login for setup only. Usage: python revert_servicenow.py [--apply]
"""

import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

M = "tmp/backups/2026-10-03-pre-agentic/servicenow/change_manifest.jsonl"
URL = os.environ["SN_INSTANCE_URL"].rstrip("/")
AUTH = "Basic " + base64.b64encode(
    f"{os.environ['SN_ADMIN_USER']}:{os.environ['SN_ADMIN_PASS']}".encode()
).decode()
APPLY = "--apply" in sys.argv
BARQ_SET = "62bce4c8477fc310c148497f316d4364"
PREFS = ("2ddfbfef4793cb50c148497f316d4308", "4adf33e3471b4b50c148497f316d435f")
SKIP_TABLES = {"sys_update_version", "sys_update_xml", "sys_user_preference", "sys_update_set", "incident"}


def call(method, path, body=None):
    req = urllib.request.Request(
        URL + path,
        data=json.dumps(body).encode() if body is not None else None,
        method=method,
        headers={"Authorization": AUTH, "Accept": "application/json",
                 "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read()
            return r.status, (json.loads(raw).get("result") if raw else None)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:300]


def exists(table, sys_id):
    code, _ = call("GET", f"/api/now/table/{table}/{sys_id}?sysparm_fields=sys_id")
    return code == 200


def plain(value):
    return value.get("value", "") if isinstance(value, dict) else value


rows = [json.loads(line) for line in open(M)]
order, first, before = [], {}, {}
acls = set()
for r in rows:
    if r.get("op") == "acls_created_actual_ids":
        acls.update(r["acls"].values())
    if r.get("op") == "commit_update_set" and r.get("acls"):
        acls.update(a[1] for a in r["acls"])
    t, s = r.get("table"), r.get("sys_id")
    if not t or not s:
        continue
    key = (t, s)
    if key not in first:
        first[key] = r["op"]
        order.append(key)
    if r["op"] == "update" and first[key] == "update":
        for f, v in (r.get("before") or {}).items():
            before.setdefault(key, {}).setdefault(f, plain(v))

# hold_reason ACL (committed via update set; recorded by name only)
code, found = call("GET", "/api/now/table/sys_security_acl?sysparm_query=name=incident.hold_reason"
                   "^conditionLIKEai_human_lock&sysparm_fields=sys_id,name")
if code == 200:
    acls.update(x["sys_id"] for x in found)

deletes = [k for k in order if first[k] == "create" and k[0] not in SKIP_TABLES]
restores = [k for k in order if first[k] == "update" and k[0] not in SKIP_TABLES]
print(f"plan: delete {len(deletes)} created records, restore {len(restores)} changed records, "
      f"delete {len(acls)} ACLs; then update sets; then admin prefs -> Default. apply={APPLY}")
for k in deletes:
    print("  delete", k)
for k in restores:
    print("  restore", k, json.dumps(before.get(k, {}))[:160])
if not APPLY:
    sys.exit(0)

log = []
# capture the revert in our own update set (deleted at the end), not in Default
for p in PREFS:
    call("PATCH", f"/api/now/table/sys_user_preference/{p}", {"value": BARQ_SET})
for k in restores:
    code, res = call("PATCH", f"/api/now/table/{k[0]}/{k[1]}", before.get(k, {}))
    log.append(("restore", k, code))
for k in reversed(deletes):
    if exists(*k):
        code, res = call("DELETE", f"/api/now/table/{k[0]}/{k[1]}")
        log.append(("delete", k, code, res if code >= 300 else ""))
    else:
        log.append(("gone", k, 404))
for a in acls:
    if exists("sys_security_acl", a):
        code, res = call("DELETE", f"/api/now/table/sys_security_acl/{a}")
        if code >= 300:  # deleting ACLs may need elevation: deactivate instead
            code2, _ = call("PATCH", f"/api/now/table/sys_security_acl/{a}", {"active": "false"})
            log.append(("acl_deactivated", a, code, code2))
        else:
            log.append(("acl_deleted", a, code))
# our update sets: the in-progress BARQ set and the local sets made by committing ours
for p in PREFS:
    call("PATCH", f"/api/now/table/sys_user_preference/{p}",
         {"value": "2cb1e9394717cb10c148497f316d43de"})
code, sets = call("GET", "/api/now/table/sys_update_set?sysparm_query=nameSTARTSWITHBARQ agentic 2026-10-03"
                  "&sysparm_fields=sys_id,name,state")
for s in sets if code == 200 else []:
    c, _ = call("DELETE", f"/api/now/table/sys_update_set/{s['sys_id']}")
    log.append(("update_set_deleted", s["name"], c))
code, rsets = call("GET", "/api/now/table/sys_remote_update_set?sysparm_query=nameSTARTSWITHBARQ agentic 2026-10-03"
                   "&sysparm_fields=sys_id,name")
for s in rsets if code == 200 else []:
    c, _ = call("DELETE", f"/api/now/table/sys_remote_update_set/{s['sys_id']}")
    log.append(("remote_set_deleted", s["name"], c))
bad = [x for x in log if isinstance(x[2], int) and x[2] >= 300]
json.dump(log, open("tmp/revert/servicenow_revert_log.json", "w"), indent=1, default=str)
print(f"done: {len(log)} steps, {len(bad)} problems")
for x in bad:
    print("  PROBLEM", x)
