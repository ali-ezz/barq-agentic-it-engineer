# Inflow — business-focused presentation proposal

The purpose is to reduce incident engineers’ workload. Inflow assists with investigation, knowledge search and preparation of proposed resolution steps. Verification, human review and recovery support that purpose. They are supporting capabilities, not the main business problem.

Seven slides. Nine minutes including a two-minute demo, leaving one minute within the ten-minute limit. Proposed benefits describe the business objective; the project evidence does not yet quantify engineer time saved, staffing savings or production MTTR improvement.

## 1. Inflow — 0:30

### Slide wording
Inflow

Helping incident engineers investigate issues and prepare fixes

BARQ Systems × Sprints — Team 1

Ali Ezz, Mohamed Abdelaziem, Ahmed Tamer, Kerolos Mohsen, Tasneem Mohammed

### Spoken explanation
“We built Inflow to take on part of the investigation and preparation work involved in handling IT incidents. It works with ServiceNow and the knowledge base to give the engineer proposed steps and their supporting sources.”

### Design
A minimal dark cover with Inflow as the main identity and BARQ and Sprints alongside it. One brief fade introduces the project description. Avoid abstract decorative artwork.

## 2. Problem statement — 1:00

### Slide wording
Engineers spend time researching incidents and preparing fixes

Finding the right guidance and preparing a fix take work before anyone can act.

The groundwork behind a fix:
- Understand the incident
- Find relevant knowledge
- Prepare the next steps

### Spoken explanation
“Handling an incident involves more than applying a fix. The engineer first has to understand the reported issue, look for relevant guidance and work out the next steps. Our business objective is to reduce that manual preparation so engineers can give more attention to complex incidents and decisions that require their expertise.”

### Design
Light left side with a large problem statement. A contrasting navy area on the right shows the preparation work. Reveal each task as it is explained. Logos remain small and balanced along the bottom.

## 3. Our solution — 1:00

### Slide wording
Inflow gives the engineer a prepared starting point

A proposed fix in ServiceNow

Supporting knowledge articles

Review information when a human decision is needed

### Spoken explanation
“Inflow reads an eligible incident and searches the knowledge base. Its agents investigate the likely cause and prepare suggested steps. The engineer receives a proposed fix with sources, or a review brief when the incident cannot continue automatically. The intended benefit is less manual groundwork, with the engineer retaining responsibility for the actions they take.”

### Design
One enlarged real ServiceNow example with clearly readable suggested steps. Highlight the proposed response and its sources. The screenshot must match the scenario and recorded state; do not substitute a manually populated field fixture as evidence of an end-to-end run.

## 4. How Inflow supports the engineer — 1:30

### Slide wording
Inflow prepares a proposed fix so the engineer can focus on deciding what to do next.

1. Understand the incident — Classify the issue and assess risk.
2. Find relevant knowledge — Find guidance that matches the issue.
3. Prepare a proposed fix — Draft steps with supporting sources.
4. Support the next decision — Provide a suggestion or request review.

A proposed fix, with evidence, ready for the engineer.

### Spoken explanation
“ServiceNow triggers the workflow when an incident is eligible. Inflow assesses the risk first. Incidents that can continue go through knowledge search, diagnosis and resolution drafting. A separate critic checks the steps and can request a revision. The system writes the permitted suggestion or outcome to ServiceNow, or pauses for a human decision. That automation takes on preparation work while keeping review available where needed.”

### Design
A light, horizontal process with short descriptions and sequential builds. The final result appears in a navy band. Explain the high-risk branch before retrieval in the narration or a small branch in the final animated diagram. Do not imply that high-risk incidents proceed through automatic drafting or that every low-risk suggestion requires prior approval.

## 5. Demo — 2:00

### Slide wording
An incident becomes a proposed fix

Incident details

Suggested steps and their sources

Engineer review and the resulting update

### Spoken explanation
Use one verified incident to show the work Inflow performs for the engineer. Begin with the incident, show the relevant knowledge and prepared steps, then show the engineer’s decision and ServiceNow result. Use brief recorded segments for review, a blocked request and recovery if they fit clearly into the two-minute cut. Keep the more detailed demonstrations available for questions. Reconcile the final demo with the PRD’s required resolution, approval, guardrail and recovery scenarios.

### Design
A large Arcade demo with short captions and tightly cropped views. Supporting trace details belong in narration or question material. The mandatory MP4 is a separate deliverable and has not yet been created here.

## 6. Results — 1:30

### Slide wording
Rewriting helped find the right knowledge article in a local test

Expected article in the top five results:

Original incident — 8 of 23 cases

Rewritten query — 23 of 23 cases

Median retrieval time — 0.40 seconds versus 2.98 seconds

Local test with added noise. Production workload reduction has not been measured.

### Spoken explanation
“The business benefit depends on giving the engineer relevant guidance. In this local experiment, rewriting the noisy incident query increased the number of answerable cases where the expected article appeared in the top five, from eight to twenty-three out of twenty-three. It also added retrieval time. This is evidence about search behavior on this dataset. It is not a measurement of engineer time saved or production resolution accuracy.”

### Design
One native chart with the original result revealed first and the rewritten result second. Show the time comparison afterward. Keep the test scope visible. If a more representative team evaluation is used, verify the dataset and baseline before replacing this chart.

## 7. Business value and next steps — 1:30

### Slide wording
Less manual preparation for incident engineers

More attention for complex incidents

Next: measure engineer effort and resolution outcomes in a pilot

Thank you

### Spoken explanation
“Our goal is to reduce the time engineers spend assembling a proposed resolution. The system already performs investigation, search and drafting within the incident workflow. The next business test is to measure how much preparation it saves, how useful engineers find the suggestions and whether the complete workflow improves resolution outcomes. We would measure review effort alongside acceptance rates and time to resolution.”

### Design
Dark close connected to the cover. Present the intended benefits, then the pilot measurement plan. Do not present the benefits as established production savings.

## Transition approach
Short fades for most slide changes. Reveal the investigation work and workflow stages in order. Animate chart comparisons with the explanation. Use a smoother object transition for a repeated incident view only if the available tooling can create and play it correctly. The current PNGs are static design previews; these effects are planned, not implemented or tested.

## Source basis
Ali’s instruction establishes workload reduction as the main business framing. PRD-v2.0 sections 01 and 04 describe the platform and incident-engineer users; the feature list describes diagnosis, drafting, retrieval and review. The repository README and multi-agent/HITL design documents substantiate the supporting workflow. Retrieval figures come from docs/evidence/retrieval_query_ablation_noisy.json: 23 answerable cases and six unanswerable cases, with the chart using the answerable subset. No source presently establishes production staffing savings or MTTR improvement.
