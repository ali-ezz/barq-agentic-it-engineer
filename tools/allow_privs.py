"""Allow every cross-scope privilege the BARQ app has requested on the PDI (enforcing mode
records each new API the app uses as 'requested' and refuses it until allowed)."""
from sn import get
from setup_pdi_call import call

for p in get("sys_scope_privilege", "source_scope=51a63bbf738bc7502aedfed25ab8b789^status!=allowed", "sys_id,target_name,operation", 50):
    print("allowed", p["operation"], p["target_name"],
          call("PATCH", f"/api/now/table/sys_scope_privilege/{p['sys_id']}", {"status": "allowed"})[0])
