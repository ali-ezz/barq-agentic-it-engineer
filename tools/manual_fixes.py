"""Engineer (beth.anglin) finishes the tickets that need a person — human in the loop. PDI test tickets only."""
import json, sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1] / "code/scripts/live"))
from verify_conversation import AdminSession
from verify_engineer_book import Instance
sn, admin = Instance(), AdminSession()
P = "x_2215032_ai_inc_0_ai_"
sid = lambda n: sn.query("incident", f"number={n}", "sys_id")[0]["sys_id"]

def as_beth(number, comment=None, note=None, fields=None):
    js = f"var inc = new GlideRecord('incident'); inc.get({json.dumps(sid(number))});\n"
    if comment: js += f"inc.comments = {json.dumps(comment)};\n"
    if note: js += f"inc.work_notes = {json.dumps(note)};\n"
    for k, v in (fields or {}).items(): js += f"inc.setValue({json.dumps(k)}, {json.dumps(v)});\n"
    js += "inc.update(); gs.print('DONE ' + inc.getDisplayValue('state'));"
    out = admin.run_as("beth.anglin", js)
    print(number, out.strip().splitlines()[-1][:80])

RESOLVE = lambda notes: {"state": "6", "close_code": "Solution provided", "close_notes": notes}

# Karim: security engineer answers after BARQ AI flagged it
as_beth("INC0010331",
    comment="Hi Karim, Beth from IT Security here. Thanks for raising this. For Sara's safety we only unlock an account when she contacts us herself so we can verify it's her. Please ask her to call the service desk and we'll help her right away. No changes were made to her account.",
    note="Security review: request on another person's account, flagged by BARQ AI. No action on barq.sara. Requester told the correct process.",
    fields=RESOLVE("Security reviewed; no change made. Account owner must contact the service desk."))
# Tarek: engineer corrects the process
as_beth("INC0010329",
    comment="Hi Tarek, Beth from IT Security. Admin access can't be added from a support ticket, even with a verbal approval. Please submit an access request in the portal; it goes to your manager and the Finance system owner for approval.",
    note="Security review: privileged access request with urgency/authority pressure, flagged by BARQ AI. Not granted; redirected to the access request process.",
    fields=RESOLVE("Access not granted from a ticket; redirected to the formal access request."))
# Yousef: security reviews the injection attempt
as_beth("INC0010344",
    note="Security review: prompt-injection attempt, flagged by BARQ AI. No accounts were changed. Logged for the security team.",
    comment="Hi Yousef, Beth from IT Security. We reviewed this ticket and there is nothing to action, so I'm closing it.",
    fields=RESOLVE("Injection attempt reviewed by Security; no action taken."))
as_beth("INC0010330", note="Same message as INC0010344; reviewed there.", fields={"state": "8", "close_notes": "Duplicate of INC0010344"})
# Hana: hardware engineer finishes the job
as_beth("INC0010335",
    comment="Hi Hana, Beth from the Hardware team. A replacement laptop is ready for you at the IT desk on the 2nd floor. Bring the damaged one and we'll move your files across while you wait.",
    fields=RESOLVE("Replacement laptop issued; files migrated at the IT desk."))
# Salma: engineer takes over (stays with the engineer -> card shows Hand back)
as_beth("INC0010337",
    comment="Hi Salma, Beth from the service desk here, I've taken over your ticket. I cleared the stuck jobs on the print server from my side. Please try printing again and reply here if anything is still stuck.")
# Dina asked to cancel
as_beth("INC0010338", note="Caller asked to cancel; Teams works after a restart.", fields={"state": "8", "close_notes": "Cancelled at the caller's request."})
# clean titles
for n, t in (("INC0010334", "Outlook on laptop shows Disconnected but webmail works"), ("INC0010336", "Caller reports something is not working - details requested")):
    as_beth(n, fields={"short_description": t})
# leftovers from the interrupted run (AI quota): no answer, not part of the demo
for n in ("INC0010339", "INC0010340", "INC0010341", "INC0010342", "INC0010343", "INC0010345", "INC0010346", "INC0010347"):
    sn.patch("incident", sid(n), {"state": "8", "close_notes": "Test run interrupted (AI quota); not part of the demo.", P + "enabled": "false"})
    print(n, "cancelled")
