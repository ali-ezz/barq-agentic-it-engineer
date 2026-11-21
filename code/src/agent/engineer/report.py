"""Apply the end of a turn to ServiceNow: the reply, the ticket state, the engineer report.

The report (field AI Report, JSON) is what the engineer's card shows: one summary line,
what the caller said vs. what the agent found, what it did (with undo), red flags, its
recommendation and the full timeline across every turn on the ticket.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

P = "x_2215032_ai_inc_0_ai_"

#: Ticket states (incident.state) the outcomes lead to.
STATE_IN_PROGRESS, STATE_ON_HOLD, STATE_RESOLVED, STATE_CLOSED, STATE_CANCELLED = (
    "2",
    "3",
    "6",
    "7",
    "8",
)
HOLD_AWAITING_CALLER = "1"
CLOSE_CODE = "Solution provided"
MAX_TIMELINE = 80

CLASSIFICATION_FOR_TEAM = {
    "network": "network",
    "software": "software",
    "hardware": "hardware",
    "database": "software",
    "service_desk": "other",
    "security": "security",
}


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")


def previous_report(view: dict[str, Any]) -> dict[str, Any]:
    raw = str(view.get(f"{P}report") or "").strip()
    if not raw:
        return {}
    try:
        report = json.loads(raw)
    except ValueError:
        return {}
    return report if isinstance(report, dict) else {}


def ticket_body(
    *,
    outcome: str,
    team_group: str | None,
    reply: str,
    finish: dict[str, Any],
    current_state: str,
    updates: dict[str, str],
    report: dict[str, Any],
    note: str,
    done: list[str] | None = None,
) -> dict[str, str]:
    """The single PATCH that ends the turn."""
    body: dict[str, str] = dict(updates)
    if reply.strip():
        body["comments"] = reply.strip()[:4000]
    summary = str(finish.get("summary") or "").strip()[:300]
    conclusion = str(finish.get("conclusion") or "").strip()[:1500]
    if outcome == "waiting_for_caller":
        body.update(state=STATE_ON_HOLD, hold_reason=HOLD_AWAITING_CALLER)
    elif outcome == "fixed":
        body.update(
            state=STATE_RESOLVED,
            close_code=CLOSE_CODE,
            close_notes=f"Resolved by BARQ AI Agent. {summary}\n\n{conclusion}"[:4000],
        )
    elif outcome == "closed":
        body.update(
            state=STATE_CLOSED,
            close_code=CLOSE_CODE,
            close_notes=f"Closed by BARQ AI Agent after the caller confirmed. {summary}\n\n"
            f"{conclusion}"[:4000],
        )
    elif outcome == "cancelled":
        body.update(
            state=STATE_CANCELLED, close_notes=f"Cancelled by BARQ AI Agent. {summary}"[:4000]
        )
    elif outcome in ("with_engineer", "security"):
        body["state"] = STATE_IN_PROGRESS
        if team_group:
            body["assignment_group"] = team_group
    elif current_state in ("1", ""):
        body["state"] = STATE_IN_PROGRESS
    if current_state == STATE_ON_HOLD and outcome not in ("waiting_for_caller",):
        body.setdefault("hold_reason", "")
    if outcome in ("with_engineer", "security") and "assignment_group" not in body and team_group:
        body["assignment_group"] = team_group

    confidence = finish.get("confidence")
    try:
        confidence_value = max(0.0, min(1.0, float(str(confidence))))
    except (TypeError, ValueError):
        confidence_value = 0.5
    body.update(
        {
            f"{P}processing_state": "complete",
            f"{P}confidence": f"{confidence_value:.2f}",
            f"{P}human_review_required": "true"
            if outcome in ("with_engineer", "security")
            else "false",
            f"{P}suggestion": summary,
            f"{P}processing_end": _now(),
            f"{P}activity": "",
            f"{P}report": json.dumps(report, ensure_ascii=False)[:64000],
        }
    )
    if outcome in ("fixed", "closed") and reply.strip():
        body[f"{P}resolution"] = reply.strip()[:4000]
    team = report.get("team")
    if team in CLASSIFICATION_FOR_TEAM:
        body[f"{P}classification"] = CLASSIFICATION_FOR_TEAM[team]
    work_note = engineer_note(report, note, done)
    if work_note:
        body["work_notes"] = work_note
    return body


def build_report(
    *,
    previous: dict[str, Any],
    finish: dict[str, Any],
    outcome: str,
    team: str | None,
    event_label: str,
    said: str,
    steps: list[Any],
    reply: str,
    rule_note: str,
    trace_url: str | None,
    execution_id: str,
    notes: list[str],
    started_at: str | None = None,
) -> dict[str, Any]:
    timeline = list(previous.get("timeline") or [])
    timeline.append(
        {"at": started_at or _now(), "kind": "event", "title": event_label, "detail": said[:500]}
    )
    actions = list(previous.get("actions") or [])
    for step in steps:
        timeline.append(
            {
                "at": step.at,
                "kind": "act"
                if step.action
                else ("check" if step.tool != "note_for_engineers" else "note"),
                "title": step.title if step.ok else f"{step.title} — not done",
                "reason": step.reason,
                "detail": step.result,
                "ok": step.ok,
            }
        )
        if step.action:
            actions.append(
                {
                    "at": step.at,
                    "action": step.action,
                    "title": step.title,
                    "undo": step.undo,
                    "undone": False,
                    "execution_id": execution_id,
                }
            )
    if reply.strip():
        timeline.append(
            {"at": _now(), "kind": "reply", "title": "Replied to the caller", "detail": reply[:800]}
        )
    timeline.append(
        {
            "at": _now(),
            "kind": "decision",
            "title": OUTCOME_TITLES.get(outcome, outcome),
            "detail": (rule_note + " " if rule_note else "")
            + str(finish.get("conclusion") or "")[:500],
        }
    )
    facts = [
        {"fact": str(f.get("fact") or "")[:300], "source": str(f.get("source") or "")}
        for f in (finish.get("facts") or [])
        if isinstance(f, dict) and f.get("fact")
    ][:15]
    return {
        "version": 1,
        "updated_at": _now(),
        "outcome": outcome,
        "status": OUTCOME_TITLES.get(outcome, outcome),
        "team": team,
        "summary": str(finish.get("summary") or "")[:300],
        "conclusion": str(finish.get("conclusion") or "")[:1500],
        "confidence": finish.get("confidence"),
        "said": said[:600],
        "facts": facts,
        "red_flags": [str(flag)[:300] for flag in (finish.get("red_flags") or [])][:10],
        "recommendation": _recommendation(finish.get("recommendation")),
        "actions": actions[-20:],
        "notes": notes[-5:],
        "timeline": timeline[-MAX_TIMELINE:],
        "trace_url": trace_url,
        "turns": int(previous.get("turns") or 0) + 1,
    }


def _recommendation(value: Any) -> str:
    """The engineer's next step, or nothing ("None, ..." from the model is nothing)."""
    text = str(value or "").strip()
    if not text or text.lower().startswith(("none", "n/a", "no action", "nothing")):
        return ""
    return text[:800]


OUTCOME_TITLES = {
    "waiting_for_caller": "Waiting for the caller's answer",
    "fixed": "Fixed — waiting for the caller to confirm",
    "closed": "Closed — the caller confirmed",
    "with_engineer": "Handed to an engineer",
    "security": "Sent to security — suspicious request",
    "cancelled": "Cancelled by the caller",
    "working": "Done what was asked",
}


def engineer_note(report: dict[str, Any], rule_note: str, done: list[str] | None = None) -> str:
    """One readable work note per turn, so the journal tells the story as well."""
    lines = [f"BARQ AI Agent — {report.get('status')}: {report.get('summary')}"]
    for fact in report.get("facts", [])[:6]:
        lines.append(f"• {fact['fact']} ({fact['source']})")
    for title in (done or [])[-3:]:
        lines.append(f"Done: {title}")
    for flag in report.get("red_flags", [])[:3]:
        lines.append(f"Red flag: {flag}")
    if report.get("recommendation"):
        lines.append(f"Recommendation: {report['recommendation']}")
    for extra in report.get("notes", [])[-2:]:
        lines.append(f"Note: {extra}")
    if rule_note:
        lines.append(f"Rule applied: {rule_note}")
    return "\n".join(lines)[:4000]


__all__ = [
    "OUTCOME_TITLES",
    "P",
    "build_report",
    "engineer_note",
    "previous_report",
    "ticket_body",
]
