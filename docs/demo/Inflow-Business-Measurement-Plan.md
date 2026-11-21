# Inflow business measurement plan

Proposed pilot protocol. No measured business savings are claimed yet.

## Comparison

Compare engineers handling incidents with their current workflow against engineers using Inflow’s cited proposals. Match incident category, priority, complexity and engineer experience. Use comparable knowledge access in both groups. Agree the pilot duration, sample size and success thresholds before starting; do not choose them after seeing the results.

## Record for every incident

Incident identifier; cohort; category; priority; complexity; engineer; opened and confirmed-resolution times; active investigation, search, drafting, review and correction minutes; whether a proposal was reviewed and marked useful; whether it was used; model cost; allocated infrastructure cost; outcome; seven-day reopen status. Use synthetic or anonymized identifiers in presentation materials.

## Business scorecard

| Measure | Calculation | Interpretation |
|---|---|---|
| Preparation effort | Median active investigation + search + drafting + review + correction minutes per incident | Compare both cohorts. Include the effort of unsuccessful incidents. Keep waiting time separate. |
| Effort reduction | (Baseline median − assisted median) ÷ baseline median × 100 | Calculate only when baseline is greater than zero. Report both medians and cohort sizes alongside the percentage. |
| Useful-proposal rate | Proposals engineers mark useful ÷ all reviewed proposals × 100 | Report review coverage too. Usefulness and acceptance do not establish successful resolution. |
| Cost per resolved incident | Total engineering cost + model cost + allocated infrastructure cost, divided by confirmed resolved incidents | Convert active engineer minutes using an agreed hourly rate. Include unsuccessful attempts in total costs. Apply the same cost boundary to both cohorts. |
| Time to resolve | Confirmed resolution time − opened time | Report median and p95 separately from active engineer effort. |
| Reopen rate | Incidents reopened within seven days ÷ resolved incidents with a complete seven-day follow-up × 100 | Compare like categories and priorities. Exclude incidents lacking complete follow-up from this denominator. |

Engineering capacity released, if effort falls: mean active minutes saved per comparable incident × eligible monthly incident volume ÷ 60. Label this a projection and state the observed sample and assumed volume. Do not equate released capacity to layoffs or cash savings.

## Decision

Expand only when the agreed effort or cost threshold is met, proposal usefulness is acceptable and resolution time, reopen rate and safety have not worsened beyond agreed tolerances. Report sample sizes, missing data and variability. Investigate weaker incident categories before expanding them. Keep system latency, load tests and approval tests as supporting technical evidence, separate from business benefit.

## Adoption and scaling

Configure the business’s ServiceNow integration, knowledge, service permissions and review rules. Validate a limited category using the scorecard. Expand categories and teams after pilot evidence supports it. Other ticket platforms need a new connector and equivalent security/write-back validation.

Scale queued processing after load testing. Before adding worker replicas, separate Celery beat into one scheduler service and remove fixed worker naming. Validate model quotas, datastore capacity, duplicate processing, recovery, queue delay and cost. Initial business deployments can be isolated; shared multi-tenant operation is not claimed as built.

Sources: project README, PRD v2.0 and docker-compose.yml. Queue-worker scaling considerations: https://learn.microsoft.com/en-us/azure/architecture/patterns/competing-consumers. The business evaluation protocol above is a proposed measurement design, not an observed project result.
