"""Save a fix as a knowledge article when an engineer tells the agent to.

Reuses the knowledge-capture pipeline (compose the article, publish it in ServiceNow,
index it for search). The engineer's instruction is the authorisation, so the publish tool
is registered for this turn only; the toolbox lets the model call it only on a turn an
engineer started (``TurnFacts.instructed_by_engineer``), never on a caller's word.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


def save_article_for(payload: dict[str, Any], execution_id: str) -> Callable[[str, str, str], str]:
    def save(title: str, problem: str, fix: str) -> str:
        from agent.dependencies import get_agent_dependencies
        from agent.knowledge_capture import capture_human_resolution, make_next_article_number
        from agent.servicenow import IncidentGateway, build_servicenow_backend
        from agent.state import IncidentSnapshot
        from agent.tools import RefusalExplainer, build_servicenow_tool_registry
        from agent.tools.permissions import PermissionClass
        from agent.tools.registry import PostgreSQLApprovalChecker, ToolRegistration
        from app.clients.qdrant import get_qdrant_client
        from app.core.config import get_settings, kb_publisher_settings
        from app.publishing.servicenow_kb import ServiceNowKBClient, make_kb_publish_handler
        from app.utils.async_bridge import run_blocking
        from app.workers.sync_engine import (
            build_sync_database_url,
            create_sync_engine,
            create_sync_session_factory,
        )

        settings = get_settings()
        deps = get_agent_dependencies()
        kb_client = ServiceNowKBClient(kb_publisher_settings(settings))
        qdrant = get_qdrant_client()
        engine = create_sync_engine(build_sync_database_url(settings))
        try:
            registry = build_servicenow_tool_registry(
                IncidentGateway(build_servicenow_backend, deps.tracer),
                approval_checker=PostgreSQLApprovalChecker(create_sync_session_factory(engine)),
                refusal_explainer=RefusalExplainer(deps.llm),
                extra_registrations=[
                    ToolRegistration(
                        "publish_kb_article",
                        PermissionClass.LOW_RISK_WRITE,
                        make_kb_publish_handler(kb_client, settings.servicenow_kb_id),
                    )
                ],
            )
            incident = IncidentSnapshot(
                sys_id=str(payload.get("sys_id") or ""),
                number=str(payload.get("number") or ""),
                short_description=title,
                description=problem,
                priority=None,
                impact=None,
                urgency=None,
                category="",
                service=None,
                ai_enabled=True,
                ai_human_lock=False,
            )
            result = run_blocking(
                capture_human_resolution(
                    execution_id=execution_id,
                    incident=incident,
                    solution_text=f"{problem}\n\nFix:\n{fix}",
                    deps=replace(deps, tools=registry),
                    next_number=make_next_article_number(kb_client, settings.servicenow_kb_id),
                    qdrant_client=qdrant,
                    kb_sys_id=settings.servicenow_kb_id,
                )
            )
        finally:
            run_blocking(kb_client.aclose())
            qdrant.close()
            engine.dispose()
        if result is None:
            raise RuntimeError("the article could not be composed or published")
        logger.info("engineer_knowledge_saved", execution_id=execution_id)
        return str(getattr(result, "article_number", "") or getattr(result, "article_id", ""))

    return save


__all__ = ["save_article_for"]
