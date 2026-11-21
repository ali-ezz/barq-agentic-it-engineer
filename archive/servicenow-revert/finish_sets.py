import sys, urllib.parse, json
sys.argv=["x"]
exec(open("tmp/revert/revert_servicenow.py").read().split("rows = [json.loads")[0])
q=urllib.parse.quote("nameSTARTSWITHBARQ agentic 2026-10-03")
for table in ("sys_update_set","sys_remote_update_set"):
    code, sets = call("GET", f"/api/now/table/{table}?sysparm_query={q}&sysparm_fields=sys_id,name,state")
    for s in sets or []:
        c,_=call("DELETE", f"/api/now/table/{table}/{s['sys_id']}"); print(table, s["name"], s.get("state"), c)
for p in PREFS:
    print("pref", call("GET", f"/api/now/table/sys_user_preference/{p}?sysparm_fields=value")[1])
