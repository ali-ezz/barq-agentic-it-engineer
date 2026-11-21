# Test tools -> your own ServiceNow PDI + your local backend ONLY. Usage: . tools/liveenv.sh
# Expects a git-ignored secrets file (default ./.secrets/barq-g1.env, override with SECRETS_FILE)
# and the backend settings file code/.env.pdi.
HERE="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
set -a; . "${SECRETS_FILE:-$HERE/../.secrets/barq-g1.env}"; set +a
export SN_INSTANCE_URL="${SN_INSTANCE_URL:?set SN_INSTANCE_URL to your PDI, e.g. https://devNNNNNN.service-now.com}"
export BACKEND_URL=http://127.0.0.1:18000
export OPERATOR_SECRET="$(grep '^WEBHOOK_AUTH_TOKEN=' "$HERE/../code/.env.pdi" | cut -d= -f2-)"
unset SHARED_BACKEND_HOST SHARED_OPERATOR_SECRET SN407364_ADMIN_USER SN407364_ADMIN_PASS
