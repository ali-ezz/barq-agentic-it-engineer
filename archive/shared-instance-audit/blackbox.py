"""Black-box audit of the SHARED EC2 API. Read-only plus requests that must be rejected.

Never prints secrets. Run: uv run python ../tmp/audit/blackbox.py   (from the repo dir)
"""

from __future__ import annotations

import base64
import json
import re
import sys
import uuid
from pathlib import Path

import httpx

SECRETS = Path(__file__).resolve().parents[2] / ".secrets" / "barq-g1.env"


def load_env() -> dict[str, str]:
    out: dict[str, str] = {}
    for line in SECRETS.read_text().splitlines():
        m = re.match(r"^([A-Z0-9_]+)=(.*)$", line)
        if m:
            v = m.group(2).strip()
            if len(v) >= 2 and v[0] == v[-1] and v[0] in "'\"":
                v = v[1:-1]
            out[m.group(1)] = v
    return out


ENV = load_env()
HOST = ENV["SHARED_BACKEND_HOST"]
BASE = f"http://{HOST}:8000"
RESULTS: list[tuple[str, str, str]] = []  # (area, check, verdict)


def rec(area: str, check: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((area, check, ("PASS" if ok else "FAIL") + (f" — {detail}" if detail else "")))


def token(client_id: str, secret: str) -> str | None:
    r = httpx.post(
        f"{BASE}/api/v1/oauth/token",
        data={"grant_type": "client_credentials"},
        auth=(client_id, secret),
        timeout=20,
    )
    return r.json().get("access_token") if r.status_code == 200 else None


c = httpx.Client(base_url=BASE, timeout=30)

# ---------------------------------------------------------------- tokens
op_secret = ENV.get("SHARED_WEBHOOK_AUTH_TOKEN") or ENV.get("WEBHOOK_AUTH_TOKEN", "")
op = token("barq-operator", op_secret)
rec("auth", "operator token mint (barq-operator)", op is not None)
wh = token(ENV.get("WEBHOOK_OAUTH_CLIENT_ID", ""), ENV.get("WEBHOOK_OAUTH_CLIENT_SECRET", ""))
rec("auth", "webhook-client token mint (local creds vs shared)", wh is not None,
    "" if wh else "local webhook client creds not accepted by shared (expected if rotated)")
bad = httpx.post(f"{BASE}/api/v1/oauth/token", data={"grant_type": "client_credentials"},
                 auth=("barq-operator", "wrong"), timeout=20)
rec("auth", "wrong secret -> 401", bad.status_code == 401, str(bad.status_code))
bad = httpx.post(f"{BASE}/api/v1/oauth/token", data={"grant_type": "password"},
                 auth=("barq-operator", op_secret), timeout=20)
rec("auth", "unsupported grant -> 400", bad.status_code == 400, str(bad.status_code))
bad = httpx.post(f"{BASE}/api/v1/oauth/token", data={"grant_type": "client_credentials"}, timeout=20)
rec("auth", "no credentials -> 401", bad.status_code == 401, str(bad.status_code))
bad = httpx.get(f"{BASE}/api/v1/oauth/token", timeout=20)
rec("auth", "GET token endpoint -> 405", bad.status_code == 405, str(bad.status_code))

H = {"Authorization": f"Bearer {op}"} if op else {}
WH = {"Authorization": f"Bearer {wh}"} if wh else {}
rid = str(uuid.uuid4())

# ---------------------------------------------------------------- every protected route needs auth
spec = c.get("/openapi.json").json()
local_spec = json.loads((Path(__file__).resolve().parents[2] / "barq-sprints-agentic-incident-resolution-platform-g1" / "openapi.json").read_text())
rec("deploy", "deployed openapi.json == repo openapi.json", spec == local_spec,
    "" if spec == local_spec else f"paths differ: {sorted(set(spec['paths']) ^ set(local_spec['paths']))}")
rec("deploy", "openapi version string", True, spec["info"].get("version", "?"))

public = {"/health", "/ready", "/api/v1/oauth/token"}
for path, methods in spec["paths"].items():
    for method in methods:
        if method.upper() not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
            continue
        url = re.sub(r"\{[^}]+\}", rid, path)
        r = c.request(method.upper(), url, json={} if method.upper() != "GET" else None)
        if path in public:
            rec("authz", f"{method.upper()} {path} public", r.status_code != 401, str(r.status_code))
        else:
            rec("authz", f"{method.upper()} {path} unauth -> 401", r.status_code == 401, str(r.status_code))

# operator-only routes must reject the ServiceNow webhook token, and vice-versa
if wh:
    for p in ("/api/v1/approvals", "/api/v1/dlq", "/api/v1/config", "/api/v1/eval/results"):
        r = c.get(p, headers=WH)
        rec("authz", f"webhook token rejected on operator route {p}", r.status_code in (401, 403), str(r.status_code))
if op:
    r = c.post("/api/v1/webhook/incident", headers=H, json={})
    rec("authz", "operator token rejected on webhook", r.status_code in (401, 403), str(r.status_code))
# forged / malformed bearer
for label, tok in (("garbage", "abc"), ("empty parts", "a.b.c"), ("alg none", base64.urlsafe_b64encode(b'{"alg":"none"}').decode().rstrip("=") + ".e30.")):
    r = c.get("/api/v1/approvals", headers={"Authorization": f"Bearer {tok}"})
    rec("authz", f"forged token ({label}) -> 401", r.status_code == 401, str(r.status_code))
r = c.get("/api/v1/approvals", headers={"Authorization": "Basic Zm9vOmJhcg=="})
rec("authz", "Basic scheme on bearer route -> 401", r.status_code == 401, str(r.status_code))

# ---------------------------------------------------------------- authenticated reads
if op:
    r = c.get("/api/v1/config", headers=H)
    rec("read", "GET /config 200", r.status_code == 200, str(r.status_code))
    body = r.text.lower()
    leaked = [k for k in ("password", "secret", "api_key", "signing_key", "token\":") if k in body and "redacted" not in body[max(0, body.find(k) - 40): body.find(k) + 80]]
    rec("security", "GET /config exposes no secret-looking values", not leaked, ",".join(leaked))
    r = c.get("/api/v1/approvals", headers=H)
    rec("read", "GET /approvals 200", r.status_code == 200, f"{r.status_code} rows={len(r.json()) if r.status_code == 200 else '?'}")
    r = c.get("/api/v1/approvals?execution_id=not-a-uuid", headers=H)
    rec("validation", "approvals invalid uuid filter -> 422", r.status_code == 422, str(r.status_code))
    r = c.get(f"/api/v1/approvals/{rid}", headers=H)
    rec("read", "GET unknown approval -> 404", r.status_code == 404, str(r.status_code))
    r = c.get(f"/api/v1/approvals/pending/{rid}", headers=H)
    rec("read", "GET unknown pending -> 404", r.status_code == 404, str(r.status_code))
    r = c.get("/api/v1/approvals/not-a-uuid", headers=H)
    rec("validation", "approval id not uuid -> 422", r.status_code == 422, str(r.status_code))
    r = c.get(f"/api/v1/executions/{rid}", headers=H)
    rec("read", "GET unknown execution -> 404", r.status_code == 404, str(r.status_code))
    r = c.get(f"/api/v1/executions/{rid}/trace", headers=H)
    rec("read", "GET unknown trace -> 404", r.status_code == 404, str(r.status_code))
    r = c.get("/api/v1/incidents/zzz/executions", headers=H)
    rec("validation", "incident sys_id malformed -> 4xx", 400 <= r.status_code < 500, str(r.status_code))
    r = c.get("/api/v1/incidents/" + "0" * 32 + "/executions", headers=H)
    rec("read", "unknown incident executions -> 200/404", r.status_code in (200, 404), str(r.status_code))
    r = c.get("/api/v1/dlq", headers=H)
    rec("read", "GET /dlq 200", r.status_code == 200, f"{r.status_code}")
    r = c.post(f"/api/v1/dlq/{rid}/replay", headers=H)
    rec("read", "replay unknown DLQ event -> 404", r.status_code == 404, str(r.status_code))
    r = c.get(f"/api/v1/suggestions/{rid}", headers=H)
    rec("read", "GET unknown suggestion -> 404", r.status_code == 404, str(r.status_code))
    r = c.get("/api/v1/eval/results", headers=H)
    rec("read", "GET /eval/results", r.status_code in (200, 501), f"{r.status_code} (stub by design)")
    r = c.post("/api/v1/eval/run", headers=H, json={"dataset_name": "x"})
    rec("read", "POST /eval/run", r.status_code in (422, 501), f"{r.status_code}")
    # decide on a non-paused execution must not create anything
    r = c.post(f"/api/v1/approvals/{rid}/decide", headers=H, json={"decision": "approved", "reason": "audit"})
    rec("write-guard", "decide unknown execution -> 404", r.status_code == 404, str(r.status_code))
    r = c.post(f"/api/v1/approvals/{rid}/decide", headers=H, json={"decision": "maybe"})
    rec("validation", "decide invalid decision -> 422", r.status_code == 422, str(r.status_code))
    r = c.post(f"/api/v1/approvals/{rid}/decide", headers=H, content=b"{not json", )
    rec("validation", "decide malformed JSON -> 4xx", 400 <= r.status_code < 500, str(r.status_code))
    r = c.post(f"/api/v1/suggestions/{rid}/decide", headers=H, json={"decision": "approved"})
    rec("write-guard", "suggestion decide unknown -> 404", r.status_code == 404, str(r.status_code))

# ---------------------------------------------------------------- webhook validation (rejections only)
if wh:
    for label, payload, want in (
        ("empty body", {}, 422),
        ("missing sys_id", {"event_id": "e", "number": "INC0000001"}, 422),
        ("bad sys_id", {"event_id": "e", "sys_id": "zz", "number": "INC0000001", "event_type": "incident.created"}, 422),
        ("bad number", {"event_id": "e", "sys_id": "a" * 32, "number": "../etc", "event_type": "incident.created"}, 422),
        ("bad event_type", {"event_id": "e", "sys_id": "a" * 32, "number": "INC0000001", "event_type": "evil"}, 422),
        ("full incident record smuggled", {"event_id": "e", "sys_id": "a" * 32, "number": "INC0000001", "event_type": "incident.created", "short_description": "x", "description": "y"}, 422),
    ):
        r = c.post("/api/v1/webhook/incident", headers=WH, json=payload)
        rec("webhook", f"reject: {label}", r.status_code == want, f"{r.status_code} want {want}")
    r = c.post("/api/v1/webhook/incident", headers=WH, content=b"{bad", )
    rec("webhook", "reject: malformed JSON", r.status_code in (400, 422), str(r.status_code))
    r = c.post("/api/v1/webhook/incident", headers={**WH, "content-type": "text/plain"}, content=b"x")
    rec("webhook", "reject: wrong content-type", r.status_code in (400, 415, 422), str(r.status_code))
    r = c.post("/api/v1/webhook/incident", headers=WH, content=b"x" * 2_000_000)
    rec("webhook", "reject: 2 MB body", 400 <= r.status_code < 500, str(r.status_code))
else:
    rec("webhook", "validation tests", False, "no webhook token available for shared (skipped)")

# ---------------------------------------------------------------- headers, error envelope, docs, static UI
r = c.get("/health", headers={"X-Correlation-ID": "audit-corr-123"})
rec("headers", "correlation id echoed", r.headers.get("x-correlation-id") == "audit-corr-123", r.headers.get("x-correlation-id", "none"))
r = c.get("/health")
rec("headers", "correlation id generated", bool(r.headers.get("x-correlation-id")), "")
for h in ("x-content-type-options", "strict-transport-security", "x-frame-options", "content-security-policy", "referrer-policy"):
    rec("headers", f"API sends {h}", h in r.headers, "present" if h in r.headers else "MISSING on API JSON responses")
r = c.get("/no-such-route")
rec("errors", "404 uses JSON envelope", r.headers.get("content-type", "").startswith("application/json"), r.text[:90])
r = c.get("/api/v1/approvals", headers={"Authorization": "Bearer x"})
rec("errors", "401 body has no stack/internal detail", "Traceback" not in r.text and "File \"" not in r.text, r.text[:90])
r = c.post("/health")
rec("errors", "405 handled", r.status_code == 405, str(r.status_code))
for p in ("/docs", "/redoc", "/review", "/review.js", "/review.css"):
    r = c.get(p)
    rec("surface", f"GET {p}", r.status_code == 200, str(r.status_code))
r = c.get("/docs")
rec("security", "Swagger UI exposed publicly (no auth)", False if r.status_code == 200 else True, "informational: /docs and /openapi.json are public")
r = c.get("/review")
rec("security", "/review has CSP + nosniff + no-store", all(k in r.headers for k in ("content-security-policy", "x-content-type-options", "cache-control")), "")
r = c.options("/api/v1/approvals", headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"})
rec("security", "no permissive CORS for foreign origin", "access-control-allow-origin" not in r.headers, r.headers.get("access-control-allow-origin", "none"))
r = c.get("/ready")
rec("health", "/ready 200 + db+redis", r.status_code == 200 and r.json().get("database") == "connected", r.text[:100])

# ---------------------------------------------------------------- report
width = max(len(a) for a, _, _ in RESULTS)
fails = 0
for area, check, verdict in RESULTS:
    if verdict.startswith("FAIL"):
        fails += 1
    print(f"{area:<{width}}  {verdict[:4]}  {check}" + (f"   [{verdict[7:]}]" if len(verdict) > 4 else ""))
print(f"\n{len(RESULTS)} checks, {fails} FAIL")
sys.exit(0)
