"""Ticket list layout for the BARQ AI view (incident list, view barq_engineer). PDI only.

Columns: number, caller, title, state, team, live activity, BARQ AI summary, updated.
Logged in manifest.jsonl. Only touches the list layout of our own view."""
import base64, json, urllib.request
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from sn import AUTH, BASE, get

VIEW = "8c35205073fb87d02aedfed25ab8b7ca"  # sys_ui_view barq_engineer
P = "x_2215032_ai_inc_0_ai_"
COLUMNS = ["number", "caller_id", "short_description", "state", "assignment_group",
           P + "activity", P + "suggestion", "sys_updated_on"]
MANIFEST = str(__import__("pathlib").Path(__file__).resolve().parent / "servicenow_change_manifest.jsonl")


def call(method, path, body=None):
    req = urllib.request.Request(f"{BASE}{path}", method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": AUTH, "Accept": "application/json", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
        return json.loads(raw)["result"] if raw else None


def log(entry):
    with open(MANIFEST, "a") as f:
        f.write(json.dumps(entry) + "\n")


existing = get("sys_ui_list", f"name=incident^view={VIEW}^parentISEMPTY", "sys_id")
if existing:
    list_id = existing[0]["sys_id"]
    for el in get("sys_ui_list_element", f"list_id={list_id}", "sys_id"):
        call("DELETE", f"/api/now/table/sys_ui_list_element/{el['sys_id']}")
else:
    list_id = call("POST", "/api/now/table/sys_ui_list", {"name": "incident", "view": VIEW, "sys_scope": "global"})["sys_id"]
    log({"op": "create", "table": "sys_ui_list", "sys_id": list_id, "why": "demo: BARQ AI ticket list layout"})
for pos, col in enumerate(COLUMNS):
    el = call("POST", "/api/now/table/sys_ui_list_element", {"list_id": list_id, "element": col, "position": str(pos)})
    log({"op": "create", "table": "sys_ui_list_element", "sys_id": el["sys_id"], "why": f"demo list column {col}"})
print(list_id, [r["element"] for r in get("sys_ui_list_element", f"list_id={list_id}^ORDERBYposition", "element")])
