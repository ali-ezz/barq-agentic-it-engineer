"""Admin helper for the SHARED instance dev407364. Setup only: creates labelled test incidents."""
from __future__ import annotations
import re, httpx
from pathlib import Path

def load_env():
    env = {}
    for line in (Path(__file__).resolve().parents[2] / ".secrets" / "barq-g1.env").read_text().splitlines():
        m = re.match(r"^([A-Z0-9_]+)=(.*)$", line)
        if m:
            v = m.group(2).strip()
            if len(v) >= 2 and v[0] == v[-1] and v[0] in "'\"":
                v = v[1:-1]
            env[m.group(1)] = v
    return env

ENV = load_env()
BASE = ENV["SERVICENOW_INSTANCE_URL"].rstrip("/")
assert "dev407364" in BASE, f"refusing: not the shared instance ({BASE.split('.')[0]})"
client = httpx.Client(base_url=BASE, auth=(ENV["SN407364_ADMIN_USER"], ENV["SN407364_ADMIN_PASS"]),
                      headers={"Accept": "application/json"}, timeout=60)
SCOPE = "x_2215032_ai_inc_0_"
