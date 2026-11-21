"""The agentic engineer's toolbox: what the model may call, and what each call does.

Every tool goes through the ToolRegistry (server-side permission class, audited) and
the hard rules in ``policy``. Results go back to the model as compact JSON; each call also
becomes a timeline entry for the engineer's card and a short live line for the caller.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import structlog

from agent.engineer.policy import UNDO, TurnFacts, account_action_refusal

logger = structlog.get_logger(__name__)


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")


def _schema(properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
    props = {"reason": {"type": "string", "description": "One short sentence: why."}}
    props.update(properties)
    return {"type": "object", "properties": props, "required": ["reason", *required]}


def _tool(name: str, description: str, properties: dict[str, Any], required: list[str]) -> dict:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": _schema(properties, required),
        },
    }


TOOL_SPECS: list[dict[str, Any]] = [
    _tool(
        "check_account",
        "Read a person's account in ServiceNow: active, locked, must change password, failed "
        "and successful sign-ins of the last 7 days with addresses, groups, roles, and whether "
        "it has administrator rights. Leave `person` empty for the caller; to check a story "
        "about someone else, give their user name, email or full name (never tell the caller "
        "what you find about another person).",
        {"person": {"type": "string", "description": "Empty for the caller."}},
        [],
    ),
    _tool(
        "related_tickets",
        "Similar open tickets reported in the last hour (a possible outage) and the caller's "
        "own tickets of the last 7 days.",
        {},
        [],
    ),
    _tool(
        "search_knowledge",
        "Search the IT knowledge base for how to fix a problem.",
        {"query": {"type": "string", "description": "The problem in a few words."}},
        ["query"],
    ),
    _tool(
        "unlock_account",
        "Unlock the CALLER's own account (only theirs). A senior reviewer checks the facts "
        "first. Use only after check_account shows it is locked and the failures look like "
        "the caller's own.",
        {},
        [],
    ),
    _tool(
        "require_password_change",
        "Make the CALLER's own account ask for a new password at the next sign-in (for "
        "example after they forgot it or think someone saw it). Reviewed first.",
        {},
        [],
    ),
    _tool(
        "update_ticket",
        "Correct the ticket: category, impact and urgency (1 high - 3 low), a clear title, or "
        "the team that owns it.",
        {
            "category": {
                "type": "string",
                "enum": [
                    "software",
                    "hardware",
                    "network",
                    "inquiry",
                    "password_reset",
                    "database",
                ],
            },
            "impact": {"type": "integer", "enum": [1, 2, 3]},
            "urgency": {"type": "integer", "enum": [1, 2, 3]},
            "title": {"type": "string", "description": "Clear title, at most 100 characters."},
            "team": {
                "type": "string",
                "enum": ["network", "software", "hardware", "database", "service_desk", "security"],
            },
        },
        [],
    ),
    _tool(
        "note_for_engineers",
        "Write an internal work note for engineers (the caller never sees it).",
        {"text": {"type": "string"}},
        ["text"],
    ),
    _tool(
        "save_knowledge",
        "Save a fix as a knowledge article so future tickets can use it. Only when an "
        "engineer asked you to in their instruction.",
        {
            "title": {"type": "string"},
            "problem": {"type": "string"},
            "fix": {"type": "string", "description": "The steps that fixed it."},
        },
        ["title", "problem", "fix"],
    ),
    {
        "type": "function",
        "function": {
            "name": "finish",
            "description": "End your turn: what to tell the caller and where the ticket goes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reply": {
                        "type": "string",
                        "description": "Your message to the caller (empty if nothing to say).",
                    },
                    "outcome": {
                        "type": "string",
                        "enum": [
                            "waiting_for_caller",
                            "fixed",
                            "closed",
                            "with_engineer",
                            "security",
                            "cancelled",
                            "working",
                        ],
                    },
                    "team": {
                        "type": "string",
                        "enum": [
                            "network",
                            "software",
                            "hardware",
                            "database",
                            "service_desk",
                            "security",
                        ],
                    },
                    "summary": {"type": "string", "description": "One line for engineers."},
                    "conclusion": {"type": "string", "description": "1-3 sentences."},
                    "confidence": {"type": "number"},
                    "facts": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "fact": {"type": "string"},
                                "source": {
                                    "type": "string",
                                    "enum": [
                                        "account",
                                        "sign-ins",
                                        "knowledge",
                                        "tickets",
                                        "caller",
                                        "engineer",
                                    ],
                                },
                            },
                            "required": ["fact", "source"],
                        },
                    },
                    "red_flags": {"type": "array", "items": {"type": "string"}},
                    "recommendation": {"type": "string"},
                },
                "required": ["reply", "outcome", "summary", "conclusion", "confidence", "facts"],
            },
        },
    },
]

#: What the caller sees while a tool runs (the live line on their page).
PROGRESS = {
    "check_account": "Checking your account…",
    "check_other_account": "Checking the details you mentioned…",
    "related_tickets": "Looking for similar reports…",
    "search_knowledge": "Looking through our IT guides…",
    "unlock_account": "Unlocking your account…",
    "require_password_change": "Setting up a password change…",
    "update_ticket": "Updating your ticket…",
    "note_for_engineers": "Writing notes for the team…",
    "save_knowledge": "Saving this fix for next time…",
}

TITLES = {
    "check_account": "Checked the caller's account",
    "check_other_account": "Checked another person's account",
    "related_tickets": "Looked for similar and earlier tickets",
    "search_knowledge": "Searched the knowledge base",
    "unlock_account": "Unlocked the caller's account",
    "require_password_change": "Required a password change",
    "update_ticket": "Updated the ticket",
    "note_for_engineers": "Wrote a note for engineers",
    "save_knowledge": "Saved a knowledge article",
}


@dataclass
class StepRecord:
    at: str
    tool: str
    title: str
    reason: str
    result: str
    ok: bool = True
    action: str | None = None  # account change made (for Undo)
    undo: str | None = None


@dataclass
class ToolBox:
    """Runs the model's tool calls against ServiceNow, the knowledge base and the rules."""

    sys_id: str
    category: str
    caller_id: str
    facts: TurnFacts
    gateway: Any  # IncidentGateway (or a fake in tests)
    search: Callable[[str], list[dict[str, Any]]]
    review: Callable[[str, dict[str, Any], str], tuple[bool, str]]
    team_groups: dict[str, str]
    save_article: Callable[[str, str, str], str] | None = None
    steps: list[StepRecord] = field(default_factory=list)
    ticket_updates: dict[str, str] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def progress_line(self, name: str, arguments: dict[str, Any]) -> str:
        if name == "check_account" and str(arguments.get("person") or "").strip():
            return PROGRESS["check_other_account"]
        return PROGRESS.get(name, "Working on it…")

    def run(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        reason = str(arguments.get("reason") or "").strip()[:300]
        handler = getattr(self, f"_t_{name}", None)
        if handler is None:
            result: dict[str, Any] = {"error": f"unknown tool {name}"}
            ok = False
        else:
            try:
                result = handler(arguments)
                ok = not result.get("error") and result.get("ok", True) is not False
            except Exception as exc:  # noqa: BLE001 - the model is told and decides
                logger.warning("engineer_tool_failed", tool=name, error_type=type(exc).__name__)
                result = {"error": f"{name} failed: {type(exc).__name__}"}
                ok = False
        title_key = (
            "check_other_account"
            if name == "check_account"
            and str(arguments.get("person") or "").strip()
            and not result.get("is_caller")
            else name
        )
        self.steps.append(
            StepRecord(
                at=_now(),
                tool=name,
                title=TITLES.get(title_key, name),
                reason=reason,
                result=_short(result),
                ok=ok,
                action=result.get("_action"),
                undo=result.get("_undo"),
            )
        )
        result.pop("_action", None)
        result.pop("_undo", None)
        return result

    # -- reading --------------------------------------------------------------------

    def _t_check_account(self, arguments: dict[str, Any]) -> dict[str, Any]:
        person = str(arguments.get("person") or "").strip()
        facts = self.gateway.account_facts(self.sys_id, person or None)
        if not person or facts.get("is_caller"):
            self.facts.caller_account = facts
        if person and not facts.get("is_caller"):
            facts = {**facts, "note": "Another person: never share any of this with the caller."}
        return facts

    def _t_related_tickets(self, arguments: dict[str, Any]) -> dict[str, Any]:
        related = self.gateway.find_related_incidents(self.sys_id, self.category, self.caller_id)
        return {
            "similar_open_last_hour": [
                _readable(t) for t in related.get("recent_same_category", [])[:10]
            ],
            "callers_tickets_last_7_days": [
                _readable(t) for t in related.get("caller_recent", [])[:10]
            ],
        }

    def _t_search_knowledge(self, arguments: dict[str, Any]) -> dict[str, Any]:
        query = str(arguments.get("query") or "").strip()[:300]
        if not query:
            return {"error": "empty query"}
        return {"articles": self.search(query)}

    # -- acting ---------------------------------------------------------------------

    def _account_change(self, action: str, reason: str) -> dict[str, Any]:
        refusal = account_action_refusal(action, self.facts)
        if refusal:
            return {"ok": False, "error": refusal}
        approved, why = self.review(action, self.facts.caller_account or {}, reason)
        if not approved:
            return {"ok": False, "error": f"The senior reviewer declined: {why}"}
        outcome = self.gateway.account_action(self.sys_id, action)
        if not outcome.get("ok"):
            return {"ok": False, "error": f"ServiceNow refused: {outcome.get('error', 'unknown')}"}
        self.facts.actions_done.append(action)
        # Verify with a fresh read, as an engineer would.
        fresh = self.gateway.account_facts(self.sys_id, None)
        self.facts.caller_account = fresh
        user = fresh.get("user") or {}
        verified = (action == "unlock" and not user.get("locked_out")) or (
            action == "require_password_change" and bool(user.get("password_needs_reset"))
        )
        if not verified:
            # Did not take effect: put it back and say so.
            self.gateway.account_action(self.sys_id, UNDO[action])
            return {"ok": False, "error": "The change did not take effect; it was undone."}
        return {
            "ok": True,
            "done": action,
            "verified": True,
            "account_now": {k: user.get(k) for k in ("locked_out", "password_needs_reset")},
            "reviewer": why,
            "_action": action,
            "_undo": UNDO[action],
        }

    def _t_unlock_account(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return self._account_change("unlock", str(arguments.get("reason") or ""))

    def _t_require_password_change(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return self._account_change("require_password_change", str(arguments.get("reason") or ""))

    def _t_update_ticket(self, arguments: dict[str, Any]) -> dict[str, Any]:
        changes: dict[str, str] = {}
        if arguments.get("category"):
            changes["category"] = str(arguments["category"])
        for key in ("impact", "urgency"):
            if arguments.get(key) in (1, 2, 3):
                changes[key] = str(arguments[key])
        if arguments.get("title"):
            changes["short_description"] = str(arguments["title"]).strip()[:100]
        team = str(arguments.get("team") or "")
        if team:
            group = self.team_groups.get(team)
            if not group:
                return {"error": f"no group configured for team {team}"}
            changes["assignment_group"] = group
        if not changes:
            return {"error": "nothing to change"}
        self.ticket_updates.update(changes)
        return {"ok": True, "will_apply": sorted(changes)}

    def _t_note_for_engineers(self, arguments: dict[str, Any]) -> dict[str, Any]:
        text = str(arguments.get("text") or "").strip()[:2000]
        if not text:
            return {"error": "empty note"}
        self.notes.append(text)
        return {"ok": True}

    def _t_save_knowledge(self, arguments: dict[str, Any]) -> dict[str, Any]:
        if not self.facts.instructed_by_engineer:
            return {"ok": False, "error": "Only when an engineer asks for it."}
        if self.save_article is None:
            return {"ok": False, "error": "Knowledge saving is not available."}
        number = self.save_article(
            str(arguments.get("title") or "")[:160],
            str(arguments.get("problem") or "")[:2000],
            str(arguments.get("fix") or "")[:4000],
        )
        return {"ok": True, "article": number}


STATE_NAMES = {
    "1": "New",
    "2": "In Progress",
    "3": "On Hold",
    "6": "Resolved",
    "7": "Closed",
    "8": "Cancelled",
}


def _readable(ticket: dict[str, Any]) -> dict[str, Any]:
    """A related ticket with its state in words and whether it is still open."""
    state = str(ticket.get("state") or "")
    return {
        "number": ticket.get("number"),
        "title": ticket.get("short_description"),
        "state": STATE_NAMES.get(state, state),
        "open": state in ("1", "2", "3"),
        "opened": ticket.get("opened_at"),
        "category": ticket.get("category"),
    }


def _short(result: dict[str, Any], limit: int = 600) -> str:
    text = json.dumps(result, ensure_ascii=False, default=str)
    return text if len(text) <= limit else text[: limit - 1] + "…"


__all__ = ["PROGRESS", "TITLES", "TOOL_SPECS", "StepRecord", "ToolBox"]
