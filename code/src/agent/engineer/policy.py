"""The agentic engineer's hard rules, in code so the model cannot talk its way past them.

The model decides what to investigate, what to say and what to do; these functions decide
whether an action or an ending is *allowed* given what actually happened in the turn.
ServiceNow enforces the account rules a second time (BARQ account API).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

AccountAction = Literal["unlock", "require_password_change"]

#: The only account changes the agent can make, and the change that undoes each one.
UNDO: dict[str, str] = {
    "unlock": "lock",
    "require_password_change": "clear_password_change",
}

#: How a turn may end. The ticket state each one leads to is decided in ``report``.
OUTCOMES = (
    "waiting_for_caller",  # asked the caller something; On Hold - Awaiting Caller
    "fixed",  # the problem is fixed; Resolved, the caller can confirm or say it is not
    "closed",  # the caller confirmed (or only needed an answer and is done); Closed
    "with_engineer",  # needs a person; routed to the team with the full report
    "security",  # suspicious; routed to IT security, nothing done for the requester
    "cancelled",  # the caller asked to cancel; Cancelled
    "working",  # nothing changes for the caller (e.g. an engineer's instruction was done)
)

TEAMS = ("network", "software", "hardware", "database", "service_desk", "security")


@dataclass
class TurnFacts:
    """What happened so far in this turn, as the rules need it."""

    event_type: str
    caller_is_person: bool
    suspicious: bool = False
    suspicion: list[str] = field(default_factory=list)
    caller_account: dict | None = None  # last check_account result for the caller
    actions_done: list[str] = field(default_factory=list)
    instructed_by_engineer: bool = False


def account_action_refusal(action: str, facts: TurnFacts) -> str | None:
    """Why the agent may not make this account change now, or None if it may."""
    if action not in UNDO:
        return "That is not one of the account changes BARQ AI Agent can make."
    if facts.suspicious:
        return (
            "Not allowed: this ticket looks suspicious, so nothing is changed on any account. "
            "Hand it to security instead."
        )
    if not facts.caller_is_person:
        return "Not allowed: the caller is a system account, not a person."
    if facts.caller_account is None:
        return "Check the caller's account first (check_account), then decide."
    if facts.caller_account.get("privileged"):
        return "Not allowed: the caller has administrator rights; engineers handle those accounts."
    user = facts.caller_account.get("user") or {}
    if not user.get("active", True):
        return "Not allowed: the account is inactive; an engineer must look at it."
    if action in facts.actions_done:
        return "Already done in this turn."
    if action == "unlock" and not user.get("locked_out"):
        return "Not needed: the account is not locked."
    if action == "require_password_change" and user.get("password_needs_reset"):
        return "Not needed: a password change is already required."
    return None


def settle_outcome(outcome: str, team: str | None, facts: TurnFacts) -> tuple[str, str | None, str]:
    """The outcome actually applied, its team, and a note when the rules changed it."""
    note = ""
    if outcome not in OUTCOMES:
        outcome, note = "with_engineer", f"unknown outcome {outcome!r}: handed to an engineer"
    if facts.suspicious and outcome not in ("security", "with_engineer", "waiting_for_caller"):
        outcome, note = "security", "suspicious ticket: routed to security instead"
    if outcome == "closed" and facts.event_type not in (
        "incident.caller_replied",
        "incident.caller_updated",
    ):
        # Closing needs the caller's own word; a fix without it stays Resolved for them.
        outcome, note = "fixed", "closed only after the caller confirms: left Resolved"
    if outcome == "security":
        team = "security"
    if outcome == "with_engineer" and team not in TEAMS:
        team = "service_desk"
    if team is not None and team not in TEAMS:
        team = None
    return outcome, team, note


__all__ = [
    "OUTCOMES",
    "TEAMS",
    "UNDO",
    "AccountAction",
    "TurnFacts",
    "account_action_refusal",
    "settle_outcome",
]
