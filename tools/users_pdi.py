"""Test users, Virtual Agent off, scope privileges allowed, KB publisher password (Ali's PDI only)."""
import json, secrets, sys
from pathlib import Path
from sn import get
from setup_pdi_call import call

def user(name, first, last, roles):
    rows = get("sys_user", f"user_name={name}", "sys_id", 1)
    uid = rows[0]["sys_id"] if rows else call("POST", "/api/now/table/sys_user",
        {"user_name": name, "first_name": first, "last_name": last, "email": f"{name}@example.com", "active": "true"})[1]["sys_id"]
    for role in roles:
        rid = get("sys_user_role", f"name={role}", "sys_id", 1)[0]["sys_id"]
        if not get("sys_user_has_role", f"user={uid}^role={rid}", "sys_id", 1):
            print("  grant", name, role, call("POST", "/api/now/table/sys_user_has_role", {"user": uid, "role": rid})[0])
    print("user", name, uid)

user("barq.approver", "BARQ", "Approver", ["itil", "x_2215032_ai_inc_0.operator"])
user("barq.admin", "BARQ", "Admin", ["x_2215032_ai_inc_0.admin"])
for c in get("sp_agent_chat_config", "active=true", "sys_id", 20):
    print("VA off", call("PATCH", f"/api/now/table/sp_agent_chat_config/{c['sys_id']}", {"active": "false"})[0])
for p in get("sys_scope_privilege", "source_scope=51a63bbf738bc7502aedfed25ab8b789^status!=allowed", "sys_id,target_name", 50):
    print("allow", p["target_name"], call("PATCH", f"/api/now/table/sys_scope_privilege/{p['sys_id']}", {"status": "allowed"})[0])
pw = secrets.token_urlsafe(18) + "aA1!"
kb = get("sys_user", "user_name=kb_publisher", "sys_id", 1)[0]["sys_id"]
print("kb_publisher password", call("PATCH", f"/api/now/table/sys_user/{kb}?sysparm_input_display_value=true", {"user_password": pw, "password_needs_reset": "false"})[0])
env = Path(__file__).resolve().parents[1] / "barq/.env.pdi"
text = env.read_text().replace("SERVICENOW_KB_PASSWORD=\n", f"SERVICENOW_KB_PASSWORD={pw}\n")
env.write_text(text)
print("kb roles", [r["role.name"] for r in get("sys_user_has_role", f"user={kb}", "role.name", 20)])
# The agent's display name, as on the shared instance: "BARQ AI Agent".
print("agent name", call("PATCH", "/api/now/table/sys_user/b105f832731b4b102aedfed25ab8b7f3",
                         {"first_name": "BARQ AI", "last_name": "Agent"})[0])
