"""Install the ServiceNow side of the agentic engineer on the PDI (admin, setup only).

Idempotent: every record is found by a stable key and updated in place; every create or
change is appended to tools/servicenow_change_manifest.jsonl so it can be undone. Parts:
  include  global script include BarqAccount (sign-in events + the two account flags)
  rest     scripted REST "BARQ account" (facts + safe account actions), global scope
  fields   incident fields AI Report (JSON for the engineer card) and AI Activity (live line)
  props    supported categories: every incident category the agent may work
  ui       conversation rule, BarqAjax (card back-end), card UI script, retire approval buttons
Usage: python install_engineer_sn.py [rest] [fields] [props]   (no argument = all)
"""
import json
import sys
from pathlib import Path

from setup_pdi_call import call
from sn import get

HERE = Path(__file__).resolve().parent
LIVE = HERE.parent / "code/servicenow/ai_incident_orchestrator/live"
MANIFEST = HERE / "servicenow_change_manifest.jsonl"
SCOPE = "51a63bbf738bc7502aedfed25ab8b789"
parts = set(sys.argv[1:]) or {"include", "rest", "fields", "props", "ui"}


def log(entry):
    with MANIFEST.open("a") as f:
        f.write(json.dumps(entry) + "\n")


def upsert(table, query, values, why):
    rows = get(table, query, "sys_id", 2)
    if len(rows) > 1:
        raise SystemExit(f"{table}: more than one record for {query}")
    if rows:
        sys_id = rows[0]["sys_id"]
        code, res = call("PATCH", f"/api/now/table/{table}/{sys_id}", values)
        log({"op": "update", "table": table, "sys_id": sys_id, "why": why, "fields": sorted(values)})
    else:
        code, res = call("POST", f"/api/now/table/{table}", values)
        sys_id = res["sys_id"] if code < 300 else None
        log({"op": "create", "table": table, "sys_id": sys_id, "why": why})
    if code >= 300:
        raise SystemExit(f"{table} {query}: HTTP {code} {res}")
    print(f"{table}: {query} -> {sys_id}")
    return sys_id


if "include" in parts:
    # Created by a background script so it lands in the GLOBAL scope (the Table API puts
    # admin-created records in admin's current application).
    from snsession import Session, background_script

    script = (LIVE / "BarqAccount.js").read_text()
    out = background_script(
        Session(),
        """
var inc = new GlideRecord('sys_script_include');
inc.addQuery('api_name', 'global.BarqAccount');
inc.query();
var isNew = !inc.next();
if (isNew) inc.initialize();
inc.setValue('name', 'BarqAccount');
inc.setValue('sys_scope', 'global');
inc.setValue('sys_package', 'global');
inc.setValue('api_name', 'global.BarqAccount');
inc.setValue('access', 'public');
inc.setValue('active', true);
inc.setValue('client_callable', false);
inc.setValue('description', 'BARQ AI Agent: sign-in events and the two account flags, for the BARQ account API only.');
inc.setValue('script', """ + json.dumps(script) + """);
var id = isNew ? inc.insert() : (inc.update(), inc.getUniqueValue());
gs.print('BARQINC ' + (isNew ? 'created ' : 'updated ') + id + ' scope=' + inc.getValue('sys_scope'));
""",
        scope_sys_id="global",
    )
    import re

    found = re.search(r"BARQINC (created|updated) ([0-9a-f]{32}) scope=(\w+)", out)
    if not found:
        raise SystemExit("script include install failed: " + out[-400:])
    log({"op": "create" if found.group(1) == "created" else "update", "table": "sys_script_include",
         "sys_id": found.group(2), "why": "agentic engineer: global helper BarqAccount"})
    print("script include BarqAccount", found.group(1), found.group(2), "scope", found.group(3))

if "rest" in parts:
    api = upsert(
        "sys_ws_definition",
        "service_id=barq_account",
        {
            "name": "BARQ account",
            "service_id": "barq_account",
            "active": "true",
            "short_description": "What BARQ AI Agent may read about a person, and its few safe account actions.",
            "produces": "application/json",
            "consumes": "application/json",
            "sys_scope": "global",
        },
        "agentic engineer: account facts and safe actions for BARQ AI Agent",
    )
    for name, method, path, script in (
        ("facts", "GET", "/facts", "barq_account_facts.js"),
        ("action", "POST", "/action", "barq_account_action.js"),
    ):
        upsert(
            "sys_ws_operation",
            f"web_service_definition={api}^name={name}",
            {
                "name": name,
                "web_service_definition": api,
                "http_method": method,
                "relative_path": path,
                "operation_script": (LIVE / "rest" / script).read_text(),
                "requires_authentication": "true",
                # The script checks the agent's own role; no portal/internal role needed.
                "requires_acl_authorization": "false",
                "produces": "application/json",
                "consumes": "application/json",
                "active": "true",
                "sys_scope": "global",
            },
            f"agentic engineer: BARQ account {name}",
        )
    print("base uri:", get("sys_ws_definition", f"sys_id={api}", "base_uri", 1)[0]["base_uri"])

if "fields" in parts:
    for element, label, length in (
        ("x_2215032_ai_inc_0_ai_report", "AI Report", "65000"),
        ("x_2215032_ai_inc_0_ai_activity", "AI Activity", "255"),
    ):
        upsert(
            "sys_dictionary",
            f"name=incident^element={element}",
            {
                "name": "incident",
                "element": element,
                "column_label": label,
                "internal_type": "string",
                "max_length": length,
                "sys_scope": SCOPE,
            },
            f"agentic engineer: incident field {label}",
        )

if "props" in parts:
    upsert(
        "sys_properties",
        "name=x_2215032_ai_inc_0.s1_3_supported_categories",
        {"value": "software,network,hardware,inquiry,password_reset,database"},
        "agentic engineer: the agent works every incident category",
    )


if "ui" in parts:
    rule = get("sys_script", "name=BARQ AI - Conversation events^collection=incident", "sys_id", 1)
    if not rule:
        raise SystemExit("conversation rule not found: run servicenow_apply_live_ui.py first")
    code, _ = call("PATCH", f"/api/now/table/sys_script/{rule[0]['sys_id']}",
                   {"script": (LIVE / "business_rules/conversation_events.js").read_text(), "active": "true"})
    log({"op": "update", "table": "sys_script", "sys_id": rule[0]["sys_id"],
         "why": "agentic engineer: conversation rule (caller always to agent, engineer instructions)"})
    print("conversation rule", code)
    upsert(
        "sys_script_include",
        f"name=BarqAjax^sys_scope={SCOPE}",
        {
            "name": "BarqAjax",
            "api_name": "x_2215032_ai_inc_0.BarqAjax",
            "script": (LIVE / "BarqAjax.js").read_text(),
            "client_callable": "true",
            "access": "package_private",
            "active": "true",
            "description": "Engineer's BARQ AI card: data, take over / hand back, instruct, undo.",
            "sys_scope": SCOPE,
        },
        "agentic engineer: card back-end",
    )
    upsert(
        "sys_ui_script",
        f"script_name=barq_card^sys_scope={SCOPE}",
        {
            "name": "barq_card",
            "script_name": "barq_card",
            "script": (LIVE / "ui_scripts/barq_card.js").read_text(),
            "global": "false",
            "ui_type": "0",
            "active": "true",
            "description": "Draws and refreshes the engineer's BARQ AI card.",
            "sys_scope": SCOPE,
        },
        "agentic engineer: card UI script",
    )
    for macro in get("sys_ui_macro", f"name=barq_ai_card^sys_scope={SCOPE}", "sys_id", 2):
        call("PATCH", f"/api/now/table/sys_ui_macro/{macro['sys_id']}",
             {"xml": (LIVE / "ui_macros/barq_ai_card.xml").read_text()})
        log({"op": "update", "table": "sys_ui_macro", "sys_id": macro["sys_id"],
             "why": "agentic engineer: live card"})
        print("card macro updated")
    # The card has the one control button now; the old form buttons are retired.
    for name in ("Approve AI fix", "Reject AI fix", "Take over from AI", "Hand back to BARQ AI"):
        for row in get("sys_ui_action", f"name={name}^table=incident^active=true", "sys_id", 5):
            call("PATCH", f"/api/now/table/sys_ui_action/{row['sys_id']}", {"active": "false"})
            log({"op": "update", "table": "sys_ui_action", "sys_id": row["sys_id"],
                 "before": {"active": "true"}, "why": f"agentic engineer: retire form button {name}"})
            print("retired button", name)
