// UI script x_2215032_ai_inc_0.barq_card: draws the engineer's BARQ AI card on the
// incident form (view "BARQ AI") from the agent's report, and keeps it live.
// One button (Take over / Hand back), one box to tell the agent what to do, Undo on each
// account change, and the full "how BARQ AI worked" timeline folded away.
(function() {
    var AJAX = 'x_2215032_ai_inc_0.BarqAjax';
    var timer = null;
    var openTimeline = false;
    var busy = false;

    function esc(value) {
        return String(value === null || value === undefined ? '' : value)
            .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }

    function ajax(method, extra, done) {
        var request = new GlideAjax(AJAX);
        request.addParam('sysparm_name', method);
        request.addParam('sysparm_sys_id', g_form.getUniqueValue());
        for (var key in extra) if (extra.hasOwnProperty(key)) request.addParam(key, extra[key]);
        request.getXMLAnswer(function(answer) {
            var data = {};
            try { data = JSON.parse(answer || '{}'); } catch (e) { data = {error: 'bad_answer'}; }
            done(data);
        });
    }

    function tone(data) {
        var outcome = (data.report || {}).outcome || '';
        if (data.locked) return 'muted';
        if (working(data)) return 'info';
        if (outcome === 'security') return 'bad';
        if (outcome === 'with_engineer') return 'warn';
        if (outcome === 'fixed' || outcome === 'closed') return 'good';
        return 'info';
    }

    function working(data) {
        return !data.locked && (data.ai_state === 'pending' || data.ai_state === 'in_progress');
    }

    function status(data) {
        var report = data.report || {};
        if (data.state === '8') return 'Cancelled';
        if (data.locked) return 'An engineer holds this ticket';
        if (!data.enabled) return 'BARQ AI is off for this ticket';
        if (working(data)) return 'BARQ AI is working on it';
        return report.status || 'Waiting for BARQ AI';
    }

    function when(at) {
        var text = String(at || '');
        return text.length >= 16 ? text.substring(11, 16) : text;
    }

    var SOURCE = {account: 'Account', 'sign-ins': 'Sign-ins', knowledge: 'Knowledge', tickets: 'Tickets',
        caller: 'Caller', engineer: 'Engineer'};
    var KIND = {event: 'barq-k-event', check: 'barq-k-check', act: 'barq-k-act', reply: 'barq-k-reply',
        decision: 'barq-k-decision', note: 'barq-k-check', undo: 'barq-k-undo'};

    function render(data) {
        var box = document.getElementById('barq-card');
        if (!box) return;
        if (data.error) {
            box.className = 'barq-card barq-muted';
            box.innerHTML = '<div class="barq-head"><span class="barq-logo">BARQ AI</span><span class="barq-chip">Not available for you on this ticket</span></div>';
            return;
        }
        var report = data.report || {};
        var html = [];
        var holder = data.locked ? 'Engineer' : 'BARQ AI Agent';
        html.push('<div class="barq-head"><span class="barq-logo">BARQ AI</span>');
        html.push('<span class="barq-chip">' + (working(data) ? '<span class="barq-pulse"></span>' : '') + esc(status(data)) + '</span>');
        html.push('<span class="barq-owner">In control: <b>' + esc(holder) + '</b></span>');
        if (data.enabled && data.state !== '7' && data.state !== '8')
            html.push('<button type="button" class="barq-btn" id="barq-control">' + (data.locked ? 'Hand back to BARQ AI' : 'Take over') + '</button>');
        html.push('</div>');

        if (working(data) && data.activity)
            html.push('<div class="barq-live"><span class="barq-dots"><i></i><i></i><i></i></span>' + esc(data.activity) + '</div>');
        if (report.summary) html.push('<div class="barq-summary">' + esc(report.summary) + '</div>');
        if (report.conclusion) html.push('<div class="barq-conclusion">' + esc(report.conclusion) + '</div>');

        if (report.said || (report.facts || []).length) {
            html.push('<div class="barq-grid">');
            html.push('<div class="barq-panel"><div class="barq-label">What the caller said</div><div class="barq-quote">' + esc(report.said || '—') + '</div></div>');
            html.push('<div class="barq-panel"><div class="barq-label">What BARQ AI found</div><ul class="barq-facts">');
            var facts = report.facts || [];
            for (var i = 0; i < facts.length; i++)
                html.push('<li><span class="barq-src">' + esc(SOURCE[facts[i].source] || facts[i].source) + '</span>' + esc(facts[i].fact) + '</li>');
            if (!facts.length) html.push('<li class="barq-none">Nothing checked yet.</li>');
            html.push('</ul></div></div>');
        }

        var actions = report.actions || [];
        if (actions.length) {
            html.push('<div class="barq-label">What BARQ AI did</div><ul class="barq-actions">');
            for (var a = 0; a < actions.length; a++) {
                var act = actions[a];
                html.push('<li class="' + (act.undone ? 'barq-undone' : '') + '"><span class="barq-tick">' + (act.undone ? '↺' : '✓') + '</span>' + esc(act.title) +
                    ' <span class="barq-time">' + esc(when(act.at)) + '</span>' +
                    (act.undone ? ' <span class="barq-muted-text">undone by ' + esc(act.undone_by) + '</span>' :
                        (act.undo ? ' <a href="#" class="barq-undo" data-index="' + a + '">Undo</a>' : '')) + '</li>');
            }
            html.push('</ul>');
        }
        var flags = report.red_flags || [];
        if (flags.length) {
            html.push('<div class="barq-flags"><b>Red flags</b><ul>');
            for (var f = 0; f < flags.length; f++) html.push('<li>' + esc(flags[f]) + '</li>');
            html.push('</ul></div>');
        }
        if (report.recommendation)
            html.push('<div class="barq-reco"><b>Recommendation</b> ' + esc(report.recommendation) + '</div>');

        var meta = [];
        if (report.confidence !== undefined && report.confidence !== null) {
            var pct = Math.round(Number(report.confidence) * 100);
            if (!isNaN(pct)) meta.push('<span>Confidence&nbsp;<b>' + pct + '%</b><span class="barq-bar"><span style="width:' + pct + '%"></span></span></span>');
        }
        if (data.team) meta.push('<span>Team:&nbsp;<b>' + esc(data.team) + '</b></span>');
        if (report.updated_at) meta.push('<span>Updated&nbsp;' + esc(when(report.updated_at)) + '&nbsp;UTC</span>');
        if (meta.length) html.push('<div class="barq-meta">' + meta.join('<span class="barq-sep"></span>') + '</div>');

        var timeline = report.timeline || [];
        if (timeline.length) {
            html.push('<a href="#" class="barq-toggle" id="barq-toggle">' + (openTimeline ? '▾ Hide' : '▸ Show') + ' how BARQ AI worked (' + timeline.length + ' steps)</a>');
            if (report.trace_url && /^https:\/\//.test(report.trace_url))
                html.push('<a class="barq-trace" target="_blank" rel="noopener" href="' + esc(report.trace_url) + '">Open the full trace in Langfuse ↗</a>');
            if (openTimeline) {
                html.push('<ol class="barq-timeline">');
                for (var t = 0; t < timeline.length; t++) {
                    var step = timeline[t];
                    html.push('<li class="' + (KIND[step.kind] || '') + (step.ok === false ? ' barq-failed' : '') + '"><span class="barq-time">' + esc(when(step.at)) + '</span><b>' + esc(step.title) + '</b>' +
                        (step.reason ? '<div class="barq-why">Why: ' + esc(step.reason) + '</div>' : '') +
                        (step.detail ? '<div class="barq-detail">' + esc(step.detail) + '</div>' : '') + '</li>');
                }
                html.push('</ol>');
            }
        }

        if (data.enabled && data.state !== '7' && data.state !== '8') {
            html.push('<div class="barq-ask"><textarea id="barq-text" rows="2" placeholder="' +
                esc(data.locked ? 'Optional: what should BARQ AI do when you hand it back?' : 'Tell BARQ AI what to do next, e.g. check if she is in the VPN group, or save this fix as knowledge') +
                '"></textarea><button type="button" class="barq-btn barq-send" id="barq-send">' + (data.locked ? 'Hand back' : 'Send') + '</button></div>');
        }
        var typed = document.getElementById('barq-text');
        var keep = typed ? typed.value : '';
        box.className = 'barq-card barq-' + tone(data);
        box.innerHTML = html.join('');
        var area = document.getElementById('barq-text');
        if (area && keep) area.value = keep;
        bind(data);
        schedule(data);
    }

    function bind(data) {
        var control = document.getElementById('barq-control');
        if (control) control.onclick = function() {
            if (busy) return;
            busy = true;
            control.disabled = true;
            var area = document.getElementById('barq-text');
            ajax('control', {sysparm_text: area ? area.value : ''}, function() { location.reload(); });
        };
        var send = document.getElementById('barq-send');
        if (send) send.onclick = function() {
            var area = document.getElementById('barq-text');
            var text = area ? area.value.replace(/^\s+|\s+$/g, '') : '';
            if (!text && !data.locked) return;
            busy = true;
            send.disabled = true;
            ajax(data.locked ? 'control' : 'instruct', {sysparm_text: text}, function(result) {
                busy = false;
                if (data.locked) { location.reload(); return; }
                if (area) area.value = '';
                refresh();
            });
        };
        var toggle = document.getElementById('barq-toggle');
        if (toggle) toggle.onclick = function(event) {
            event.preventDefault();
            openTimeline = !openTimeline;
            render(data);
        };
        var undos = document.querySelectorAll('#barq-card .barq-undo');
        for (var i = 0; i < undos.length; i++) undos[i].onclick = function(event) {
            event.preventDefault();
            var index = this.getAttribute('data-index');
            if (!confirm('Undo this action on the caller\'s account?')) return;
            ajax('undo', {sysparm_index: index}, function(result) {
                if (!result.ok) alert('Could not undo: ' + (result.error || 'unknown'));
                refresh();
            });
        };
    }

    function schedule(data) {
        if (timer) clearTimeout(timer);
        timer = setTimeout(refresh, working(data) ? 2500 : 15000);
    }

    function refresh() {
        if (busy) return;
        var focused = document.activeElement;
        if (focused && focused.id === 'barq-text' && focused.value) {
            // never redraw under an engineer who is typing an instruction
            timer = setTimeout(refresh, 3000);
            return;
        }
        ajax('card', {}, render);
    }

    window.barqCardStart = function() {
        if (document.getElementById('barq-card')) refresh();
    };
})();
