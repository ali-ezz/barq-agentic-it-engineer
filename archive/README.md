# Archive

Earlier work kept for reference. Not part of the running system.

- `audit-2026-10-02/`: the system audit, its fixes as patches against the team base commit (`audit-fixes.patch`,
  `infra-hardening.patch`; a placeholder replaced one tunnel hostname, so they are for reading, not guaranteed to apply
  cleanly), the audit report and an operations runbook.
- `shared-instance-audit/`: read-only probing scripts, red-team exploration and notes from that audit.
- `servicenow-revert/`: scripts that restored a shared instance to its earlier state and verified it.
- `servicenow-research/`: ACL update-set XML, upload scripts and notes from researching the instance.
- `closed-prs/`: my pull requests on the private team repository that were closed without merging, each as a description
  (`pr-N-*.md`) and a plain diff (`pr-N-*.diff`): #214 (the agentic ServiceNow platform branch; 91.8 % of its added lines are
  in `code/`, only the dropped Streamlit chat UI is not), #215 (SDK build-toolchain overrides), #181, #179, #176 and #120
  (small fixes and doc notes). The two audit PRs, #211 and #212, are under `audit-2026-10-02/` (patches and descriptions).
- `local-only-branches.md`: the commit subjects of the 18 branches that exist only in my clone of the team repository.

These scripts read credentials from a local env file (`BARQ_ENV_FILE`) and refer to hosts by placeholder.

## Other repositories (what is, and is not, here)

- `team-repo-stash0.patch`: the one unfinished change that sat in my clone of the team repository (a one-line
  whitespace edit to `scripts/verify_permissions.py`). Apply it, if you ever want it, on the team repository with `git apply archive/team-repo-stash0.patch`.
- My local-only branches from the team repository (18 branches, listed by commit subject in `local-only-branches.md`; mostly dependency bumps, scratch merges and branches whose
  content was later merged upstream by squash) were saved as a git bundle on my machine
  (`team-repo-local-only-branches.bundle`, 2.8 MB, thin: it needs the team repository's `main` to restore). It is **not published**:
  the commit history contains the team's personal e-mail addresses and old deployment details. To restore it locally:
  `git clone <team repo> && cd <team repo> && git fetch /path/to/team-repo-local-only-branches.bundle 'refs/heads/*:refs/heads/bundle/*'`.
- The worktrees of my working copy (`barq-agentic`, `barq-sdk-audit`) were clean; their branches are already in the team repository or contained here.
