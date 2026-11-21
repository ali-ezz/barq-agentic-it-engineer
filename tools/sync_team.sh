#!/bin/sh
# Bring the team's updates into the PDI copy. Read-only towards the team: it only fetches
# (the "team" remote has pushing disabled). Steps: fetch -> merge team/main and
# team/feat/admin-chatbot on a scratch branch -> lint + unit tests -> move `pdi` forward
# -> rebuild the running backend. If anything fails, `pdi` is left exactly as it was.
# CI-only conflicts (.github/) keep our version; any other conflict stops for a person.
# Log: sync.log. Usage: tools/sync_team.sh
export PATH=$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH
REPO="$(cd "$(dirname "$0")/../code" && pwd)"
LOG="$REPO/../sync.log"
cd "$REPO" || exit 1
say() { echo "$(date '+%Y-%m-%d %H:%M') $*" >> "$LOG"; }
alert() { say "$*"; osascript -e "display notification \"$*\" with title \"BARQ PDI sync\"" 2>/dev/null; }

pgrep -f "scripts/live/verify_" >/dev/null && { say "skipped: a live test is running"; exit 0; }
[ "$(git branch --show-current)" = pdi ] || { alert "skipped: not on branch pdi"; exit 1; }
[ -z "$(git status --porcelain)" ] || { alert "skipped: uncommitted changes in the copy"; exit 1; }
git fetch -q team || { alert "fetch failed"; exit 1; }

NEW=""
for b in main feat/admin-chatbot; do
  [ "$(git rev-list --count pdi..team/$b)" -gt 0 ] && NEW="$NEW team/$b"
done
[ -n "$NEW" ] || { say "up to date"; exit 0; }

git switch -q -C sync-tmp pdi
for ref in $NEW; do
  if ! git merge -q --no-ff --no-edit -m "Bring in team updates from ${ref#team/} ($(git rev-parse --short "$ref"))" "$ref" >/dev/null 2>&1; then
    OTHER=$(git diff --name-only --diff-filter=U | grep -v '^\.github/')
    if [ -n "$OTHER" ]; then
      git merge --abort; git switch -q pdi; git branch -q -D sync-tmp
      alert "needs a person: $ref conflicts in $(echo $OTHER | tr '\n' ' ')"; exit 1
    fi
    git diff --name-only --diff-filter=U | xargs git checkout --ours --
    git add -A .github && git commit -q --no-edit
    say "$ref: CI-only conflict, kept our .github version"
  fi
done

uv sync -q --all-extras --dev --locked >> "$LOG" 2>&1 \
  && uv run ruff check -q . >> "$LOG" 2>&1 \
  && uv run ruff format --check -q . >> "$LOG" 2>&1 \
  && uv run mypy src >> "$LOG" 2>&1
OK=$?
if [ $OK -eq 0 ]; then
  # the macOS native teardown abort can follow a fully green run; judge by the summary line
  uv run pytest -q -p no:randomly > /tmp/barq_sync_pytest.txt 2>&1
  tail -3 /tmp/barq_sync_pytest.txt >> "$LOG"
  grep -qE '^[0-9]+ passed' /tmp/barq_sync_pytest.txt && ! grep -qE '[0-9]+ (failed|error)' /tmp/barq_sync_pytest.txt || OK=1
fi
if [ $OK -ne 0 ]; then
  git switch -q -f pdi; git branch -q -D sync-tmp
  alert "team update$NEW NOT taken: checks failed (see sync.log)"; exit 1
fi

git switch -q pdi && git merge -q --ff-only sync-tmp && git branch -q -D sync-tmp
say "taken:$NEW -> pdi $(git rev-parse --short HEAD)"
if docker ps --format '{{.Names}}' | grep -q '^barqpdi-api$'; then
  ./pdi.sh build -q api celery-worker >> "$LOG" 2>&1 && ./pdi.sh up -d api celery-worker >> "$LOG" 2>&1 \
    && ./pdi.sh exec -T api alembic upgrade head >> "$LOG" 2>&1 \
    && alert "team updates taken and backend rebuilt" || alert "team updates taken, but the rebuild failed (see sync.log)"
else
  alert "team updates taken (backend not running, nothing rebuilt)"
fi
