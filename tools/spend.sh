#!/bin/sh
# Print today's spend on the AI key (LiteLLM key-info endpoint). Needs LITELLM_BASE_URL and the key
# from a git-ignored secrets file (default ./.secrets/barq-g1.env, override with SECRETS_FILE).
HERE="$(cd "$(dirname "$0")" && pwd)"
set -a; . "${SECRETS_FILE:-$HERE/../.secrets/barq-g1.env}"; set +a
curl -s -m 20 "$LITELLM_BASE_URL/key/info" -H "Authorization: Bearer $LITELLM_API_KEY" | python3 -c 'import json,sys; i=json.load(sys.stdin)["info"]; print("spend $%.3f of $%s" % (i["spend"], i["max_budget"]))'
