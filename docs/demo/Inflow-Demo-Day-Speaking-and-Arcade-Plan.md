# Inflow Demo Day plan

## Event and submission

The organizer’s supplied messages specify Tuesday, 6 October 2026 at Sprints, Villa 2, Street 212, Degla Square, Maadi. Arrive from 09:30 Cairo. The event starts by 10:00 and runs until 13:00. Dress code: formal to semi-formal.

The submission deadline is Saturday, 3 October 2026 at 23:59 Cairo. Required files: PPTX presentation and an MP4 demo made with Arcade. One or two presenters maximum. The ten-minute pitch includes the video. The detailed event agenda and submission link were not included in the supplied messages.

## Presenter timing

The timings below total exactly ten minutes. For two presenters, use a single handover after slide 7. For a solo presenter, keep the same order.

| Slide | Section | Time |
|---|---|---|
| 1 | Inflow | 0:15 |
| 2 | Our team | 0:30 |
| 3 | Problem | 1:00 |
| 4 | Solution | 1:00 |
| 5 | Goals and users | 0:45 |
| 6 | How it works | 1:15 |
| 7 | Tools and technologies | 0:45 |
| 8 | Demo | 2:00 |
| 9 | Results and impact | 1:00 |
| 10 | Challenges and lessons | 0:45 |
| 11 | Next steps | 0:30 |
| 12 | Close and Q&A | 0:15 |

## Arcade recording plan

Create a 100-second Arcade walkthrough, leaving ten seconds to introduce it and ten seconds to explain the outcome within the two-minute demo slot.

1. **0–25 seconds: employee report.** Describe Wi-Fi dropping on the corporate 5 GHz network, then open the proposed ticket.
2. **25–60 seconds: agent response.** Show the incident conversation and the message that the network team has the ticket with the proposed steps.
3. **60–100 seconds: engineer handoff.** Show the engineer page, the cited knowledge and who is in control. End on the handoff.

Record the real shared-system demo with approved demo accounts and labelled test data. Use the same ticket across all scenes. Keep waits out of the walkthrough or label an edited wait. Do not claim that routing the ticket has repaired the Wi-Fi. Export an MP4 from Arcade and test offline playback before submission.

**Video status:** No Arcade project or MP4 was supplied. The deck contains a recorded screenshot, and the MP4 still needs to be recorded and exported. Do not submit the screenshot as the requested video.

## Slide speaking notes

### 1. Inflow

15 seconds. Inflow is our Agentic Incident Resolution Platform for ServiceNow. It uses company knowledge to work an incident, with people in control when a decision needs review. Introduce the project and move directly to the team.

### 2. Our team

30 seconds. We are Ali Ezz, Mohamed Abdelaziem, Ahmed Tamer, Kerolos Mohsen and Tasneem Mohammed. Our work spans orchestration and retrieval, identity and logging, incident events and tool permissions, knowledge ingestion, and ServiceNow integration. Aya Ashraf is our mentor and reviewer. The labels summarize contribution areas, with shared ownership of the finished workflow. One presenter can deliver the full pitch. With two presenters, Presenter 1 handles slides 1–7 and Presenter 2 handles slides 8–12.

### 3. Problem

60 seconds. Before an engineer fixes a ticket, they need to understand the symptoms, find the right procedure and prepare a response. When many people report the same outage, that investigation repeats. An AI response also needs more than a plausible answer: it needs company evidence and permission to act. Our project addresses that preparation and coordination work. We have not measured a manual support-time baseline, so this slide makes no percentage claim.

### 4. Solution

60 seconds. Inflow begins with the incident and its conversation. It asks for missing details when appropriate, retrieves company procedures and checks the proposed fix. It can update, assign or resolve an eligible caller-doable case within its configured boundaries. Cases that require an engineer or approval stay with a person. Qualifying human resolutions can become knowledge for future retrieval. Ticket resolution means the workflow supplies a caller-doable fix and asks for confirmation. It does not prove a repaired device or restored infrastructure.

### 5. Goals and users

45 seconds. Employees can describe an issue and follow its conversation. Engineers receive the proposed steps and sources, and can take over or hand work back. Approvers decide cases that require human review. Our goals are less repeated investigation, grounded fixes, traceable handovers and reusable company knowledge. A measured support-team pilot is still needed to quantify time and cost benefit.

### 6. How it works

75 seconds. ServiceNow sends an eligible incident or conversation event. FastAPI accepts it and queues the work through Redis and Celery. Workers load the incident and conversation, validate eligibility, classify the issue and assess risk. Eligible cases proceed to retrieval, diagnosis, generation, evidence verification, safety and confidence checks. Some cases route directly to an action or review before retrieval. The action step can ask the caller, assign a group, supply a permitted fix or pause for approval. PostgreSQL stores workflow state, Qdrant supports knowledge search and Langfuse records traces. Engineer decisions and the employee page reach the backend through a ServiceNow server-side bridge. This is a simplified presentation of the graph, not a promise that every ticket runs every node. Sources: src/agent/graph.py, src/agent/nodes/act.py and docs/barq_agentic_system.md.

### 7. Tools and technologies

45 seconds. ServiceNow is the user and engineer workspace. Python and FastAPI provide the event and operator APIs. Redis and Celery run background work. LangGraph coordinates the agent workflow and resumable reviews. Qdrant retrieves knowledge and PostgreSQL stores state and audit records. Langfuse helps inspect model activity and workflow traces. These tools are verified in the project files. Do not state an exact model, current price or production scaling limit without a separate check.

### 8. Demo

120 seconds total, including the video. Introduce the journey in 10 seconds: an employee reports Wi-Fi dropping on the corporate 5 GHz network. Play a 100-second Arcade MP4, then use 10 seconds to explain the handoff. Scene 1, 0–25 seconds: employee describes the problem and opens the ticket. Scene 2, 25–60 seconds: show the ticket conversation and the agent's message that the network team now has it. Scene 3, 60–100 seconds: open the engineer view, show the cited steps and who is in control. End on the handoff, not an unsupported claim that Wi-Fi is already repaired. The slide contains a recorded screenshot of INC0010366 from 3 October 2026. It is a still image, not an embedded or completed Arcade video. Capture a fresh approved demonstration for the final MP4. Show only demo users and labelled test data.

### 9. Results and impact

60 seconds. The recorded shared-system regression contains 46 passing top-level scenarios and checks across six suites. We grouped them without overlap: 11 incident and risk scenarios, 17 permissions and conversation scenarios/checks, and 18 user and engineer page checks. The tests include low-risk resolution, engineer handoff, approval and rejection, caller follow-up, role separation and appropriate page actions. This evidence supports functional behavior in the recorded test run. It does not establish production accuracy, universal safety, customer adoption or measured financial savings. Sources: docs/evidence/agentic_live_2026-10-03/{agentic_core,triage,permissions,conversation,user_chat,engineer_page}.json and README.md. All six files report passed, and their top-level counts total 46. Date: 3 October 2026, shared ServiceNow and shared backend. No fresh live verification was run while editing this presentation.

### 10. Challenges and lessons

45 seconds. Live testing found that similar ticket text could hide different conversation context, so cache reuse was restricted to new tickets with eligibility checks. The platform's limit on UI action conditions caused buttons to appear too widely, so server-side guards now enforce the same rules. The employee page also exposed internal references, so answers now render readable text and sources. The broader lesson is to test the actual workflow as each user role. These are documented findings from the 3 October regression, not claims that this session ran new live tests. Source: docs/evidence/agentic_live_2026-10-03/README.md.

### 11. Next steps

30 seconds. Begin by agreeing the support baseline and action boundaries. Pilot with one BARQ support team and compare preparation effort, operating cost and resolution outcomes. Wider client workflows need separate access and knowledge. Infrastructure remediation is a later proposal that needs approved system actions. Our ask is a support team and sponsor for a measured pilot. These stages are proposals, not approved delivery dates or production commitments.

### 12. Close and Q&A

15 seconds. Inflow brings company knowledge into the incident workflow, automates routine ticket actions and keeps an engineer able to take control. Thank the audience and invite questions. Stay on this slide during Q&A. Demo Day is Tuesday, 6 October 2026. The organizer's supplied notice says arrival from 09:30 Cairo, start by 10:00, event until 13:00, at Sprints, Villa 2, Street 212, Degla Square, Maadi. Dress code: formal to semi-formal. The pitch is ten minutes including the Arcade video, with one or two presenters maximum. These logistics come from the user's supplied organizer messages.