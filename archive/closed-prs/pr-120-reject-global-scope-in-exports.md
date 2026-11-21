# PR 120: test(servicenow): fail the build on new Global-scope records in an export

Private team repository `barq-sprints-agentic-incident-resolution-platform-g1`, authored by me. **Closed, not merged.**

- State: CLOSED (never merged)
- Base: `main`
- Head branch: `test/reject-global-scope-in-exports`
- Opened: 2026-09-16T16:10:08Z; closed: 2026-09-16T19:53:28Z
- Size: +88 / -0 in 1 files
- Diff: `pr-120-reject-global-scope-in-exports.diff` (plain `git diff`-style, no author data)


## Description (as written on the PR)

Advances #48. The remaining half needs work on the PDI — see below.

## Confirmed, by parsing the exports

| Export | Scopes found |
|---|---|
| `s1_1.xml` | 22 × AI Incident Orchestrator — **clean** |
| `s1_2.xml` | 76 × AI Incident Orchestrator, **5 × Global** |
| `s1_3.xml` | 17 × AI Incident Orchestrator — **clean** |

The five:

```
sys_security_acl_a2a3e94e...  sys_journal_field create
sys_security_acl_7fa32d4e...  sys_journal_field read
sys_security_acl_91b7ec2c...  incident.* write
sys_security_acl_66f0fbc6...  incident.comments write
sys_script_2f5038f9...        "AI Enforce Human Lock Safety Stop" (added by #32)
```

Exactly the four #48 lists, **plus the business rule it predicted #32 would add.**

## Why "0 global leaks" was claimed in #29

`sys_scope` lives inside each `sys_update_xml`'s **`<payload>` CDATA**. Scanning the outer document — a grep, or an ElementTree pass over the file — finds **nothing at all**. You have to parse each payload as XML in its own right. That's how this drifted unnoticed, and it's why the check is a test rather than a grep in a workflow step.

## What this PR does, and does not do

**Does not:** remove them. That means restoring the baseline ACLs on the instance, rebuilding the lock rule inside `x_2215032_ai_inc_0`, and re-exporting — instance work, owned by @MohamedAbdelaiem.

**Does:** stop the set growing. The five are listed with the issue tracking them; **anything else in Global fails the build.**

## It's a ratchet, not a permission slip

A second test fails if a listed record is **no longer present** in any export — so a fixed record must be *deleted* from the list, not left behind to silently re-permit itself if it ever returns. When the list empties, it gets replaced by a plain assertion of zero.

There's also a guard asserting the exports were found at all, so a rename can't turn this into a vacuous pass.

## Verified both directions

```
# A new Global record appears:
AssertionError: New Global-scope records in an exported update set:
{'ai_incident_orchestrator_s1_2.xml': ['sys_script_2f5038f9...']}

# A listed record is fixed but the entry is left behind:
AssertionError: These are no longer in any export, so remove them from
KNOWN_GLOBAL_RECORDS: ['sys_script_already_fixed_on_pdi']
```

`349 passed, 11 skipped`; ruff, format and mypy clean.

## Checklist

- [x] No credential added, including in `.env.example`
- [x] Internal choice values used, never display labels
- [x] Nothing added in Global scope — this PR is the check for it
- [x] Docs updated if behaviour changed — rationale is in the module docstring
