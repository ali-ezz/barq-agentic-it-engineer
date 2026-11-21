"""Lina's account for the demo. `lock` = the story's starting state (locked + failed sign-ins);
`unlock` = so the Impersonate dialog can find her (it hides locked users)."""
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1] / "code/scripts/live"))
from engineer_fixtures import ensure_people, reset_signins
from verify_conversation import AdminSession
from verify_engineer_book import Instance
sn = Instance()
if sys.argv[1] == "lock":
    ensure_people(sn, ["barq.lina"]); reset_signins(AdminSession(), ["barq.lina"])
else:
    uid = sn.query("sys_user", "user_name=barq.lina", "sys_id")[0]["sys_id"]
    sn._call("PATCH", f"/api/now/table/sys_user/{uid}", {"locked_out": "false"})
print("barq.lina locked_out =", sn.query("sys_user", "user_name=barq.lina", "locked_out")[0]["locked_out"])
