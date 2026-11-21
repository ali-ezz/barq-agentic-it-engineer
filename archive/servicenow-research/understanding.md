# Full-system understanding notes (2026-10-03) — study worktree /private/tmp/barq-study @ d7548ea (#213 head = main e065df9 + chat)

## Graph (src/agent/graph.py, edges.py, nodes/*)
- Fixed 11-node pipeline: load→validate→classify→determine_risk→retrieve→diagnose→generate⇄verify_evidence(revise ≤max)→safety_check→confidence_check→act→END. Any missing section routes to act (fail closed).
- Risk is deterministic (policy.py): HIGH = priority in AGENT_RISK_PRIORITIES [1] or unknown or class `security`; ELEVATED = Tier-1 service (keys never match the shared instance, F-17) or MFA reset; else LOW.
- act outcomes: skipped_ineligible (log only) | escalated_high_risk/no_evidence/blocked/low_confidence → write awaiting_approval + note to SN, save interrupt, interrupt() | suggested: LOW → processing_state COMPLETE + ai_resolution=draft (incident NOT resolved/closed); ELEVATED → awaiting_approval + interrupt.
- Approve without solution uses stored draft; rejection → processing_state FAILED, clears suggestion.
- `_request_human_decision` returns approved when interrupt() raises RuntimeError (no graph context) — fail-open path, only safe if act is never called outside the graph.
- Write idempotency: 3-phase receipt (writing→fields_written→logged→written) + read-back probe.
- Agent's only SN write tools: read_incident, write_ai_fields, write_work_note, write_execution_log, (+publish_kb_article from S3.5). No assign/state/comment/resolve/related records.

## ServiceNow instance (dev407364) vs repo
- Hidden in-instance UI (not in repo): UI actions Approve/Refuse AI Suggestion (field-only, never call backend), Approve & Capture to KB ×2 (hard-coded operator secret, executions[0], marks complete even on backend failure), Replay AI Incident (re-fires S1.3 event); UI page barq_dlq_dashboard (server-side proxy using properties ec2_endpoint + operator_client_secret); modules; no roles on actions.
- SN: 92 awaiting_approval / 144 pending / 31 complete / 6 failed / 2 in progress; backend: 35 parked, 108 succeeded, 33 failed.

## Approvals / suggestions API
- POST /approvals/{id}/decide (role approver): checks no existing approval, execution status == awaiting_approval, advisory lock; if interrupt stored → resume graph off-loop (asyncio.to_thread) then insert immutable approval + close execution; capture KB if approved with solution. On main, a paused execution WITHOUT a stored interrupt still gets an immutable approval and no resume (audit F-8). decided_by = token subject "barq-operator" (no per-human identity; the reason text carries the SN display name only by convention).
- /suggestions/{execution_id}/decide: post-completion accept/reject of a COMPLETE draft (separate from interrupts) — writes SN directly (one of the 3 out-of-registry SN call sites, F-15).

## Worker (src/app/workers/tasks.py)
- Celery worker runs with embedded --beat (reaper of stale 'running' rows on maintenance queue). Concurrency 4 prefork on EC2, soft limit 120 s, hard 150 s, 5 retries w/ backoff, DLQ in Redis.
- Semantic cache admission (ENABLE_SEMANTIC_CACHE=true on EC2): LEADER runs graph and publishes solution; FOLLOWER of RESOLVED cluster → apply_follower_cluster_resolution writes leader's resolution with ai_processing_state COMPLETE and review flag false, NO per-incident risk/approval (F-1, from #210); write failure is swallowed and the run still marked succeeded (F-2). RUNNING/CREATING/AWAITING cluster → durable waiter row. `candidate_draft` always None (dead).

## Tool registry (docs/sprint3_tool_registry.md) — the extension point for new agent abilities
- Classes READ / LOW_RISK_WRITE / HIGH_RISK, server-owned, sealed. HIGH_RISK dispatch only when the latest approvals row for (execution_id, evidence.tool_name) is `approved` (rows immutable by trigger). Approval not consumed; not bound to argument hash. Every call permit/refusal audited; refusal explainer.
- Extension contract: name, class, narrow handler, typed args, approval scope, audit, permit/refusal/bypass tests, graph only via registry, doc + traceability update.
- Integration user ACLs (dev407364): writes only work_notes + the AI fields (+ table write when human_lock=false). No ACL for state/assignment/comments/close fields → new tools need new scoped field ACLs (admin setup).

## Chat (#213): separate LangGraph screen→route→cache→retrieve→answer→verify(1 repair)→persist; routes knowledge | incident_read | work_note but only knowledge implemented; no tool loop; operator JWT + per-browser session secret; CHAT_ENABLED default false; needs price rates; Streamlit UI (rejected by Ali). M4 (incident reads) and M5 (confirmed work notes) designed in docs/admin_chatbot_handoff.md §9–10.
- Backend /review page: paste execution id + bearer token manually — not usable by engineers.

## What Ali asked across sessions (10-02 → 10-03)
- 10-02: understand everything; S4.1 part 2 chatbot; then "test everything, fix everything before new features, one PR"; shared systems only ("Mohamed shared PDI" = dev407364); merges happened mid-session; parked runs: leave them.
- 10-03: closed #211/#212 himself (much wrong); #213 never merge as-is (draft now); goals = fully agentic + SN-native UI (no Streamlit, not localhost, engineers see everyone + approvals) + deep fix/test; test without pushing to main; careful: rotating secrets may break things and "there is a lot more".

## Server health (2026-10-03 ~05:10 Cairo)
- Qdrant 50 points (SN has 126 published KB articles across 4 bases; 85 in "Knowledge").
- api + worker restarted 2026-10-02 21:59:41Z (same minute #211/#212 were closed); restarts=0 since.
- Kernel log shows repeated global OOM kills of celery children (4 prefork on 3.8 GB, no swap).
- CORRECTION: server .env WEBHOOK_AUTH_TOKEN == running container's (my earlier tr command stripped a char). .env last edited 2026-10-02 21:49Z.
- Demo Day (ROADMAP): live automated resolution, human approval, guardrail block, worker-crash recovery; evidence: eval report, trace set, red-team results, ops runbook. CI eval gate (FR-20) still missing.
