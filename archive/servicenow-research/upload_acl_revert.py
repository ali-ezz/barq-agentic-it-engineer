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

name = "BARQ revert 2026-10-03 - remove agent field ACLs"
ACLS = ["552a9efa818842039db1d1ad5b261671","1cda457885fb44fbb16413fe2486db97","818431ed1877471e808d368ae5dd2888","0b8ea8d6283f4eb3ad0830cd8855cefa","4528565a5bbf414493257e145133ec71","6653c2efc15a4de99d66a436329c7b75","02a09dac906e448cb42593b922c78bab"]
rus = uuid.uuid4().hex
updates = []
for acl in ACLS:
    rec = get("sys_security_acl", f"sys_id={acl}", "name", 1)
    nm = rec[0]["name"] if rec else "acl"
    for link in get("sys_security_acl_role", f"sys_security_acl={acl}", "sys_id", 20):
        lid = link["sys_id"]
        p = (f'<?xml version="1.0" encoding="UTF-8"?><record_update table="sys_security_acl_role"><sys_security_acl_role action="DELETE"><sys_class_name>sys_security_acl_role</sys_class_name><sys_id>{lid}</sys_id>{PKG}<sys_update_name>sys_security_acl_role_{lid}</sys_update_name></sys_security_acl_role></record_update>')
        updates.append((f"sys_security_acl_role_{lid}", "Access Roles", nm, p))
    p = (f'<?xml version="1.0" encoding="UTF-8"?><record_update table="sys_security_acl"><sys_security_acl action="DELETE"><name>{nm}</name><sys_class_name>sys_security_acl</sys_class_name><sys_id>{acl}</sys_id>{PKG}<sys_update_name>sys_security_acl_{acl}</sys_update_name></sys_security_acl></record_update>')
    updates.append((f"sys_security_acl_{acl}", "Access Control", nm, p))
print(len(updates), "deletes")
parts = ['<?xml version="1.0" encoding="UTF-8"?><unload unload_date="2026-10-03 19:30:00">',
         f'<sys_remote_update_set action="INSERT_OR_UPDATE"><application display_value="AI Incident Orchestrator">{SCOPE}</application><application_name>AI Incident Orchestrator</application_name><application_scope>x_2215032_ai_inc_0</application_scope><collisions/><commit_date/><deleted/><description>Revert: remove the BARQ agent field ACLs added 2026-10-03.</description><inserted/><name>{escape(name)}</name><origin_sys_id/><parent display_value=""/><release_date/><remote_base_update_set display_value=""/><remote_parent_id/><remote_sys_id>{uuid.uuid4().hex}</remote_sys_id><state>loaded</state><summary/><sys_class_name>sys_remote_update_set</sys_class_name><sys_id>{rus}</sys_id><update_set display_value=""/><update_source display_value=""/><updated/></sys_remote_update_set>']
for upd_name, typ, target, payload in updates:
    parts.append(f'<sys_update_xml action="INSERT_OR_UPDATE"><action>DELETE</action><application display_value="AI Incident Orchestrator">{SCOPE}</application><category>customer</category><comments/><name>{upd_name}</name><payload>{escape(payload)}</payload><payload_hash/><remote_update_set display_value="{escape(name)}">{rus}</remote_update_set><replace_on_upgrade>false</replace_on_upgrade><sys_id>{uuid.uuid4().hex}</sys_id><table/><target_name>{escape(target)}</target_name><type>{typ}</type><update_domain>global</update_domain><update_guid>{uuid.uuid4().hex}</update_guid><update_set display_value=""/><view/></sys_update_xml>')
parts.append("</unload>")
xml = "".join(parts)
fname = "barq_revert_acls.xml"
open(fname, "w").write(xml)
s = Session()
boundary = "----barq" + uuid.uuid4().hex
def fld(k, v): return f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'
body = (fld("sysparm_ck", s.ck) + fld("sysparm_referring_url", "sys_remote_update_set_list.do") + fld("sysparm_target", "sys_remote_update_set")
        + f'--{boundary}\r\nContent-Disposition: form-data; name="attachFile"; filename="barq_revert_acls.xml"\r\nContent-Type: text/xml\r\n\r\n').encode() + xml.encode() + f"\r\n--{boundary}--\r\n".encode()
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
    print("left", [a for a in ACLS if get("sys_security_acl", f"sys_id={a}", "sys_id", 1)])
json.dump({"remote_update_set": rus}, open("acl_revert_plan.json", "w"))
