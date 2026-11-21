# PR 215: Override node-gyp, livereload and fflate in the SDK build toolchain

Private team repository `barq-sprints-agentic-incident-resolution-platform-g1`, authored by me. **Closed, not merged.**

- State: CLOSED (never merged)
- Base: `main`
- Head branch: `fix/sdk-audit-overrides`
- Opened: 2026-10-03T03:10:36Z; closed: 2026-10-03T03:28:19Z
- Size: +75 / -982 in 3 files
- Diff: `pr-215-sdk-audit-overrides.diff` (plain `git diff`-style, no author data)

Dependency/lockfile change for the ServiceNow SDK build; one third-party package-author e-mail address in the lockfile diff is masked as `<npm-author-email>`.

## Description (as written on the PR)

## Why

Three advisories published 2026-09-18 made **Audit the build toolchain** in the ServiceNow SDK workflow fail on every PR (19 vulnerabilities, 16 high). npm's only offered remedy is `@servicenow/sdk` 4.13.3, which the 4.8.0 pin (#54 / #161) rules out.

## What

None of the vulnerable leaves has a patched release, so the packages that pull them in are overridden instead (SDK stays at 4.8.0):

| Override | Effect |
|---|---|
| `node-gyp` `^13.1.0` (was 11.5.0) | 13.x drops `make-fetch-happen`, removing `http-cache-semantics` (GHSA-ch52-4w7c-c8xp, no fix) |
| `livereload` `^0.10.3` (was 0.9.3) | 0.10.x uses `chokidar` 4, removing one `braces` path |
| `fflate` `^0.8.3` (was 0.8.2) | GHSA-px8p-9vwx-vf98 fixed; same version SDK 4.13.3 pins |

Result: **19 → 9 vulnerabilities (9 high, 0 moderate).** The README section on build-toolchain advisories records it.

## Still failing — on purpose

The audit step **stays red**. The remaining nine highs are one chain: `@servicenow/sdk-build-core` pins `fast-glob` 3.3.3 → `micromatch` → `braces` (GHSA-vfj7-8cjw-p6xm, CVE-2026-93687, `<=3.0.3`). Every `fast-glob`/`micromatch` release depends on `braces`, 3.0.3 is the latest `braces`, and the upstream fix (micromatch/braces#72) is unmerged. SDK 4.13.3 pins the same `fast-glob` 3.3.3, so upgrading would not help either. The audit level is not lowered and no step is skipped; when a fixed `braces` is released, one more override line turns the step green.

## Verified locally (Node 22.23.3)

- `npm audit --package-lock-only --audit-level=high` → 9 high, all on the `braces` chain
- `npm ci` → ok (node-gyp 13.1.0, livereload 0.10.3 installed)
- `npx now-sdk build --frozenKeys` → exits 0; `git status` clean afterwards (`keys.ts` unchanged)
- `npm test` → 28/28 pass
- `python3 .github/scripts/check_build_matches_export.py` → all records match the exports
