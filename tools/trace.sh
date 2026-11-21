#!/bin/sh
# Trace one ticket through the backend: what arrived, every run, every step, failures,
# approvals, and the worker log lines of each run.  Usage: tools/trace.sh INC0010243
N="$1"; [ -n "$N" ] || { echo "usage: trace.sh INC0010243"; exit 1; }
cd "$(dirname "$0")/../code" || exit 1
Q() { ./pdi.sh exec -T postgres sh -c "psql -U \"\$POSTGRES_USER\" -d \"\$POSTGRES_DB\" -P pager=off -c \"$1\""; }

echo "== Events from ServiceNow and the run each started"
Q "select to_char(ev.received_at,'HH24:MI:SS') at, ev.event_type, e.execution_id, e.status, e.termination_cause
   from events ev left join executions e on e.event_record_id=ev.id
   where ev.incident_number='$N' order by ev.received_at"

echo "== Steps of each run (node, status, time)"
Q "select left(w.execution_id::text,8) run, w.sequence_number seq, w.node_name step, w.status,
          to_char(w.started_at,'HH24:MI:SS') started, round(extract(epoch from w.ended_at-w.started_at)::numeric,1) secs,
          left(coalesce(w.decision::text,''),90) decision
   from workflow_state w join executions e on e.execution_id=w.execution_id join events ev on ev.id=e.event_record_id
   where ev.incident_number='$N' order by w.started_at, w.sequence_number"

echo "== Failures"
Q "select to_char(f.occurred_at,'HH24:MI:SS') at, f.failure_type, f.retryable, left(f.message,160) message
   from failures f join executions e on e.execution_id=f.execution_id join events ev on ev.id=e.event_record_id
   where ev.incident_number='$N' order by f.occurred_at"

echo "== Approvals"
Q "select to_char(a.decided_at,'HH24:MI:SS') at, a.decision, a.decided_by, left(a.reason,120) reason
   from approvals a join executions e on e.execution_id=a.execution_id join events ev on ev.id=e.event_record_id
   where ev.incident_number='$N' order by a.decided_at"

echo "== Worker log (last 2 hours) for these runs"
IDS=$(./pdi.sh exec -T postgres sh -c "psql -U \"\$POSTGRES_USER\" -d \"\$POSTGRES_DB\" -Atc \"select e.execution_id from events ev join executions e on e.event_record_id=ev.id where ev.incident_number='$N'\"" | tr '\n' '|' | sed 's/|$//')
[ -n "$IDS" ] && ./pdi.sh logs --since 2h --no-log-prefix celery-worker api 2>&1 | sed 's/\x1b\[[0-9;]*m//g' \
  | grep -E "$IDS" | grep -vE "tool_registry_enforcement" | cut -c1-260 | tail -60
