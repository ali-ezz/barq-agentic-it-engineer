# Local-only branches of the team repository

Snapshot of my clone of the private team repository (`barq-sprints-agentic-incident-resolution-platform-g1`), 2026-11-21.
These 18 branches hold commits that exist on no remote branch. Only the commit subjects are listed (no authors, e-mail
addresses or hashes); the full history was kept as a git bundle on my machine that is not published, because it contains
teammates' personal e-mail addresses. Counts are commits not reachable from any remote branch.
"Unique" means commits reachable from no remote branch and from none of the other local-only branches; a branch with 0 unique
commits is only a combination of the others (a scratch merge or a copy).

| Branch | Commits not on a remote | Unique to this branch | Merge commits | Kind |
|---|---|---|---|---|
| `dependabot/uv/openai-3.16.2` | 1 | 1 | 0 | dependency bump |
| `dependabot/uv/redis-8.1.0` | 2 | 2 | 0 | dependency bump |
| `feat/retrieval-query-rewrite` | 11 | 11 | 2 | work branch |
| `feature/s1-1-ai-incident-field-model` | 22 | 22 | 0 | work branch |
| `fix/rejection-failed-state` | 1 | 1 | 0 | work branch |
| `fix/retrieval-clearance-ceiling` | 1 | 1 | 0 | work branch |
| `fix/s35-approved-solution` | 1 | 1 | 0 | work branch |
| `fix/sprint2-issue-sweep` | 16 | 16 | 2 | work branch |
| `pr159` | 30 | 30 | 2 | work branch |
| `pr161` | 1 | 1 | 0 | work branch |
| `pr30` | 23 | 23 | 3 | work branch |
| `revert/pr-169` | 1 | 1 | 0 | work branch |
| `review/pr138` | 3 | 3 | 0 | work branch |
| `scratch/combined` | 15 | 15 | 15 | scratch merge of other work |
| `scratch/combined-sprints-20260927` | 66 | 61 | 5 | scratch merge of other work |
| `scratch/s1-combined-20260919` | 11 | 11 | 11 | scratch merge of other work |
| `sim_b` | 5 | 0 | 1 | work branch (all commits also in other local branches) |
| `test-qdrant-119` | 2 | 2 | 1 | work branch |

Reading the table: `scratch/combined`, `scratch/s1-combined-20260919` and `scratch/combined-sprints-20260927` are throw-away integration
branches (their commits are mostly merges of other branches, so most of that work is also on the remote PR branches);
`sim_b` is a copy of work contained in other branches. The rest are my own work branches or dependency bumps, several of
them later merged upstream by squash (so the original commits no longer match any remote branch).

## `dependabot/uv/openai-3.16.2` (1 commits)

- chore(deps): bump openai from 2.54.0 to 3.16.2

## `dependabot/uv/redis-8.1.0` (2 commits)

- fix(api): narrow the DLQ range read across the sync/async redis clients
- chore(deps): bump redis from 5.2.1 to 8.1.0

## `feat/retrieval-query-rewrite` (11 commits)

- fix(cache): integrate governed incident reuse and durable approval waiters
- fix(deps): patch virtualenv activation-script vulnerability
- docs: verify final dependency stack and record merged updates
- Merge remote-tracking branch 'origin/main' into feat/retrieval-query-rewrite
- docs: refresh approval and trace evidence with semantic-cache main
- fix(retrieval): preserve complete query anchors within rewrite budget
- Merge remote-tracking branch 'origin/main' into feat/retrieval-query-rewrite
- feat: add measured article-level MMR diversity selection
- fix: stabilize retrieval approvals and dead-letter recovery
- fix: patch brace expansion in the SDK build lockfile
- feat: add query augmentation and preserve final reranker ordering

## `feature/s1-1-ai-incident-field-model` (22 commits)

- revert: restore confidence validation to the exported build
- Delay error message display for AI Confidence validation
- Rename validation script for AI confidence on change
- docs: align confidence test evidence
- docs: record first formal review outcome
- docs: address S1.1 review evidence and permissions
- docs: map S1.1 requirements to review evidence
- docs: finalize S1.1 acceptance checklist
- docs: complete secondary PDI verification record
- docs: verify imported application on secondary P AndersenDI
- docs: record clean secondary PDI commit
- docs: add clean secondary-PDI preview evidence
- docs: add processing-state choice evidence
- docs: add confidence validation evidence
- fix: preserve confidence validation error message
- docs: add populated Incident form evidence
- docs: record completed packaging checks
- feat: implement S1.1 scoped incident field model
- docs: adopt scoped Table Builder fast path
- docs: record confirmed S1.1 decisions
- docs: scaffold S1.1 ServiceNow field model
- Initial commit

## `fix/rejection-failed-state` (1 commits)

- fix: keep rejected incident attempts failed

## `fix/retrieval-clearance-ceiling` (1 commits)

- fix: let the agent reach restricted articles instead of reporting no evidence

## `fix/s35-approved-solution` (1 commits)

- fix: capture approved human solutions after no-evidence interrupts

## `fix/sprint2-issue-sweep` (16 commits)

- Resolve conflicts with #159: keep token-derived decided_by and the 404 (#147/#148), adopt the solution fold into evidence; align test fixtures with the shipped hybrid retrieval default (#150)
- merge main into fix/sprint2-issue-sweep (after #155, #157, #159)
- merge origin/main into fix/sprint2-issue-sweep
- docs: state the rerank latency cost the report actually shows (#150)
- docs: correct the README's sprint claims and the CI badge link (#36)
- docs: make every relative link in tracked markdown resolve (#36)
- fix: repository secret scan that actually scans (#51)
- docs(s2.1): record the live S1.3 -> webhook proof for #137
- fix(api): accept S1.3 events that carry no contract_version (#137)
- fix(api): split operator and ServiceNow credentials, make approvals immutable (#136, #147, #148, #51)
- fix(scripts): fail closed in verify_permissions when a result cannot be read (#46)
- docs(sdk): state the keys.ts check in a form a reader can reproduce
- fix(deps): close the four Dependabot alerts in the ServiceNow SDK lockfile
- ci: run the integration suite against real PostgreSQL and Redis (#149)
- fix(eval): make the retrieval report match its data and correct the rerank limit check (#150)
- docs: match the README layout to the tree and bring Sprint 1 status up to date (#36)

## `pr159` (30 commits)

- Merge branch 'main' into feat/s3-5-knowledge-capture
- style: sort test imports
- test(publishing): read-back verification fails closed
- docs(s3.2): S3.5 write-back registration complete in traceability
- chore: format and pass full just check suite
- docs(evidence): record live end-to-end loop closure for INC0010120
- docs(evidence): update demo transcript from live user run
- feat(schemas): accept human_solution as an alias for solution
- fix(demo): live PDI approval gate and record demo transcript
- docs(s3.5): live demo runbook with the approval-endpoint decision step
- test(s3.5): rubric-named sparse-input and double-ingest cases
- docs(evidence): live loop-closure demo script
- docs(s3.5): knowledge capture design and drift matrix
- test(loop): escalated knowledge retrievable for the next incident
- feat(agent): knowledge capture with drift-safe ordering
- test(agent): capture orchestrator rules (red)
- feat(publishing): register guarded KB write-back tool
- test(publishing): guarded KB write-back gate (red)
- feat(agent): compose human solutions into structured KB articles
- test(agent): composer faithful, fabrication flagged (red)
- feat(schemas): accept human solution in approval decisions
- test(schemas): solution field accepted, distinct from reason (red)
- Merge remote-tracking branch 'origin/main' into feature/s3-2-tool-registry
- docs(s3.2): clarify sync-to-async tool bridge
- fix(s3.2): harden registry security boundaries
- docs(s3.2): document tool registry security model
- feat(s3.2): enforce registry-only graph tool access
- feat(s3.2): add post-refusal explanation flow
- feat(s3.2): register ServiceNow tools with permission classes
- feat(s3.2): add server-side tool registry enforcement

## `pr161` (1 commits)

- chore(deps-sdk): bump @servicenow/sdk

## `pr30` (23 commits)

- fix(s1.3): scope-prefix the categories property so the imported rules can read it
- fix(s1.3): treat a whitespace endpoint as unset and drop the unused Default GET
- docs(s1.3): move deliverables into the sprint folder and record the deploy hazard
- fix(tests): remove stale scripts/verification_report.json from PLANNED
- Merge branch 'main' into feature/s1-3-eligibility-business-rule
- fix: Remove S1.4 KB publishing entries from planned paths
- style: format path config drift test
- merge main and preserve S1.3 path config fix
- fix(ci): align S1.3 export checks
- merge main into feature/s1-3-eligibility-business-rule
- fix(s1.3): sync final PDI behavior and update set
- chore(s1.3): clean up obsolete scaffold files
- docs(s1.3): clarify outbound OAuth status
- docs(s1.3): strengthen performance evidence
- fix(s1.3): align supported categories with knowledge corpus
- fix(s1.3): improve suppression tracing and legacy lock handling
- fix(s1.3): externalize outbound endpoint
- docs(s1.3): add performance evidence
- feat(s1.3): eligibility business rule and outbound event
- Add S1.3 minimal incident event contract
- Implement S1.3 incident eligibility rule
- Add S1.3 eligibility scaffold
- Add S1.3 documentation scaffolding

## `revert/pr-169` (1 commits)

- Revert knowledge base enrichment merge (#169)

## `review/pr138` (3 commits)

- fix(cd): make EC2 deployments fail closed
- fix(cd): execute alembic directly in api container
- ci(cd): add automated deployment workflow to EC2 on main push

## `scratch/combined` (15 commits)

- Merge remote-tracking branch 'origin/fix/kb-publisher-identity' into scratch/combined
- Merge remote-tracking branch 'origin/fix/s1-3-outbound-oauth' into scratch/combined
- Merge remote-tracking branch 'origin/fix/s1-3-single-source' into scratch/combined
- Merge remote-tracking branch 'origin/fix/s1-2-clean-install' into scratch/combined
- Merge remote-tracking branch 'origin/feat/kb-fields-in-fluent' into scratch/combined
- Merge remote-tracking branch 'origin/docs/field-model-lock-roles-and-retry-count' into scratch/combined
- Merge remote-tracking branch 'origin/fix/incident-cross-write-and-typed-parse-errors' into scratch/combined
- Merge remote-tracking branch 'origin/docs/review-dismissal-rule' into scratch/combined
- Merge remote-tracking branch 'origin/chore/pin-qdrant-client-to-server' into scratch/combined
- Merge remote-tracking branch 'origin/fix/live-acl-test-no-skip' into scratch/combined
- Merge remote-tracking branch 'origin/docs/layout-and-sprint-status' into scratch/combined
- Merge remote-tracking branch 'origin/fix/verify-permissions-fail-closed' into scratch/combined
- Merge remote-tracking branch 'origin/fix/kb-publish-403-swallow' into scratch/combined
- Merge remote-tracking branch 'origin/chore/dependabot-grouping' into scratch/combined
- Merge remote-tracking branch 'origin/fix/s1-3-tests-in-ci' into scratch/combined

## `scratch/combined-sprints-20260927` (66 commits)

- Reject mixed shared and local KB loop evidence
- Compare shared ServiceNow host exactly in demo guard
- Prevent local replay harness from duplicating shared incidents
- Prevent premature approval note in local demo
- Keep approval resume spans in the original execution trace
- Document reproducible local demo setup
- Verify combined Sprint 3 demo and isolate OCR test dependency
- Integrate manual knowledge enrichment with HITL branch
- Merge Sprint 3 guardrails into HITL branch
- test(workers): wait for DLQ record write to eliminate integration test flake
- fix(ci): install poppler-utils in workflow, skip pdf test when absent, and fix docs link
- fix(eval): enforce strict score validation, complete coverage for acceptance, and safety error accounting
- fix(publishing): preserve prior attempt history in publication journal upon retry
- feat(retrieval): propagate provenance and reliability through RetrievalHit to EvidenceItem
- fix(agent): prevent reference-only evidence from authorizing active resolution steps
- fix(eval): enforce metric floors, complete accounting, and gate failures on retrieval/judge errors
- fix(eval): validate compound forbidden labels and refusal turn safety constraints
- feat(knowledge): preserve full provenance and OCR reliability in KnowledgePayload
- fix(publishing): persist manual publication report incrementally on each article outcome
- fix(reconciliation): preserve active versions when superseding specific article revisions
- fix(agent): protect procedure generation from historical and warned evidence
- fix(deploy): keep deploy script isolated from missing container scripts and preserve data
- ci(deploy): add Qdrant knowledge base seeding to CD pipeline
- docs(manual): operator runbooks for validation, release and recovery
- fix(test): isolate mock_settings from SERVICENOW_KB environment variables
- feat(eval): add --skip-ingest flag and configure Gemini judge via LiteLLM
- fix(kb): prevent ServiceNow Table API 403 on prefix search and fix wide search work notes
- feat(eval): Stage A RAGAS runner for the 87 answerable turns
- feat(manual): publish manifest units through the existing publisher
- feat(agent): manual evidence reaches the incident retriever
- feat(manual): publication units ingest through the article pipeline
- fix(manual): close three review gaps in manifest and coverage
- docs(manual): manifest review record pending owner sign-off
- style: reflow comments and reformat files flagged by lint
- feat(manual): lifecycle-aware KB manifest and section adapter
- fix(manual): refine section detection and recover section 6.12
- test: drop reflection padding, harden deploy gate to step level
- test(eval): drop the input hash pins
- feat(manual): extract, cover and hash-pin the committed PDF
- test(manual): extraction coverage is explicit, never silent
- feat(eval): Stage A dataset contract and retrieval-only loader
- test(eval): pin the 100-turn dataset contract
- fix(capture): enforce the KB1001–KB1999 human-capture range
- test(capture): allocator stays inside KB1001–KB1999
- fix(seed): manual sections are opt-in with a separate target
- test(seed): manual sections need an explicit separate target
- fix(seed): never purge live knowledge; verify by point IDs
- test(seed): seeding must not destroy other knowledge
- chore(eval): track barq eval dataset and adapters
- test(eval): demand tracked barq eval inputs
- Enforce the approval-brief timeout the module already declared
- Sarah's S3.4 review: routing-independence test, the NO_EVIDENCE rationale, and trace-continuity evidence
- Bring the roadmap's Sprint 3 and Sprint 4 scope in line with what shipped
- Forbid unknown fields on the incident write payload
- Correct the documentation against the code, and document the API failures
- Refresh the S3.4 live transcript against the fixed code
- Merge branch 'main' into feat/s3-4-hitl-interrupt
- S3.4: close four defects found reviewing the HITL path, and add a live demo
- chore(agent): stamp the graph as s3.4 in every audit row
- docs(readme): add the Sprint 2 and Sprint 3 status tables
- merge main into feat/s3-4-hitl-interrupt after #160 (11-issue sweep)
- fix(s3.4): close the write-boundary race the review flagged
- Adapt the S3.4 resume path to #157's async tool bridge: run the graph resume and the test parking helper off-loop, adopt the solution fold into evidence
- merge main into feat/s3-4-hitl-interrupt (after #155, #157, #159)
- fix(s3.4): three defects found by a live end-to-end run
- feat(agent): true LangGraph interrupt/resume with approval audit (S3.4)

## `scratch/s1-combined-20260919` (11 commits)

- Merge remote-tracking branch 'origin/fix/kb-publisher-identity' into scratch/s1-combined-20260919
- Merge remote-tracking branch 'origin/fix/kb-publish-403-swallow' into scratch/s1-combined-20260919
- Merge remote-tracking branch 'origin/fix/s1-3-outbound-oauth' into scratch/s1-combined-20260919
- Merge remote-tracking branch 'origin/fix/s1-3-single-source' into scratch/s1-combined-20260919
- Merge remote-tracking branch 'origin/fix/s1-2-clean-install' into scratch/s1-combined-20260919
- Merge remote-tracking branch 'origin/feat/kb-fields-in-fluent' into scratch/s1-combined-20260919
- Merge remote-tracking branch 'origin/docs/field-model-lock-roles-and-retry-count' into scratch/s1-combined-20260919
- Merge remote-tracking branch 'origin/docs/layout-and-sprint-status' into scratch/s1-combined-20260919
- Merge remote-tracking branch 'origin/fix/verify-permissions-fail-closed' into scratch/s1-combined-20260919
- Merge remote-tracking branch 'origin/chore/pin-qdrant-client-to-server' into scratch/s1-combined-20260919
- Merge remote-tracking branch 'origin/chore/dependabot-grouping' into scratch/s1-combined-20260919

## `sim_b` (5 commits)

- fix(s3.4): close the write-boundary race the review flagged
- Adapt the S3.4 resume path to #157's async tool bridge: run the graph resume and the test parking helper off-loop, adopt the solution fold into evidence
- merge main into feat/s3-4-hitl-interrupt (after #155, #157, #159)
- fix(s3.4): three defects found by a live end-to-end run
- feat(agent): true LangGraph interrupt/resume with approval audit (S3.4)

## `test-qdrant-119` (2 commits)

- Merge remote-tracking branch 'origin/main' into test-qdrant-119
- chore(deps): bump qdrant-client from 1.14.3 to 1.19.0

