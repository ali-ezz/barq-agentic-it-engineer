"""One labelled event against an ALREADY-COMPLETE shared incident: idempotency + 202 latency.

Writes at most one BLOCKED execution-log row (ineligible: already processed). No LLM call.
"""

from __future__ import annotations

import asyncio
import re
import statistics
import time
import uuid
from pathlib import Path

import httpx

from app.clients.servicenow_client import ServiceNowClient
from app.core.config import get_settings

env: dict[str, str] = {}
for line in (Path(__file__).resolve().parents[2] / ".secrets" / "barq-g1.env").read_text().splitlines():
    m = re.match(r"^([A-Z0-9_]+)=(.*)$", line)
    if m:
        v = m.group(2).strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "'\"":
            v = v[1:-1]
        env[m.group(1)] = v
BASE = f"http://{env['SHARED_BACKEND_HOST']}:8000"


async def incident(number: str) -> tuple[str, str]:
    c = ServiceNowClient(get_settings())
    try:
        rows = await c._request(
            "GET", "/api/now/table/incident",
            params={"sysparm_query": f"number={number}", "sysparm_limit": 1,
                    "sysparm_fields": "sys_id,number,x_2215032_ai_inc_0_ai_processing_state"},
        )
        return rows[0]["sys_id"], rows[0]["x_2215032_ai_inc_0_ai_processing_state"]
    finally:
        await c.aclose()


NUMBER = "INC0010233"
sys_id, state = asyncio.run(incident(NUMBER))
print(f"target {NUMBER} ai_processing_state={state} (must be 'complete' so it is ineligible)")
assert state == "complete", "refusing: target is not an already-complete incident"

tok = httpx.post(
    f"{BASE}/api/v1/oauth/token", data={"grant_type": "client_credentials"},
    auth=(env["WEBHOOK_OAUTH_CLIENT_ID"], env["WEBHOOK_OAUTH_CLIENT_SECRET"]), timeout=20,
).json()["access_token"]
H = {"Authorization": f"Bearer {tok}"}
event = {"event_id": f"audit-{uuid.uuid4()}", "sys_id": sys_id, "number": NUMBER,
         "event_type": "incident.updated", "contract_version": "v1"}

lat: list[float] = []
bodies: list[dict] = []
with httpx.Client(base_url=BASE, timeout=30, headers=H) as c:
    for i in range(30):
        t0 = time.perf_counter()
        r = c.post("/api/v1/webhook/incident", json=event)
        lat.append((time.perf_counter() - t0) * 1000)
        bodies.append({"code": r.status_code, **(r.json() if r.status_code == 202 else {"raw": r.text[:120]})})
first, rest = bodies[0], bodies[1:]
print("first request :", first["code"], "idempotent_replay =", first.get("idempotent_replay"))
print("replays       :", {(b["code"], b.get("idempotent_replay")) for b in rest})
lat_sorted = sorted(lat)
print(f"202 latency over 30 requests from this Mac (incl. internet RTT): "
      f"p50={statistics.median(lat):.0f} ms  p95={lat_sorted[int(0.95*len(lat))-1]:.0f} ms  max={max(lat):.0f} ms")
print("event_id:", event["event_id"])
