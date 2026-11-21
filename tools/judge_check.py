"""Light check as a brand-new user: random judge-style questions, one turn each."""
import sys, json
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1] / "code/scripts/live"))
from verify_conversation import AdminSession
from verify_engineer_book import Instance, Conversation
sn = Instance()
USER = "guest.tester"
if not sn.query("sys_user", f"user_name={USER}", "sys_id"):
    sn.create("sys_user", {"user_name": USER, "first_name": "Guest", "last_name": "Tester",
                           "email": "guest.tester@example.com", "title": "[BARQ-TEST] employee", "active": "true"})
print("user:", sn.query("sys_user", f"user_name={USER}", "name,locked_out,active")[0])
QUESTIONS = sys.argv[1:] or [
    "How do I reset my password?",
    "My wifi keeps disconnecting in the meeting room.",
    "I need Adobe Photoshop installed on my laptop.",
    "My laptop is very slow since this morning.",
    "الإنترنت بطيء جدا عندي اليوم",
    "What's the weather like today?",
]
def ask(q):
    c = Conversation(sn, AdminSession(), USER, label="")
    try:
        t = c.open(q)
        return {"q": q, "inc": c.number, "outcome": t["outcome"], "team": t["team"], "secs": t["seconds"],
                "steps": t["steps"], "reply": t["reply"]}
    except Exception as e:
        return {"q": q, "inc": c.number, "error": str(e)}
with ThreadPoolExecutor(3) as pool:
    for r in pool.map(ask, QUESTIONS):
        print("\n==", r["q"]); print(json.dumps({k: v for k, v in r.items() if k != "q"}, ensure_ascii=False, indent=1))
