# Inflow — proposed Demo Day storyboard

Seven slides. Planned duration: 9 minutes, including a 2-minute demo. One minute remains inside the 10-minute presentation limit for pauses and presenter handover. This is a proposal for wording and design, not a finished presentation.

## 1. Inflow — 0:30

**On the slide**

Inflow

AI assistance for incident resolution in ServiceNow

Team 1 — BARQ Systems × Sprints

Ali Ezz, Mohamed Abdelaziem, Ahmed Tamer, Kerolos Mohsen, Tasneem Mohammed

**What we say**

“We built Inflow to help engineers work through IT incidents in ServiceNow. It finds relevant knowledge, prepares a proposed fix and checks its supporting evidence. When the incident needs a human decision, it pauses and presents the information for review.”

**Design and motion**

Dark opening slide. Inflow is the main visual. BARQ and Sprints appear alongside it with balanced proportions. The project description appears once. A brief fade introduces the team names.

## 2. Problem statement — 1:00

**On the slide**

An AI answer still needs an engineer’s judgement

Before acting on a suggested fix, an engineer needs to know where it came from and when to stop.

Example incident: “My VPN stopped working after I changed my password.”

Does the guidance match this incident?

Can this action proceed, or does it need approval?

**What we say**

“An incident description gives us a starting point, but it is not enough to justify a fix. The suggested steps need to match the incident and the supporting knowledge article. Some incidents also need a human decision before the workflow can continue. Our challenge was to make those checks part of the system, and to keep a record of what happened even if processing stops or a worker restarts.”

**Design and motion**

Light background. One large problem statement on the left and one clearly labelled illustrative incident on the right. The incident and the two questions appear in sequence. Main wording stays visible.

## 3. Our solution — 1:00

**On the slide**

Inflow prepares a proposed fix inside the incident workflow

Relevant knowledge articles

Suggested steps with citations

Human review when required

**What we say**

“Inflow starts from an eligible ServiceNow incident. It searches the knowledge base, uses separate agents to diagnose the issue and draft the steps, and checks those steps against the cited evidence. The incident receives the permitted suggestion or outcome. If the risk or other checks require review, the workflow pauses for the engineer’s decision.”

**Design and motion**

One enlarged, verified ServiceNow example. Highlight the suggestion and its citation as they are explained. Avoid a full-screen interface with unreadable details. The screenshot must be from the real project and accurately labelled.

## 4. How Inflow handles an incident — 1:30

**On the slide**

The system checks the incident, prepares a proposed fix, and routes it according to the review rules.

1. Check the incident — Check eligibility and risk.
2. Find relevant guidance — Find matching knowledge articles.
3. Draft and verify steps — Check each step against its source.
4. Update or request review — Write a suggestion or ask for review.

High-risk incidents leave the automated path before knowledge search.

**What we say**

“ServiceNow sends an event, and the backend accepts it without waiting for the model. A background worker handles the incident. Risk checks happen before knowledge search. For incidents that can continue, the diagnostic agent identifies a likely cause, the resolution agent proposes steps, and the critic checks the evidence and can request a revision. Review outcomes pause the workflow. The stored execution lets it continue after the human decision without starting a new incident run.”

**Design and motion**

A simple horizontal process with four stages. Reveal each stage on a click. Add the early human-review route as the risk check is explained. Keep detailed infrastructure names in the spoken explanation rather than turning the slide into a list of products.

## 5. Demo — 2:00

**On the slide**

An incident in ServiceNow

Proposed steps and supporting knowledge

A human decision and the resulting update

**What we say and show**

Follow a real incident from creation to the suggested steps, then show a recorded review path and the result in ServiceNow. Include short, accurately labelled evidence of a blocked request and recovery after interruption. Use recorded clips to avoid consuming the slot waiting for model calls. The final cut must fit two minutes. If all required scenarios cannot be shown clearly within that cut, select the principal flow for the live portion and retain the other verified demonstrations for questions.

**Design and motion**

The demo occupies most of the slide. Short captions identify the stage. Avoid small trace screenshots. Arcade MP4 creation is a separate required deliverable; these previews do not contain a video.

## 6. Retrieval results — 1:30

**On the slide**

Rewriting helped retrieval in a local noisy-query test

Expected article in the top five results

Original incident: 8 of 23 cases

Rewritten query: 23 of 23 cases

Median retrieval time: 0.40 seconds versus 2.98 seconds

Local test with added noise. These results do not measure production resolution accuracy.

**What we say**

“We tested whether rewriting a noisy incident description would help the search find the expected article. In this local test, the original descriptions found it in eight of twenty-three answerable cases. Rewritten queries found it in all twenty-three. The additional model call increased median retrieval time from about four-tenths of a second to almost three seconds. This shows a useful trade-off in this test, not a claim about production accuracy or how quickly an engineer resolves an incident.”

**Design and motion**

One editable two-bar chart. Reveal the original result, then the rewritten result. Show the timing comparison afterward. Keep the experimental scope visible. Other evaluation findings can replace this example only after their dataset, baseline and measurements are checked.

## 7. Challenges and next steps — 1:30

**On the slide**

Better search takes additional time

Human review must survive an interrupted run

Next: test more incident types and measure the complete workflow

Thank you

**What we say**

“Two challenges shaped the implementation. Improving search can require another model call, so retrieval quality and latency need to be measured together. Human review also has to survive interruptions while preserving the decision and preventing duplicate actions. Our next step is to test a broader set of incidents and measure the full workflow, including the cases where the system should ask for help. Thank you.”

**Design and motion**

Dark closing slide related to the opening, without abstract decorative artwork. Two short lessons appear one at a time, followed by the next step and the close.

## Animation and transition direction

Use short fades for most slide changes. Use sequential builds to explain the workflow and the chart. Reserve a smoother object transition for a repeated incident example if the available tooling can produce it correctly. Effects are planned here, not yet implemented or tested. Avoid animated paragraphs, decorative spinning objects and automatic advance during speaking.

## Source basis

- DOCS/reference/PRD-v2.0-agentic-incident-resolution-platform.docx: problem, users, goals and Demo Day acceptance criteria.
- DOCS/reference/BARQ System Knowledge Base Manual.pdf: KB0001 and operational context. The VPN quotation is an illustrative paraphrase, not a quoted real caller.
- Team repository README.md, docs/sprint3_multi_agent_design.md and docs/sprint3_hitl_design.md: workflow, agent roles and review semantics.
- Team repository docs/evidence/retrieval_query_ablation_noisy.json: retrieval comparison. The dataset contains 23 answerable cases and six unanswerable cases; the chart uses the answerable cases.
- Supplied Demo Day agenda and preparation message: 5–7 slides, 10 minutes including demo, maximum two presenters, PPTX and Arcade MP4 submission.

These sources support the proposed content. A completed deck still needs verified screenshots, the final video, effect implementation and inspection in the presentation application.
