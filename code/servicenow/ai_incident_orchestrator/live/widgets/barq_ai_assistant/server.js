// Server script of the "BARQ AI" widget (Employee Center page ?id=barq_ai).
// A chat with BARQ AI Agent. Every conversation is one incident the user owns: the first
// message opens it, every next message is a comment on it, and the agent answers there.
// Runs as the logged-in user; every read and write is limited to incidents where that user
// is the caller, through GlideRecordSecure so their own ACLs apply.
(function() {
    var P = 'x_2215032_ai_inc_0_ai_';
    var me = gs.getUserID();
    data.user = gs.getUserDisplayName();
    data.first_name = String(gs.getUser().getFirstName() || data.user || '').split(' ')[0];
    data.error = '';

    function clean(text, max) {
        return String(text || '').replace(/^\s+|\s+$/g, '').substring(0, max);
    }

    function ownTicket(sysId) {
        var gr = new GlideRecordSecure('incident');
        if (!sysId || !gr.get(sysId) || gr.getValue('caller_id') != me) return null;
        return gr;
    }

    function report(gr) {
        try {
            return JSON.parse(gr.getValue(P + 'report') || '{}');
        } catch (e) {
            return {};
        }
    }

    function status(gr) {
        var state = gr.getValue('state');
        var ai = gr.getValue(P + 'processing_state');
        var locked = gr.getValue(P + 'human_lock') == '1';
        var working = !locked && (ai == 'pending' || ai == 'in_progress');
        if (state == '7') return {label: 'Closed', tone: 'done', working: false, open: false};
        if (state == '8') return {label: 'Cancelled', tone: 'done', working: false, open: false};
        if (working) return {label: 'Looking into it', tone: 'info', working: true, open: true};
        if (state == '6') return {label: 'Fixed - tell me if it works', tone: 'good', working: false, open: true};
        if (state == '3' && gr.getValue('hold_reason') == '1') return {label: 'Waiting for your reply', tone: 'warn', working: false, open: true};
        var outcome = report(gr).outcome;
        if (locked || gr.getValue(P + 'human_review_required') == '1' || outcome == 'with_engineer' || outcome == 'security')
            return {label: 'With an engineer', tone: 'info', working: false, open: true};
        return {label: 'In progress', tone: 'info', working: false, open: true};
    }

    function summary(gr) {
        var s = status(gr);
        return {
            sys_id: gr.getUniqueValue(),
            number: gr.getValue('number'),
            title: gr.getValue('short_description'),
            status: s.label,
            tone: s.tone,
            working: s.working,
            open: s.open,
            updated: gr.getDisplayValue('sys_updated_on')
        };
    }

    function myTickets() {
        var list = [];
        var gr = new GlideRecordSecure('incident');
        gr.addQuery('caller_id', me);
        gr.addQuery('sys_created_on', '>=', gs.daysAgoStart(60));
        gr.orderByDesc('sys_updated_on');
        gr.setLimit(25);
        gr.query();
        while (gr.next()) list.push(summary(gr));
        return list;
    }

    function messages(gr) {
        // The caller's own first message (the ticket text), then the customer-visible
        // comments, oldest first; never work notes.
        var list = [{
            id: 'first',
            // display value: the user's own time zone, like the journal entries below
            at: gr.getDisplayValue('opened_at'),
            who: data.user,
            role: 'me',
            text: gr.getValue('description') || gr.getValue('short_description')
        }];
        var text = String(gr.getDisplayValue('comments') || '');
        var header = /^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - (.+?) \((?:Additional comments|Comments)\)\s*$/gm;
        var marks = [], m;
        while ((m = header.exec(text)) !== null) marks.push({at: m[1], who: m[2], start: m.index, end: header.lastIndex});
        var comments = [];
        for (var i = 0; i < marks.length; i++) {
            var body = text.substring(marks[i].end, i + 1 < marks.length ? marks[i + 1].start : text.length);
            var who = marks[i].who;
            var agent = who == 'BARQ AI Agent' || who.indexOf('AI Orchestrator') == 0;
            comments.push({
                id: marks[i].at + '|' + who,
                at: marks[i].at,
                who: agent ? 'BARQ AI' : who,
                role: who == data.user ? 'me' : (agent ? 'agent' : 'engineer'),
                text: body.replace(/^\s+|\s+$/g, '')
            });
        }
        comments.sort(function(a, b) { return a.at < b.at ? -1 : a.at > b.at ? 1 : 0; });
        return list.concat(comments);
    }

    function view(gr) {
        var v = summary(gr);
        v.messages = messages(gr);
        v.activity = v.working ? (gr.getValue(P + 'activity') || 'Looking into it…') : '';
        return v;
    }

    var action = input && input.action;

    if (!action || action == 'init' || action == 'list') {
        data.tickets = myTickets();
        return;
    }

    if (action == 'start') {
        var message = clean(input.text, 4000);
        if (!message) return;
        var firstLine = message.split(/\r?\n/)[0];
        var inc = new GlideRecord('incident');
        inc.initialize();
        inc.setValue('caller_id', me);
        inc.setValue('short_description', firstLine.length > 90 ? firstLine.substring(0, 87) + '...' : firstLine);
        inc.setValue('description', message);
        inc.setValue('category', 'inquiry');
        inc.setValue('contact_type', 'self-service');
        inc.setValue('impact', 3);
        inc.setValue('urgency', 3);
        inc.setValue(P + 'enabled', true);
        inc.setValue(P + 'activity', 'Reading your message…');
        var created = inc.insert();
        if (!created) {
            data.error = 'Sorry, I could not start the conversation. Please try again.';
            return;
        }
        data.ticket = view(ownTicket(created));
        data.tickets = myTickets();
        return;
    }

    var ticket = ownTicket(input.sys_id);
    if (!ticket) {
        data.error = 'That conversation is not available.';
        data.tickets = myTickets();
        return;
    }

    if (action == 'send') {
        var reply = clean(input.text, 4000);
        if (reply && status(ticket).open) {
            ticket.comments = reply;
            ticket.update();
            ticket = ownTicket(input.sys_id);
        }
    }
    data.ticket = view(ticket);
    data.tickets = myTickets();
})();
