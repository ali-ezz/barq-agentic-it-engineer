"""Prepare Ali's PDI (dev434590) for the BARQ copy: event/token addresses -> our tunnel,
approver role, agent field ACLs (uploaded update set), backend properties.
Admin login for setup only. Idempotent. Usage: python setup_pdi.py <tunnel-url>"""
import base64, json, sys, time, urllib.error, urllib.request, uuid
from pathlib import Path
from xml.sax.saxutils import escape

from sn import AUTH, BASE, get
from snsession import Session, background_script

TUNNEL = sys.argv[1].rstrip("/")
ENV = {}
for line in Path(__file__).resolve().parents[1].joinpath("barq/.env.pdi").read_text().splitlines():
    if "=" in line and not line.lstrip().startswith("#"):
        k, v = line.split("=", 1)
        ENV[k.strip()] = v.strip()
SCOPE = "51a63bbf738bc7502aedfed25ab8b789"


def call(method, path, body=None):
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode() if body is not None else None,
                                 method=method, headers={"Authorization": AUTH, "Accept": "application/json",
                                                         "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read()
            return r.status, (json.loads(raw).get("result") if raw else None)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:300]


def prop(name, value, ptype="string"):
    rows = get("sys_properties", f"name={name}", "sys_id", 1)
    if rows:
        code, _ = call("PATCH", f"/api/now/table/sys_properties/{rows[0]['sys_id']}", {"value": value})
    else:
        code, _ = call("POST", "/api/now/table/sys_properties",
                       {"name": name, "value": value, "type": ptype, "sys_scope": SCOPE})
    print("property", name, code)


# 1. Event and token addresses -> our tunnel, our own webhook client
prop("x_2215032_ai_inc_0.s1_3_event_endpoint", f"{TUNNEL}/api/v1/webhook/incident")
prop("x_2215032_ai_inc_0.ec2_endpoint", TUNNEL)
prop("x_2215032_ai_inc_0.operator_client_id", ENV["OPERATOR_CLIENT_ID"])
prop("x_2215032_ai_inc_0.operator_client_secret", ENV["WEBHOOK_AUTH_TOKEN"], "password2")
prop("x_2215032_ai_inc_0.agent_user_name", "ai_orchestrator_svc")
code, _ = call("PATCH", "/api/now/table/oauth_entity/c3758576739b4b102aedfed25ab8b780",
               {"token_url": f"{TUNNEL}/api/v1/oauth/token",
                "client_id": ENV["WEBHOOK_OAUTH_CLIENT_ID"],
                "client_secret": ENV["WEBHOOK_OAUTH_CLIENT_SECRET"]})
print("oauth entity", code)
for cred in get("oauth_credential", "oauth_entity_profile=0b758576739b4b102aedfed25ab8b782", "sys_id", 50):
    print("stale token removed", call("DELETE", f"/api/now/table/oauth_credential/{cred['sys_id']}")[0])

s = Session()
# 2. Approver role (in the app scope)
out = background_script(s, """
var r = new GlideRecord('sys_user_role'); r.addQuery('name', 'x_2215032_ai_inc_0.operator'); r.query();
if (!r.next()) { r.initialize(); r.setValue('name', 'x_2215032_ai_inc_0.operator'); r.setValue('suffix', 'operator');
  r.setValue('sys_scope', '51a63bbf738bc7502aedfed25ab8b789');
  r.setValue('description', 'BARQ approver: approves or rejects BARQ AI runs waiting for a person'); r.insert(); }
gs.print('ROLE ' + r.getUniqueValue());
""", scope_sys_id="global")
print("role:", out[-80:])

# 3. Agent field ACLs through an uploaded update set (REST cannot create ACLs)
ROLE = get("sys_user_role", "name=x_2215032_ai_inc_0.integration_writer", "sys_id", 1)[0]["sys_id"]
PKG = (f'<sys_package display_value="AI Incident Orchestrator" source="x_2215032_ai_inc_0">{SCOPE}</sys_package>'
       f'<sys_policy/><sys_scope display_value="AI Incident Orchestrator">{SCOPE}</sys_scope>')
COND = "x_2215032_ai_inc_0_ai_human_lock=false^EQ"
import os
name = os.environ.get("BARQ_ACL_SET_NAME", "BARQ PDI - agent field ACLs")
fields = os.environ.get("BARQ_ACL_FIELDS", "state,incident_state,assignment_group,comments,close_code,close_notes,hold_reason").split(",")
wanted = [f for f in fields if not get("sys_security_acl", f"name=incident.{f}^operation=write^conditionLIKEai_human_lock", "sys_id", 1)]
if wanted and not get("sys_remote_update_set", f"name={name}^state=committed", "sys_id", 1):
    rus = uuid.uuid4().hex
    parts = ['<?xml version="1.0" encoding="UTF-8"?><unload unload_date="2026-10-03 21:00:00">',
             f'<sys_remote_update_set action="INSERT_OR_UPDATE"><application display_value="AI Incident Orchestrator">{SCOPE}</application><application_name>AI Incident Orchestrator</application_name><application_scope>x_2215032_ai_inc_0</application_scope><collisions/><commit_date/><deleted/><description>Field write ACLs so BARQ AI Agent can route, start, resolve, comment and put on hold, only while ai_human_lock=false.</description><inserted/><name>{escape(name)}</name><origin_sys_id/><parent display_value=""/><release_date/><remote_base_update_set display_value=""/><remote_parent_id/><remote_sys_id>{uuid.uuid4().hex}</remote_sys_id><state>loaded</state><summary/><sys_class_name>sys_remote_update_set</sys_class_name><sys_id>{rus}</sys_id><update_set display_value=""/><update_source display_value=""/><updated/></sys_remote_update_set>']
    for f in wanted:
        acl, link, nm = uuid.uuid4().hex, uuid.uuid4().hex, f"incident.{f}"
        desc = escape(f"Allow integration_writer (BARQ AI Agent) to write {f} on an incident that is not human-locked")
        acl_xml = (f'<?xml version="1.0" encoding="UTF-8"?><record_update table="sys_security_acl"><sys_security_acl action="INSERT_OR_UPDATE"><active>true</active><admin_overrides>true</admin_overrides><advanced>false</advanced><applies_to/><condition>{COND}</condition><controlled_by_refs/><decision_type>allow</decision_type><description>{desc}</description><local_or_existing>Existing</local_or_existing><name>{nm}</name><operation display_value="write">write</operation><script/><security_attribute/><sys_class_name>sys_security_acl</sys_class_name><sys_id>{acl}</sys_id><sys_name>{nm}</sys_name>{PKG}<sys_update_name>sys_security_acl_{acl}</sys_update_name><type display_value="record">record</type></sys_security_acl></record_update>')
        link_xml = (f'<?xml version="1.0" encoding="UTF-8"?><record_update table="sys_security_acl_role"><sys_security_acl_role action="INSERT_OR_UPDATE"><sys_class_name>sys_security_acl_role</sys_class_name><sys_id>{link}</sys_id><sys_name>{nm}.x_2215032_ai_inc_0.integration_writer</sys_name>{PKG}<sys_security_acl display_value="{nm}">{acl}</sys_security_acl><sys_update_name>sys_security_acl_role_{link}</sys_update_name><sys_user_role display_value="x_2215032_ai_inc_0.integration_writer" name="x_2215032_ai_inc_0.integration_writer">{ROLE}</sys_user_role></sys_security_acl_role></record_update>')
        for upd, typ, payload in ((f"sys_security_acl_{acl}", "Access Control", acl_xml),
                                  (f"sys_security_acl_role_{link}", "Access Roles", link_xml)):
            parts.append(f'<sys_update_xml action="INSERT_OR_UPDATE"><action>INSERT_OR_UPDATE</action><application display_value="AI Incident Orchestrator">{SCOPE}</application><category>customer</category><comments/><name>{upd}</name><payload>{escape(payload)}</payload><payload_hash/><remote_update_set display_value="{escape(name)}">{rus}</remote_update_set><replace_on_upgrade>false</replace_on_upgrade><sys_id>{uuid.uuid4().hex}</sys_id><table/><target_name>{escape(nm)}</target_name><type>{typ}</type><update_domain>global</update_domain><update_guid>{uuid.uuid4().hex}</update_guid><update_set display_value=""/><view/></sys_update_xml>')
    parts.append("</unload>")
    xml = "".join(parts)
    boundary = "----barq" + uuid.uuid4().hex
    def fld(k, v): return f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'
    body = (fld("sysparm_ck", s.ck) + fld("sysparm_referring_url", "sys_remote_update_set_list.do") + fld("sysparm_target", "sys_remote_update_set")
            + f'--{boundary}\r\nContent-Disposition: form-data; name="attachFile"; filename="barq_pdi_acls.xml"\r\nContent-Type: text/xml\r\n\r\n').encode() + xml.encode() + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(f"{BASE}/sys_upload.do", data=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}", "X-UserToken": s.ck})
    print("upload", s.op.open(req, timeout=120).status)
    s.ajax("UpdateSetPreviewAjax", sysparm_ajax_processor_function="preview", sysparm_ajax_processor_sys_id=rus)
    for _ in range(40):
        st = get("sys_remote_update_set", f"sys_id={rus}", "state", 1)[0]["state"]
        if st == "previewed": break
        time.sleep(3)
    problems = get("sys_update_preview_problem", f"remote_update_set={rus}", "type,description", 20)
    print("preview", st, "problems", problems)
    if st == "previewed" and not problems:
        s.ajax("UpdateSetCommitAjax", sysparm_type="commitRemoteUpdateSet", sysparm_remote_updateset_sys_id=rus)
        for _ in range(40):
            if get("sys_remote_update_set", f"sys_id={rus}", "state", 1)[0]["state"] == "committed": break
            time.sleep(3)
# 4. The app updates incidents (hand-offs, approvals) and its users' page creates them: the incident
# table must allow update and create from other application scopes, and the table cache must be
# flushed or the old setting keeps applying.
print("incident update from app scope", call("PATCH", "/api/now/table/sys_db_object/87e1e180a56503108bb220b7a4d212ec",
                                             {"update_access": "true", "create_access": "true"})[0])
background_script(s, "GlideTableManager.invalidateTable('incident'); gs.print('ok');", scope_sys_id="global")
# 5. Cross-scope privileges the app asks for at run time (enforcing mode) are allowed.
for p in get("sys_scope_privilege", f"source_scope={SCOPE}^status!=allowed", "sys_id,target_name", 50):
    print("privilege allowed", p["target_name"], call("PATCH", f"/api/now/table/sys_scope_privilege/{p['sys_id']}", {"status": "allowed"})[0])
time.sleep(5)
print("agent ACLs now:", sorted(a["name"] for a in get("sys_security_acl", "nameSTARTSWITHincident.^operation=write^conditionLIKEai_human_lock", "name", 20)))
