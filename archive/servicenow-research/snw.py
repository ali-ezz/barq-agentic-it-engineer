"""Write helper for dev407364 setup (admin login, setup only). Every write is appended to a
manifest so it can be reverted (deactivate / restore previous values)."""
import json, urllib.request, urllib.parse, datetime
from sn import AUTH, BASE, get
MANIFEST="change_manifest.jsonl"
def _req(method, path, body=None):
    data=json.dumps(body).encode() if body is not None else None
    r=urllib.request.Request(f"{BASE}{path}", data=data, method=method,
        headers={"Authorization":AUTH,"Accept":"application/json","Content-Type":"application/json"})
    try:
        return json.load(urllib.request.urlopen(r,timeout=60)).get("result")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{method} {path} -> {e.code}: {e.read()[:400]!r}")
def _log(entry):
    entry["at"]=datetime.datetime.utcnow().isoformat()+"Z"
    open(MANIFEST,"a").write(json.dumps(entry)+"\n")
def create(table, fields):
    res=_req("POST", f"/api/now/table/{table}?sysparm_exclude_reference_link=true", fields)
    _log({"op":"create","table":table,"sys_id":res["sys_id"],"fields":{k:v for k,v in fields.items() if k not in ("script","html")}})
    return res
def update(table, sys_id, fields):
    before=_req("GET", f"/api/now/table/{table}/{sys_id}?sysparm_fields={','.join(fields)}&sysparm_exclude_reference_link=true")
    res=_req("PATCH", f"/api/now/table/{table}/{sys_id}?sysparm_exclude_reference_link=true", fields)
    _log({"op":"update","table":table,"sys_id":sys_id,"before":before,"after":{k:(v if k not in ("script","html") else "<code>") for k,v in fields.items()}})
    return res
