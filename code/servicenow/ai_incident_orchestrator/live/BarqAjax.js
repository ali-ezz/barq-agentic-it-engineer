// Script include BarqAjax (client callable): everything the engineer's BARQ AI card does.
//   card        -> the card's data (status, report, live activity) for drawing and refresh
//   control     -> Take over (the engineer holds the ticket, the agent is locked out) or
//                  Hand back (the agent holds it again), with an optional instruction
//   instruct    -> tell the agent what to do next while it holds the ticket
//   undo        -> undo one account change the agent made (unlock -> lock again, ...)
// Only engineers (itil) and approvers may use it, on an incident they can read.
var BarqAjax = Class.create();
BarqAjax.prototype = Object.extendsObject(global.AbstractAjaxProcessor, {
    P: 'x_2215032_ai_inc_0_ai_',
    MARKER: '[To BARQ AI]',
    UNDO_FLAG: {lock: ['locked_out', true], clear_password_change: ['password_needs_reset', false]},

    _engineer: function() {
        return gs.hasRole('itil') || gs.hasRole('x_2215032_ai_inc_0.operator');
    },

    _incident: function() {
        var incident = new GlideRecordSecure('incident');
        if (!this._engineer() || !incident.get(String(this.getParameter('sysparm_sys_id') || ''))) return null;
        return incident;
    },

    _answer: function(value) {
        return JSON.stringify(value);
    },

    card: function() {
        var incident = this._incident();
        if (!incident) return this._answer({error: 'not_available'});
        var P = this.P;
        var report = {};
        try {
            report = JSON.parse(incident.getValue(P + 'report') || '{}');
        } catch (e) {
            report = {};
        }
        return this._answer({
            number: incident.getValue('number'),
            state: incident.getValue('state'),
            state_label: incident.getDisplayValue('state'),
            enabled: incident.getValue(P + 'enabled') == '1',
            locked: incident.getValue(P + 'human_lock') == '1',
            ai_state: incident.getValue(P + 'processing_state'),
            activity: incident.getValue(P + 'activity') || '',
            caller: incident.getDisplayValue('caller_id'),
            team: incident.getDisplayValue('assignment_group'),
            updated: incident.getDisplayValue('sys_updated_on'),
            report: report
        });
    },

    control: function() {
        var incident = this._incident();
        if (!incident || incident.getValue('active') != '1') return this._answer({ok: false, error: 'not_available'});
        var P = this.P;
        var instruction = String(this.getParameter('sysparm_text') || '').replace(/^\s+|\s+$/g, '').substring(0, 2000);
        var record = new GlideRecord('incident');
        record.get(incident.getUniqueValue());
        if (record.getValue(P + 'human_lock') != '1') {
            record.setValue(P + 'human_lock', true);
            record.setValue(P + 'activity', '');
            record.work_notes = 'Taken over from BARQ AI Agent by ' + gs.getUserDisplayName() +
                '. The agent will not change this ticket until it is handed back.';
            record.update();
            return this._answer({ok: true, holder: 'engineer'});
        }
        record.setValue(P + 'human_lock', false);
        record.setValue(P + 'human_review_required', false);
        record.setValue(P + 'processing_state', 'pending');
        record.setValue(P + 'activity', 'Reading the instruction…');
        if (record.getValue('state') == '3') {
            record.state = 2;
            record.hold_reason = '';
        }
        record.work_notes = 'Handed back to BARQ AI Agent by ' + gs.getUserDisplayName() +
            (instruction ? '. Instruction: ' + instruction : '.');
        record.update();
        // Clearing the lock wakes the agent through the eligibility rule (one event).
        return this._answer({ok: true, holder: 'agent'});
    },

    instruct: function() {
        var incident = this._incident();
        if (!incident || incident.getValue('active') != '1') return this._answer({ok: false, error: 'not_available'});
        var text = String(this.getParameter('sysparm_text') || '').replace(/^\s+|\s+$/g, '').substring(0, 2000);
        if (!text) return this._answer({ok: false, error: 'empty'});
        if (incident.getValue(this.P + 'human_lock') == '1') return this.control();
        var record = new GlideRecord('incident');
        record.get(incident.getUniqueValue());
        record.setValue(this.P + 'activity', 'Reading the instruction…');
        // The conversation rule sees the marker and wakes the agent with this instruction.
        record.work_notes = this.MARKER + ' ' + text;
        record.update();
        return this._answer({ok: true});
    },

    undo: function() {
        var incident = this._incident();
        if (!incident) return this._answer({ok: false, error: 'not_available'});
        var P = this.P;
        var index = parseInt(this.getParameter('sysparm_index'), 10);
        var report = {};
        try {
            report = JSON.parse(incident.getValue(P + 'report') || '{}');
        } catch (e) {
            return this._answer({ok: false, error: 'no_report'});
        }
        var actions = report.actions || [];
        var action = actions[index];
        if (!action || action.undone || !this.UNDO_FLAG[action.undo]) return this._answer({ok: false, error: 'nothing_to_undo'});
        var flag = this.UNDO_FLAG[action.undo];
        var now = new global.BarqAccount().setFlag(incident.getValue('caller_id'), flag[0], flag[1]);
        if (now !== flag[1]) return this._answer({ok: false, error: 'not_applied'});
        action.undone = true;
        action.undone_by = gs.getUserDisplayName();
        action.undone_at = new GlideDateTime().getDisplayValue();
        report.timeline = report.timeline || [];
        report.timeline.push({at: new GlideDateTime().getValue(), kind: 'undo',
            title: gs.getUserDisplayName() + ' undid: ' + action.title, ok: true});
        var record = new GlideRecord('incident');
        record.get(incident.getUniqueValue());
        record.setValue(P + 'report', JSON.stringify(report));
        record.work_notes = gs.getUserDisplayName() + ' undid what BARQ AI Agent did: ' + action.title + '.';
        record.update();
        return this._answer({ok: true});
    },

    type: 'BarqAjax'
});
