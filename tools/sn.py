"""Read-only ServiceNow helper for dev000001 (Ali PDI) (admin login, GET only)."""
import os, sys, json, urllib.request, urllib.parse, base64
env={}
for line in open(__import__("os").environ.get("BARQ_ENV_FILE", ".secrets/barq-g1.env")):
    line=line.strip()
    if "=" in line and not line.startswith("#"):
        k,v=line.split("=",1); env[k]=v.strip().strip("'\"")
BASE="https://dev000001.service-now.com"
AUTH="Basic "+base64.b64encode(f"{env['SN_ADMIN_USER']}:{env['SN_ADMIN_PASS']}".encode()).decode()
def get(table, query="", fields="", limit=200, display="false"):
    q=urllib.parse.urlencode({"sysparm_query":query,"sysparm_fields":fields,"sysparm_limit":limit,"sysparm_display_value":display,"sysparm_exclude_reference_link":"true"})
    r=urllib.request.Request(f"{BASE}/api/now/table/{table}?{q}",headers={"Authorization":AUTH,"Accept":"application/json"})
    return json.load(urllib.request.urlopen(r,timeout=60))["result"]
if __name__=="__main__":
    t,q,f=sys.argv[1],sys.argv[2],sys.argv[3]
    lim=int(sys.argv[4]) if len(sys.argv)>4 else 200
    for row in get(t,q,f,lim,"true"): print(" | ".join(str(row.get(x,""))[:110] for x in f.split(",")))
