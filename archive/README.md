# Archive

Earlier work kept for reference. Not part of the running system.

- `audit-2026-10-02/`: the system audit, its fixes as patches against the team base commit (`audit-fixes.patch`,
  `infra-hardening.patch`; a placeholder replaced one tunnel hostname, so they are for reading, not guaranteed to apply
  cleanly), the audit report and an operations runbook.
- `shared-instance-audit/`: read-only probing scripts, red-team exploration and notes from that audit.
- `servicenow-revert/`: scripts that restored a shared instance to its earlier state and verified it.
- `servicenow-research/`: ACL update-set XML, upload scripts and notes from researching the instance.

These scripts read credentials from a local env file (`BARQ_ENV_FILE`) and refer to hosts by placeholder.
