import sys, json
sys.argv=["x"]
src=open("tmp/revert/revert_servicenow.py").read()
exec(src.split("print(f\"plan:")[0])
still=[k for k in deletes if exists(*k)]
print("created records still present:", still)
bad=[]
for k in restores:
    want=before.get(k,{})
    code,cur=call("GET", f"/api/now/table/{k[0]}/{k[1]}?sysparm_fields={','.join(want)}")
    if code==404: print("  (gone)",k); continue
    diff={f:(cur.get(f),v) for f,v in want.items() if f!="xml" and str(plain(cur.get(f)))!=str(v)}
    if diff: bad.append((k,diff))
print("restores not matching:", bad)
print("ACLs still present:", [a for a in acls if exists("sys_security_acl",a)])
