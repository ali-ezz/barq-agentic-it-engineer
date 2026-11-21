// Client controller of the "BARQ AI" widget: a chat with BARQ AI Agent.
// Polls while the agent works (every 2 s) and shows its live activity as a typing bubble;
// new answers from the agent type themselves in.
api.controller = function($scope, $interval, $timeout) {
    var c = this;
    c.text = '';
    c.busy = false;
    c.ticket = null;
    c.typed = {};      // message id -> characters shown so far (typing animation)
    var seen = {};     // message ids already on screen
    var first = true;
    var poll = null;
    var typing = null;

    function scrollDown() {
        $timeout(function() {
            var box = document.querySelector('.barq-messages');
            if (box) box.scrollTop = box.scrollHeight;
        }, 30);
    }

    function animate(ticket) {
        (ticket.messages || []).forEach(function(m) {
            if (seen[m.id]) return;
            seen[m.id] = true;
            if (!first && m.role === 'agent') c.typed[m.id] = 0;
        });
        first = false;
        if (typing) return;
        typing = $interval(function() {
            var pending = false;
            Object.keys(c.typed).forEach(function(id) {
                var m = (c.ticket && c.ticket.messages || []).filter(function(x) { return x.id === id; })[0];
                if (!m) { delete c.typed[id]; return; }
                c.typed[id] = Math.min(m.text.length, c.typed[id] + 3);
                if (c.typed[id] >= m.text.length) delete c.typed[id]; else pending = true;
            });
            scrollDown();
            if (!pending) { $interval.cancel(typing); typing = null; }
        }, 16);
    }

    c.shown = function(m) {
        return c.typed.hasOwnProperty(m.id) ? m.text.substring(0, c.typed[m.id]) : m.text;
    };

    function apply(data) {
        c.tickets = data.tickets || c.tickets;
        c.error = data.error || '';
        if (data.ticket) {
            var count = c.ticket ? (c.ticket.messages || []).length : 0;
            c.ticket = data.ticket;
            animate(c.ticket);
            if ((c.ticket.messages || []).length !== count || c.ticket.working) scrollDown();
        }
        schedule();
    }

    function schedule() {
        if (poll) $timeout.cancel(poll);
        var fast = c.ticket && c.ticket.working;
        poll = $timeout(refresh, fast ? 2000 : 8000);
    }

    function refresh() {
        if (c.busy) return schedule();
        var request = c.ticket ? {action: 'open', sys_id: c.ticket.sys_id} : {action: 'list'};
        c.server.get(request).then(function(r) { apply(r.data); });
    }

    c.open = function(t) {
        if (c.ticket && c.ticket.sys_id === t.sys_id) return;
        seen = {};
        first = true;
        c.typed = {};
        c.ticket = null;
        c.server.get({action: 'open', sys_id: t.sys_id}).then(function(r) { apply(r.data); scrollDown(); });
    };

    c.newChat = function() {
        c.ticket = null;
        c.text = '';
        c.error = '';
        $timeout(function() { var box = document.querySelector('.barq-compose textarea'); if (box) box.focus(); }, 50);
    };

    c.send = function() {
        var text = (c.text || '').trim();
        if (!text || c.busy) return;
        c.busy = true;
        var request = c.ticket ? {action: 'send', sys_id: c.ticket.sys_id, text: text} : {action: 'start', text: text};
        if (!c.ticket) { seen = {}; first = true; }
        c.text = '';
        c.server.get(request).then(function(r) {
            c.busy = false;
            apply(r.data);
            scrollDown();
        }, function() {
            c.busy = false;
            c.text = text;
            c.error = 'Sorry, that did not go through. Please try again.';
        });
    };

    c.keydown = function(event) {
        if (event.keyCode === 13 && !event.shiftKey) {
            event.preventDefault();
            c.send();
        }
    };

    c.time = function(at) {
        var text = String(at || '');
        return text.length >= 16 ? text.substring(11, 16) : text;
    };

    c.tickets = c.data.tickets || [];
    schedule();
    $scope.$on('$destroy', function() {
        if (poll) $timeout.cancel(poll);
        if (typing) $interval.cancel(typing);
    });
};
