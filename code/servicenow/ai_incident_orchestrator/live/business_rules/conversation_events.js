// Business rule "BARQ AI - Conversation events" (incident, before update, order 1000).
// The agentic engineer's conversation: who holds the ticket and what wakes the agent up.
//   - the caller writes (or edits the ticket) -> the agent continues, unless an engineer
//     holds it; a reply on a solved or waiting ticket brings it back to In Progress, and
//     the agent decides (it closes when the caller confirms, keeps working when not);
//   - an engineer writes to the caller -> the engineer takes the ticket (Human Lock on), so
//     the caller never hears two voices;
//   - an engineer writes a work note starting with "[To BARQ AI]" -> an instruction for the
//     agent (handled by BarqAjax when sent from the card; typed by hand it works too);
//   - closed or cancelled -> recorded for learning.
// The agent's own writes never trigger anything.
(function executeRule(current, previous) {
    var P = 'x_2215032_ai_inc_0_ai_';
    var MARKER = '[To BARQ AI]';
    if (current.getValue(P + 'enabled') != '1') return;
    var agentUser = gs.getProperty('x_2215032_ai_inc_0.agent_user_name', 'ai_orchestrator_svc');
    if (gs.getUserName() == agentUser) return;

    var actor = gs.getUserID();
    var isCaller = actor == current.getValue('caller_id');
    var wrote = current.comments.changes();
    var noted = current.work_notes.changes();
    var edited = current.short_description.changes() || current.description.changes();
    var before = previous.getValue('state');
    var state = current.getValue('state');
    var locked = current.getValue(P + 'human_lock') == '1';
    var finished = state == '7' || state == '8';
    var event = '';

    if (finished && before != state) {
        event = 'incident.closed';
    } else if (isCaller && (wrote || edited)) {
        if (!locked) {
            // The caller is talking to the agent: wake it up on a solved or waiting ticket.
            if (state == '6' || state == '3') {
                current.state = 2;
                current.hold_reason = '';
            }
            current.setValue(P + 'processing_state', 'pending');
            current.setValue(P + 'activity', 'Reading your message…');
            event = wrote ? 'incident.caller_replied' : 'incident.caller_updated';
        }
    } else if (wrote && !isCaller) {
        if (!locked) {
            current.setValue(P + 'human_lock', true);
            current.setValue(P + 'activity', '');
            current.work_notes = 'BARQ AI Agent stood down: ' + gs.getUserDisplayName() +
                ' is talking with the caller. Use "Hand back to BARQ AI" on the BARQ AI card to return the ticket.';
        }
        event = 'incident.engineer_replied';
    } else if (noted && !isCaller && !locked && String(current.work_notes).indexOf(MARKER) >= 0) {
        current.setValue(P + 'processing_state', 'pending');
        event = 'incident.engineer_instructed';
    } else if (before == '6' && state != '6' && !finished && !isCaller) {
        event = 'incident.reopened';
    }

    if (event)
        gs.eventQueue('x_2215032_ai_inc_0.barq_event', current, gs.generateGUID(), event + '|' + actor);
})(current, previous);
