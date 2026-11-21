## Do not merge during a demo or a burst of work

**Merging this restarts the `postgres`, `redis` and `qdrant` containers once on the shared EC2** (a few seconds; the named data volumes persist). The deploy recreates them because their published-port configuration changes; the API and worker are recreated by every deploy anyway, and this deploy also rebuilds the image (the Dockerfile changes). In-flight runs recover through the existing retry path. Pick a quiet window. This is a **draft** so it cannot be merged by accident; mark it ready when the window is chosen.

## Why

Found during the 2026-10-02 audit of the shared host (full write-up in `docs/audit_2026-10-02.md` on #211, findings O-3 to O-5):

- `BIND_IP=0.0.0.0` on the host publishes PostgreSQL, Redis and Qdrant on **every interface**. Only the AWS security group protects them (verified closed on 2026-10-02: 5432, 6379, 6333, 6334; only SSH and 8000 answered). Qdrant has no API key. One security-group change would expose all the data.
- `pgweb` and `redis-commander` are unauthenticated admin UIs on `:latest` that start on a plain `docker compose up`.
- No container log rotation, on a 19 GB disk shared with every image the host builds. No swap.
- The deploy builds on the host and never reclaims anything; about 17 GB of images and build cache had accumulated and the disk was at 77-80%.
- The Dockerfile pulls `uv:latest` and a rolling Python tag, and trusts `X-Forwarded-*` from any client, so any caller could spoof its address in the access log.

## What changes (5 files, +107 / -14)

| File | Change |
|---|---|
| `docker-compose.yml` | `postgres`, `redis` and `qdrant` (6333 and 6334) are **always** published on `127.0.0.1`; `BIND_IP` now applies to the API only. The services reach the datastores over the compose network (`barq-postgres`, `barq-redis`, `barq-qdrant`), not through a published port, so nothing inside the stack changes. `pgweb` (pinned to `0.17.0`) and `redis-commander` move behind the `tools` profile and stay on loopback. Every service gets bounded `json-file` logs (10 MB x 3 files) |
| `Dockerfile` | `uv` pinned to `0.12.19` (was `latest`); Python base `python:3.12-slim` → `python:3.12-slim-bookworm`; uvicorn `--forwarded-allow-ips=*` → `127.0.0.1` |
| `.github/workflows/deploy.yml` | After a good deploy: `docker image prune -f` and `docker builder prune -f --filter until=72h`, then `df -h /`. Both prunes end in `|| true`, so a prune failure cannot fail a deploy, and neither command touches volumes or images in use |
| `.env.example` | `BIND_IP` comment corrected: it governs the API port only |
| `tests/repo/test_deployment_hardening.py` | Six tests pin each of the above |

Opt-in admin tools, when someone needs them: `docker compose --profile tools up -d pgweb` (or `redis-commander`), then reach them on the host's loopback, for example through an SSH tunnel. `redis-commander` stays on `:latest` because it publishes no semver tags; it is now opt-in and loopback-only instead.

## Who is affected

- Nobody reaching the datastores from outside the host loses access that worked: the security group already blocked those ports (verified 2026-10-02). What goes away is the *dependence* on that single control.
- Anyone using `pgweb` / `redis-commander` on the shared host must now start them with the `tools` profile.
- Local development is unchanged: `BIND_IP` already defaulted to `127.0.0.1`.

## Verification

- **CI: all 7 checks pass** on head `9801f61` (lint/type/test, integration against PostgreSQL + Redis, scoped-app build, both CodeQL analyses, CodeQL, label).
- Re-checked today on this exact head, in a throwaway worktree with a dummy `.env`:
  - `docker compose config --services` renders `api celery-worker postgres qdrant redis` by default, and with `--profile tools` adds `pgweb` and `redis-commander`;
  - with `BIND_IP=127.0.0.1` **and** with `BIND_IP=0.0.0.0` the rendered bindings are: `api` follows `BIND_IP`; `postgres` 5432, `redis` 6379, `qdrant` 6333/6334, `pgweb` 8081 and `redis-commander` 8082 are all `127.0.0.1`; `celery-worker` publishes nothing;
  - every service renders `max-size=10m`, `max-file=3`;
  - `tests/repo/test_deployment_hardening.py`: 6 passed.
- At push time: 1,794 unit tests passed (this branch is based on `e065df9`, before #211's tests); ruff, format, mypy and the secret scan clean.
- Pinned tags were confirmed to exist (`docker manifest inspect`) before pinning.

## One thing to decide before merging: the Python base image

`python:3.12-slim` is a rolling tag. Checked on 2026-10-03, its digest is **identical to `3.12-slim-trixie` (Debian 13)**, while this PR pins **`-bookworm` (Debian 12)**. If the image currently deployed on the host was built from the rolling tag after it moved to trixie, this change will move the container from Debian 13 to Debian 12 on the next build, which this PR's description previously did not say. The deployed image's base was **not inspected** (nothing was read from the host for this). Options: accept bookworm (older and stable; the Dockerfile's apt packages have not been checked against it), or pin `-trixie` to keep what the rolling tag gives today. Either is a reproducibility improvement over `3.12-slim`; the question is only whether the OS version should change in the same PR.

## Not verified

- **Not deployed anywhere**, so the one-time datastore restart, the rebuild on Debian 12 (if that is a change) and the post-deploy prune have not run on the real host.
- The prune's effect on the real disk (about 17 GB was reclaimable) is an estimate from the audit, not a measurement of this change.
- Not fixed here: the host has no swap and the worker was OOM-killed under a six-incident burst (audit O-8, `OOMKilled=true`). That is a capacity decision for the team (swap, a lower `WORKER_CONCURRENCY`, or a larger instance), not something to change blind in a PR. Also not fixed: Qdrant still has no API key (it is now loopback-only, which is the mitigation).

## After merge

The deploy prints the disk line itself. Worth checking once on the host (read-only): `docker compose ps` shows the five default services healthy; `ss -ltn` shows 5432, 6379, 6333 and 6334 bound to `127.0.0.1` only; a test incident still completes end to end; `df -h /` trends down after the prune. **Rollback** is reverting this PR; that costs one more datastore restart.

## Relationship to #211

Independent: the two branches merge cleanly in either order (checked). #211 carries the audit and the application fixes; this PR carries only deployment configuration, and is separate because it restarts the datastores.
