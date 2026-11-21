"""Test people for the agentic-engineer scenarios on the PDI (admin, setup only).

Every person is labelled "[BARQ-TEST]" in their title and has no roles (ordinary employees).
`reset()` puts each one back in the state its scenarios expect: account flags, and recent
sign-in history written straight into the event log as already-processed records (no real
sign-in is attempted and no lockout rule runs on them).

    python fixtures_engineer.py            # create / reset all
"""
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from setup_pdi_call import call
from sn import get

MANIFEST = Path(__file__).resolve().parent.parent / "manifest.jsonl"
OFFICE = "10.20.30.41"  # the person's usual office address in the fixtures
FOREIGN = "185.220.101.7"  # an address the person never used

PEOPLE = {
    # locked for real after mistyping a new password from their usual office
    "barq.lina": dict(first_name="Lina", last_name="Haddad", department="Finance", locked_out=True,
                      failed=[(OFFICE, m) for m in (3, 5, 6, 8, 9)], ok=[(OFFICE, 60 * 26)]),
    # says "locked" but is not: no failures, signed in fine this morning
    "barq.omar": dict(first_name="Omar", last_name="Saleh", department="Sales", locked_out=False,
                      failed=[], ok=[(OFFICE, 90)]),
    # the colleague someone else asks about: locked, failures from a foreign address
    "barq.sara": dict(first_name="Sara", last_name="Nasser", department="Finance", locked_out=True,
                      failed=[(FOREIGN, m) for m in (2, 3, 4, 5, 6, 7)], ok=[(OFFICE, 60 * 20)]),
    # asks for other people's access (the requester in the suspicious scenarios)
    "barq.karim": dict(first_name="Karim", last_name="Adel", department="Sales", locked_out=False,
                       failed=[], ok=[(OFFICE, 30)]),
    # forgot password, not locked yet, two failures
    "barq.mona": dict(first_name="Mona", last_name="Fathy", department="HR", locked_out=False,
                      failed=[(OFFICE, 4), (OFFICE, 7)], ok=[(OFFICE, 60 * 30)]),
}


def ensure_person(user_name, spec):
    rows = get("sys_user", f"user_name={user_name}", "sys_id", 1)
    values = {
        "user_name": user_name,
        "first_name": spec["first_name"],
        "last_name": spec["last_name"],
        "email": f"{user_name}@example.com",
        "title": "[BARQ-TEST] employee",
        "active": "true",
        "locked_out": "true" if spec["locked_out"] else "false",
        "password_needs_reset": "false",
    }
    if rows:
        sys_id = rows[0]["sys_id"]
        call("PATCH", f"/api/now/table/sys_user/{sys_id}", values)
    else:
        code, res = call("POST", "/api/now/table/sys_user", values)
        if code >= 300:
            raise SystemExit(f"create {user_name}: {code} {res}")
        sys_id = res["sys_id"]
        with MANIFEST.open("a") as f:
            f.write(json.dumps({"op": "create", "table": "sys_user", "sys_id": sys_id,
                                "why": f"agentic-engineer test person {user_name}"}) + "\n")
    dept = get("cmn_department", f"name={spec['department']}", "sys_id", 1)
    if dept:
        call("PATCH", f"/api/now/table/sys_user/{sys_id}", {"department": dept[0]["sys_id"]})
    return sys_id


def reset_signins(people):
    """Replace each person's fixture sign-ins with the scenario history, back-dated.

    A background script is used because the Table API ignores sys_created_on."""
    from snsession import Session, background_script

    now = datetime.now(UTC)
    rows = []
    for user_name, spec in people.items():
        for ok, entries in ((False, spec["failed"]), (True, spec["ok"])):
            for address, minutes_ago in entries:
                at = (now - timedelta(minutes=minutes_ago)).strftime("%Y-%m-%d %H:%M:%S")
                rows.append({"name": "login" if ok else "login.failed", "user": user_name,
                             "address": address, "at": at})
    script = """
var users = %s, rows = %s;
var old = new GlideRecord('sysevent');
old.addQuery('name', 'IN', 'login,login.failed');
old.addQuery('parm1', 'IN', users.join(','));
old.query();
old.deleteMultiple();
for (var i = 0; i < rows.length; i++) {
    var e = new GlideRecord('sysevent');
    e.initialize();
    e.autoSysFields(false);
    e.setWorkflow(false);
    e.setValue('name', rows[i].name);
    e.setValue('parm1', rows[i].user);
    e.setValue('parm2', rows[i].address);
    e.setValue('state', 'processed');
    e.setValue('sys_created_on', rows[i].at);
    e.setValue('sys_updated_on', rows[i].at);
    e.insert();
}
gs.print('BARQEVENTS ' + rows.length);
""" % (json.dumps(list(people)), json.dumps(rows))
    out = background_script(Session(), script, scope_sys_id="global")
    if "BARQEVENTS" not in out:
        raise SystemExit("sign-in history not written: " + out[-300:])


def reset():
    ids = {}
    for user_name, spec in PEOPLE.items():
        ids[user_name] = ensure_person(user_name, spec)
    reset_signins(PEOPLE)
    return ids


if __name__ == "__main__":
    for user_name, sys_id in reset().items():
        print(user_name, sys_id)
