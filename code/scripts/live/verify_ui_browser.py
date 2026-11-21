# ruff: noqa: E501 - selectors and checks read best on one line
"""Real-browser check of the agentic engineer's two screens, in Chrome (desktop).

An admin session (setup only) impersonates the people, who use the pages exactly as a
person would:
  1. the caller opens the BARQ AI chat, describes the problem and watches the live
     "working" bubble; the answer types itself in without pressing Refresh;
  2. the engineer opens the incident: the BARQ AI card shows the summary, what the caller
     said vs. what the agent found, what it did with Undo, the timeline and the trace link;
  3. the engineer takes over (one button), then hands back with an instruction: the card
     follows the agent live;
  4. the caller sees the agent's follow-up, confirms it works, and the chat closes.
Screenshots go to --shots. Needs Playwright:

    uv run --with playwright python scripts/live/verify_ui_browser.py --out ui.json \
        --shots /tmp/barq-ui
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from engineer_fixtures import ensure_people, reset_signins  # noqa: E402
from verify_agentic_core import ServiceNow  # noqa: E402
from verify_conversation import AdminSession  # noqa: E402

CALLER = "barq.lina"
ENGINEER = "beth.anglin"
RAW_MARKUP = ("::chunk::", "**", "###", "<<<", '{"')
PROBLEM = (
    "I can't sign in this morning, it says my account is locked. I changed my password yesterday."
)


class Instance(ServiceNow):
    def create(self, table: str, fields: dict[str, Any]) -> dict[str, Any]:
        return self._call("POST", f"/api/now/table/{table}", fields)


def main() -> int:  # noqa: PLR0915 - one linear walk through both screens
    from playwright.sync_api import sync_playwright

    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--out", required=True)
    parser.add_argument("--shots", required=True)
    args = parser.parse_args()
    shots = Path(args.shots)
    shots.mkdir(parents=True, exist_ok=True)

    sn, admin = Instance(), AdminSession()
    ensure_people(sn, [CALLER])
    reset_signins(admin, [CALLER])
    users = {
        name: sn.query("sys_user", f"user_name={name}", "sys_id")[0]["sys_id"]
        for name in (CALLER, ENGINEER)
    }
    host = admin.url.split("//", 1)[1]
    jar = next(h.cookiejar for h in admin.opener.handlers if hasattr(h, "cookiejar"))
    cookies = [
        {"name": c.name, "value": c.value, "domain": host, "path": c.path or "/"} for c in jar
    ]
    checks: dict[str, bool] = {}
    timings: dict[str, float] = {}
    evidence: dict[str, Any] = {"started_at": datetime.now(UTC).isoformat(), "caller": CALLER}

    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome")
        context = browser.new_context(viewport={"width": 1440, "height": 950})
        context.add_cookies(cookies)
        page = context.new_page()
        # Developer instances can take well over 30 s to serve the first full page.
        page.set_default_navigation_timeout(90000)
        errors: list[str] = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))

        def shot(name: str) -> None:
            page.screenshot(path=str(shots / f"{name}.png"), full_page=False)

        def impersonate(user_sys_id: str) -> None:
            page.goto(f"{admin.url}/now/nav/ui/home", wait_until="domcontentloaded")
            token = page.evaluate("() => window.g_ck || ''") or admin.ck
            page.request.post(
                f"{admin.url}/api/now/ui/impersonate/{user_sys_id}",
                headers={"X-UserToken": token, "Content-Type": "application/json"},
                data="{}",
            )

        def agent_bubbles() -> int:
            return page.locator(".barq-msg.barq-agent:not(.barq-typing)").count()

        # 1. The caller: a chat that opens on a friendly welcome.
        impersonate(users[CALLER])
        page.goto(f"{admin.url}/esc?id=barq_ai", wait_until="networkidle")
        page.wait_for_selector(".barq-welcome", timeout=30000)
        shot("01_chat_welcome")
        checks["opens_on_welcome"] = page.locator(".barq-welcome").is_visible()
        checks["virtual_agent_bubble_hidden"] = not page.locator(".sp-ac-root").is_visible()
        checks["no_buttons_besides_new_and_send"] = page.locator(".barq-main button").count() == 1

        page.fill(".barq-compose textarea", PROBLEM)
        page.keyboard.press("Enter")
        sent = time.monotonic()
        page.wait_for_selector(".barq-top", timeout=30000)
        evidence["incident"] = page.locator(".barq-top-number").inner_text()
        activity: list[str] = []
        live_seen = False
        while time.monotonic() - sent < 180 and agent_bubbles() == 0:
            if page.locator(".barq-typing").count():
                live_seen = True
                text = page.locator(".barq-activity").first.inner_text().strip()
                if text and (not activity or activity[-1] != text):
                    activity.append(text)
                    if len(activity) == 2:
                        shot("02_live_activity")
            page.wait_for_timeout(400)
        evidence["live_lines"] = activity
        checks["live_activity_shown"] = live_seen and len(activity) >= 2
        page.wait_for_selector(".barq-msg.barq-agent:not(.barq-typing)", timeout=60000)
        timings["answer_on_screen_s"] = round(time.monotonic() - sent, 1)
        first_len = len(page.locator(".barq-msg.barq-agent .barq-text").last.inner_text())
        page.wait_for_timeout(700)
        later_len = len(page.locator(".barq-msg.barq-agent .barq-text").last.inner_text())
        checks["answer_types_itself_in"] = later_len > first_len
        page.wait_for_timeout(2500)
        shot("03_answer")
        answer = page.locator(".barq-msg.barq-agent .barq-text").last.inner_text()
        evidence["answer"] = answer
        status = page.locator(".barq-top .barq-status").inner_text()
        evidence["status_after_answer"] = status
        checks["answer_without_refresh"] = len(answer) > 40
        checks["answer_within_90s"] = timings["answer_on_screen_s"] <= 90
        checks["answer_is_readable"] = not any(mark in answer for mark in RAW_MARKUP)
        checks["status_tells_next_step"] = any(word in status for word in ("Fixed", "Waiting"))
        number = evidence["incident"]
        sys_id = sn.query("incident", f"number={number}", "sys_id")[0]["sys_id"]

        # 2. The engineer: the card tells the whole story.
        impersonate(users[ENGINEER])
        page.goto(f"{admin.url}/incident.do?sys_id={sys_id}", wait_until="networkidle")
        page.wait_for_selector("#barq-card .barq-summary", timeout=60000)
        shot("04_engineer_card")
        card = page.locator("#barq-card")
        checks["card_has_summary"] = bool(card.locator(".barq-summary").inner_text().strip())
        checks["card_said_vs_found"] = card.locator(".barq-facts li").count() >= 2
        checks["card_action_with_undo"] = card.locator(".barq-undo").count() >= 1
        checks["card_one_control_button"] = card.locator("#barq-control").count() == 1
        checks["old_form_buttons_gone"] = (
            page.locator("button#barq_approve_ai_fix, button#barq_reject_ai_fix").count() == 0
        )
        card.locator("#barq-toggle").click()
        page.wait_for_timeout(500)
        checks["card_timeline_opens"] = card.locator(".barq-timeline li").count() >= 4
        checks["card_trace_link"] = card.locator(".barq-trace").count() == 1
        shot("05_engineer_timeline")

        # 3. Take over, then hand back with an instruction; the card follows the agent live.
        card.locator("#barq-control").click()
        try:  # the button reloads the page once the take-over is saved
            page.wait_for_function(
                "() => /Hand back/.test(document.getElementById('barq-control')?.innerText || '')",
                timeout=60000,
            )
            checks["take_over_locks_agent_out"] = True
        except Exception:  # noqa: BLE001 - recorded as a failed check
            checks["take_over_locks_agent_out"] = False
        shot("06_engineer_holds")
        page.fill(
            "#barq-text",
            "Tell her I will keep an eye on her account today and she can reply here if it locks again.",
        )
        page.locator("#barq-send").click()
        page.wait_for_load_state("networkidle")
        handed = time.monotonic()
        working_seen = False
        while time.monotonic() - handed < 150:
            text = (
                page.locator("#barq-card .barq-chip").inner_text()
                if page.locator("#barq-card .barq-chip").count()
                else ""
            )
            if "working" in text.lower():
                working_seen = True
                if not (shots / "07_card_live.png").exists():
                    shot("07_card_live")
            elif working_seen:
                break
            page.wait_for_timeout(800)
        checks["card_shows_agent_working_live"] = working_seen
        page.wait_for_timeout(2000)
        shot("08_card_after_hand_back")

        # 4. The caller sees the follow-up and confirms; the chat closes.
        impersonate(users[CALLER])
        page.goto(f"{admin.url}/esc?id=barq_ai", wait_until="networkidle")
        page.wait_for_selector(".barq-item", timeout=30000)
        page.locator(".barq-item").first.click()
        page.wait_for_selector(".barq-msg.barq-agent", timeout=30000)
        page.wait_for_timeout(1500)
        checks["caller_sees_follow_up"] = agent_bubbles() >= 2
        page.fill(".barq-compose textarea", "Yes, I can sign in now. Thanks a lot!")
        page.keyboard.press("Enter")
        confirmed = time.monotonic()
        try:
            page.wait_for_selector(".barq-closed", timeout=150000)
            checks["closes_after_confirmation"] = True
        except Exception:  # noqa: BLE001 - recorded as a failed check
            checks["closes_after_confirmation"] = False
        timings["close_s"] = round(time.monotonic() - confirmed, 1)
        page.wait_for_timeout(2500)
        shot("09_closed")
        checks["no_script_errors"] = not [e for e in errors if "barq" in e.lower()]
        evidence["script_errors"] = errors[:10]
        browser.close()

    evidence.update(
        {
            "checks": checks,
            "timings": timings,
            "passed": all(checks.values()),
            "shots": sorted(str(p) for p in shots.glob("*.png")),
        }
    )
    Path(args.out).write_text(json.dumps(evidence, indent=2, ensure_ascii=False), encoding="utf-8")
    print(
        json.dumps({"checks": checks, "timings": timings, "passed": evidence["passed"]}, indent=1)
    )
    return 0 if evidence["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
