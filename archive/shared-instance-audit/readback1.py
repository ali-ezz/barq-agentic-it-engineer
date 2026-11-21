import sys, os, re, json, httpx, datetime as dt, collections; sys.path.insert(0, os.path.dirname(__file__))
from sn_admin import client, SCOPE, ENV
fx = json.load(open(os.path.join(os.path.dirname(__file__), "fixtures_batch1.json")))
print("=== ServiceNow read-back (what is actually on each incident)")
for key, f in fx.items():
    r = client.get("/api/now/table/incident/" + f["sys_id"], params={"sysparm_fields": f"number,priority,{SCOPE}ai_processing_state,{SCOPE}ai_human_review_required,{SCOPE}ai_classification,{SCOPE}ai_confidence,{SCOPE}ai_suggestion,{SCOPE}ai_resolution,{SCOPE}ai_processing_end,{SCOPE}ai_failure_reason"}).json()["result"]
    print(f"{f['number']} {key:<30} P{r['priority']} state={r[SCOPE+'ai_processing_state']:<18} review={r[SCOPE+'ai_human_review_required']:<5} conf={r[SCOPE+'ai_confidence'] or '-':<5} class={r[SCOPE+'ai_classification'] or '-':<9} sugg_len={len(r[SCOPE+'ai_suggestion'])} res_len={len(r[SCOPE+'ai_resolution'])} end={'yes' if r[SCOPE+'ai_processing_end'] else 'no'}")
print("\n=== Langfuse: is the planted fake secret visible in any trace payload?")
base = ENV["LANGFUSE_BASE_URL"].rstrip("/"); auth = (ENV["LANGFUSE_PUBLIC_KEY"], ENV["LANGFUSE_SECRET_KEY"])
since = (dt.datetime.now(dt.UTC) - dt.timedelta(minutes=25)).strftime("%Y-%m-%dT%H:%M:%SZ")
obs = httpx.get(f"{base}/api/public/v2/observations", params={"limit": 1000, "fromStartTime": since, "fields": "core,basic,time,io,metadata,model,usage"}, auth=auth, timeout=90).json()["data"]
marker = "NotARealSecret-731"
hits = collections.Counter()
for o in obs:
    blob = json.dumps({k: o.get(k) for k in ("input", "output", "metadata")}, default=str)
    if marker in blob: hits[o["name"]] += 1
print("observations scanned:", len(obs), "| names carrying the raw fake secret:", dict(hits) or "none")
# the injection incident: did any LLM generation see the override text?
inj = collections.Counter(o["name"] for o in obs if "Ignore all previous instructions" in json.dumps(o.get("input"), default=str))
print("names carrying the raw injection text:", dict(inj) or "none")
