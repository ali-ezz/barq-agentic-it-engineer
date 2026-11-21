"""Test people for the agentic-engineer scenario book (admin login, setup only).

Ordinary employees labelled "[BARQ-TEST]" in their title, no roles. ``reset`` puts each one
back in the state the scenarios expect: account flags and a back-dated sign-in history
written straight into the event log as already-processed records (no real sign-in is
attempted, and no lockout rule runs on them).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any

OFFICE = "10.20.30.41"  # the person's usual office address
FOREIGN = "185.220.101.7"  # an address the person never used

PEOPLE: dict[str, dict[str, Any]] = {
    # locked for real after mistyping a new password from the usual office
    "barq.lina": dict(
        first_name="Lina",
        last_name="Haddad",
        locked_out=True,
        failed=[(OFFICE, m) for m in (3, 5, 6, 8, 9)],
        ok=[(OFFICE, 60 * 26)],
    ),
    # says "locked" but is not: no failures, signed in fine this morning
    "barq.omar": dict(
        first_name="Omar", last_name="Saleh", locked_out=False, failed=[], ok=[(OFFICE, 90)]
    ),
    # the colleague someone else asks about: locked, failures from a foreign address
    "barq.sara": dict(
        first_name="Sara",
        last_name="Nasser",
        locked_out=True,
        failed=[(FOREIGN, m) for m in (2, 3, 4, 5, 6, 7)],
        ok=[(OFFICE, 60 * 20)],
    ),
    # asks for other people's access (the requester in the suspicious scenarios)
    "barq.karim": dict(
        first_name="Karim", last_name="Adel", locked_out=False, failed=[], ok=[(OFFICE, 30)]
    ),
    # thinks someone saw her password; not locked, two failures
    "barq.mona": dict(
        first_name="Mona",
        last_name="Fathy",
        locked_out=False,
        failed=[(OFFICE, 4), (OFFICE, 7)],
        ok=[(OFFICE, 60 * 30)],
    ),
    # ordinary callers for knowledge-base and hand-over scenarios
    "barq.yousef": dict(
        first_name="Yousef", last_name="Ali", locked_out=False, failed=[], ok=[(OFFICE, 45)]
    ),
    "barq.nour": dict(
        first_name="Nour", last_name="Hassan", locked_out=False, failed=[], ok=[(OFFICE, 50)]
    ),
    "barq.hana": dict(
        first_name="Hana", last_name="Mostafa", locked_out=False, failed=[], ok=[(OFFICE, 55)]
    ),
}

# One ordinary person per remaining scenario, so scenarios never see each other's tickets.
for _user, _first, _last in (
    ("barq.tarek", "Tarek", "Samir"),
    ("barq.rami", "Rami", "Khalil"),
    ("barq.ziad", "Ziad", "Fouad"),
    ("barq.salma", "Salma", "Ibrahim"),
    ("barq.dina", "Dina", "Mahmoud"),
    ("barq.layla", "Layla", "Youssef"),
    ("barq.mariam", "Mariam", "Adel"),
    ("barq.ahmed", "Ahmed", "Nabil"),
):
    PEOPLE[_user] = dict(
        first_name=_first, last_name=_last, locked_out=False, failed=[], ok=[(OFFICE, 40)]
    )


def ensure_people(sn: Any, names: list[str] | None = None) -> dict[str, str]:
    """Create or reset the people; returns user_name -> sys_id."""
    ids: dict[str, str] = {}
    for user_name in names or list(PEOPLE):
        spec = PEOPLE[user_name]
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
        rows = sn.query("sys_user", f"user_name={user_name}", "sys_id")
        if rows:
            ids[user_name] = rows[0]["sys_id"]
            sn.patch("sys_user", ids[user_name], values)
        else:
            ids[user_name] = sn.create("sys_user", values)["sys_id"]
    return ids


def reset_signins(admin: Any, names: list[str] | None = None) -> None:
    """Replace the people's sign-in history with the scenario history, back-dated."""
    names = names or list(PEOPLE)
    now = datetime.now(UTC)
    rows = []
    for user_name in names:
        spec = PEOPLE[user_name]
        for ok, entries in ((False, spec["failed"]), (True, spec["ok"])):
            for address, minutes_ago in entries:
                rows.append(
                    {
                        "name": "login" if ok else "login.failed",
                        "user": user_name,
                        "address": address,
                        "at": (now - timedelta(minutes=minutes_ago)).strftime("%Y-%m-%d %H:%M:%S"),
                    }
                )
    admin.run_as(
        "admin",
        f"var users = {json.dumps(names)}, rows = {json.dumps(rows)};\n"
        """var old = new GlideRecord('sysevent');
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
}""",
    )


__all__ = ["FOREIGN", "OFFICE", "PEOPLE", "ensure_people", "reset_signins"]
