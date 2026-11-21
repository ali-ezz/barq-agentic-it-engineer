"""Event type incident.engineer_instructed (the agentic engineer).

Revision ID: 0010_engineer_instructed
Revises: 0009_article_feedback
Create Date: 2026-10-04

An engineer can tell BARQ AI Agent what to do next on an incident the agent holds; that
arrives as its own event so the agent knows the instruction came from an engineer.
Downgrade restores the v2 check as NOT VALID, keeping rows already accepted.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0010_engineer_instructed"
down_revision: str | None = "0009_article_feedback"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

V2_TYPES = (
    "incident.created",
    "incident.updated",
    "incident.caller_replied",
    "incident.caller_updated",
    "incident.handed_back",
    "incident.engineer_replied",
    "incident.reopened",
    "incident.closed",
)
V3_TYPES = (*V2_TYPES, "incident.engineer_instructed")


def _in(values: Sequence[str]) -> str:
    return "event_type IN (" + ", ".join(f"'{value}'" for value in values) + ")"


def upgrade() -> None:
    op.drop_constraint(op.f("ck_events_event_type"), "events", type_="check")
    op.create_check_constraint(op.f("ck_events_event_type"), "events", _in(V3_TYPES))


def downgrade() -> None:
    op.drop_constraint(op.f("ck_events_event_type"), "events", type_="check")
    op.execute(
        "ALTER TABLE events ADD CONSTRAINT ck_events_event_type CHECK ("
        + _in(V2_TYPES)
        + ") NOT VALID"
    )
