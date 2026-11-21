"""Add one field ACL (incident.hold_reason write for integration_writer while not locked)
through an uploaded update set, then preview and commit it. Setup only (admin session)."""
import json, time, urllib.request, uuid
from xml.sax.saxutils import escape
from snsession import Session
from sn import BASE, get

SCOPE = "51a63bbf738bc7502aedfed25ab8b789"
ROLE = "105563ec471f4310c148497f316d438c"
PKG = (f'<sys_package display_value="AI Incident Orchestrator" source="x_2215032_ai_inc_0">{SCOPE}</sys_package>'
       f'<sys_policy/><sys_scope display_value="AI Incident Orchestrator">{SCOPE}</sys_scope>')
COND = "x_2215032_ai_inc_0_ai_human_lock=false^EQ"
name = "BARQ agentic 2026-10-03 - agent hold_reason ACL"
if get("sys_remote_update_set", f"name={name}", "sys_id", 1):
    raise SystemExit("already uploaded: " + name)
rus = uuid.uuid4().hex
acl = uuid.uuid4().hex
link = uuid.uuid4().hex
nm = "incident.hold_reason"
desc = escape("Allow integration_writer (BARQ AI Agent) to write hold_reason (Awaiting Caller) on an incident that is not human-locked (agent asks the caller, 2026-10-03)")
acl_xml = (f'<?xml version="1.0" encoding="UTF-8"?><record_update table="sys_security_acl"><sys_security_acl action="INSERT_OR_UPDATE"><active>true</active><admin_overrides>true</admin_overrides><advanced>false</advanced><applies_to/><condition>{COND}</condition><controlled_by_refs/><decision_type>allow</decision_type><description>{desc}</description><local_or_existing>Existing</local_or_existing><name>{nm}</name><operation display_value="write">write</operation><script/><security_attribute/><sys_class_name>sys_security_acl</sys_class_name><sys_id>{acl}</sys_id><sys_name>{nm}</sys_name>{PKG}<sys_update_name>sys_security_acl_{acl}</sys_update_name><type display_value="record">record</type></sys_security_acl></record_update>')
link_xml = (f'<?xml version="1.0" encoding="UTF-8"?><record_update table="sys_security_acl_role"><sys_security_acl_role action="INSERT_OR_UPDATE"><sys_class_name>sys_security_acl_role</sys_class_name><sys_id>{link}</sys_id><sys_name>{nm}.x_2215032_ai_inc_0.integration_writer</sys_name>{PKG}<sys_security_acl display_value="{nm}">{acl}</sys_security_acl><sys_update_name>sys_security_acl_role_{link}</sys_update_name><sys_user_role display_value="x_2215032_ai_inc_0.integration_writer" name="x_2215032_ai_inc_0.integration_writer">{ROLE}</sys_user_role></sys_security_acl_role></record_update>')
updates = [(f"sys_security_acl_{acl}", "Access Control", nm, acl_xml),
           (f"sys_security_acl_role_{link}", "Access Roles", f"{nm}.x_2215032_ai_inc_0.integration_writer", link_xml)]
parts = ['<?xml version="1.0" encoding="UTF-8"?><unload unload_date="2026-10-03 07:30:00">',
         f'<sys_remote_update_set action="INSERT_OR_UPDATE"><application display_value="AI Incident Orchestrator">{SCOPE}</application><application_name>AI Incident Orchestrator</application_name><application_scope>x_2215032_ai_inc_0</application_scope><collisions/><commit_date/><deleted/><description>{escape("Field-level write ACL so BARQ AI Agent can put an incident On Hold - Awaiting Caller, only while ai_human_lock=false.")}</description><inserted/><name>{escape(name)}</name><origin_sys_id/><parent display_value=""/><release_date/><remote_base_update_set display_value=""/><remote_parent_id/><remote_sys_id>{uuid.uuid4().hex}</remote_sys_id><state>loaded</state><summary/><sys_class_name>sys_remote_update_set</sys_class_name><sys_id>{rus}</sys_id><update_set display_value=""/><update_source display_value=""/><updated/></sys_remote_update_set>']
for upd_name, typ, target, payload in updates:
    parts.append(f'<sys_update_xml action="INSERT_OR_UPDATE"><action>INSERT_OR_UPDATE</action><application display_value="AI Incident Orchestrator">{SCOPE}</application><category>customer</category><comments/><name>{upd_name}</name><payload>{escape(payload)}</payload><payload_hash/><remote_update_set display_value="{escape(name)}">{rus}</remote_update_set><replace_on_upgrade>false</replace_on_upgrade><sys_id>{uuid.uuid4().hex}</sys_id><table/><target_name>{escape(target)}</target_name><type>{typ}</type><update_domain>global</update_domain><update_guid>{uuid.uuid4().hex}</update_guid><update_set display_value=""/><view/></sys_update_xml>')
parts.append("</unload>")
xml = "".join(parts)
open("barq_agent_hold_reason_acl.xml", "w").write(xml)
s = Session()
boundary = "----barq" + uuid.uuid4().hex
def fld(k, v): return f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'
body = (fld("sysparm_ck", s.ck) + fld("sysparm_referring_url", "sys_remote_update_set_list.do") + fld("sysparm_target", "sys_remote_update_set")
        + f'--{boundary}\r\nContent-Disposition: form-data; name="attachFile"; filename="barq_agent_hold_reason_acl.xml"\r\nContent-Type: text/xml\r\n\r\n').encode() + xml.encode() + f"\r\n--{boundary}--\r\n".encode()
req = urllib.request.Request(f"{BASE}/sys_upload.do", data=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}", "X-UserToken": s.ck})
print("upload", s.op.open(req, timeout=120).status)
print("remote set", get("sys_remote_update_set", f"sys_id={rus}", "name,state", 1))
print("preview", s.ajax("UpdateSetPreviewAjax", sysparm_ajax_processor_function="preview", sysparm_ajax_processor_sys_id=rus)[:80])
for _ in range(30):
    st = get("sys_remote_update_set", f"sys_id={rus}", "state", 1)[0]["state"]
    if st in ("previewed",): break
    time.sleep(3)
problems = get("sys_update_preview_problem", f"remote_update_set={rus}", "type,description", 20)
print("state", st, "problems", problems)
if st == "previewed" and not problems:
    print("commit", s.ajax("UpdateSetCommitAjax", sysparm_type="commitRemoteUpdateSet", sysparm_remote_updateset_sys_id=rus)[:80])
    for _ in range(30):
        st = get("sys_remote_update_set", f"sys_id={rus}", "state", 1)[0]["state"]
        if st == "committed": break
        time.sleep(3)
    print("final", st)
    print(get("sys_security_acl", "name=incident.hold_reason^operation=write", "sys_id,name,condition,active", 10, "true"))
json.dump({"remote_update_set": rus, "acl": acl, "role_link": link}, open("acl_hold_reason_plan.json", "w"))
