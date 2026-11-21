import sys, json; sys.path.insert(0, __import__("os").path.dirname(__file__))
from sn_admin import client, SCOPE, BASE
print("instance:", BASE.split("//")[1].split(".")[0])
r = client.get("/api/now/table/sys_user", params={"sysparm_query": "user_name=" + client.auth._auth_header.split()[0] if False else "active=true", "sysparm_limit": 1, "sysparm_fields": "user_name"})
print("admin auth / read sys_user:", r.status_code)
r = client.get("/api/now/table/incident", params={"sysparm_query": "number=INC0010233", "sysparm_limit": 1, "sysparm_display_value": "false"})
print("read incident:", r.status_code)
rec = r.json()["result"][0]
keep = {k: (v if not isinstance(v, dict) else v) for k, v in rec.items() if k in ("number","state","priority","impact","urgency","category","subcategory","business_service","cmdb_ci","caller_id","assignment_group","contact_type") or k.startswith(SCOPE)}
print(json.dumps(keep, indent=1, default=str)[:1800])
