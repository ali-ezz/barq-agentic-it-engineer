// Global script include BarqAccount (accessible from all scopes), used only by the scoped
// "BARQ account" REST API. Global code may read the platform's sign-in events and write a
// user's lock flags, which app code may not. It does exactly that and nothing else, and
// only for BARQ AI Agent's integration role:
//   signins(userName)            -> JSON: recent login / login.failed events (7 days)
//   setFlag(userSysId, f, value) -> f in {locked_out, password_needs_reset}; returns new value
//                                   (the agent, or an engineer undoing the agent's change)
var BarqAccount = Class.create();
BarqAccount.prototype = {
    AGENT_ROLE: 'x_2215032_ai_inc_0.integration_writer',
    FLAGS: {locked_out: true, password_needs_reset: true},

    initialize: function() {},

    _allowed: function() {
        return gs.hasRole(this.AGENT_ROLE);
    },

    signins: function(userName) {
        if (!this._allowed() || !userName) return '[]';
        var rows = [];
        var event = new GlideRecord('sysevent');
        event.addQuery('name', 'IN', 'login,login.failed');
        event.addQuery('parm1', String(userName));
        event.addQuery('sys_created_on', '>=', gs.daysAgoStart(7));
        event.orderByDesc('sys_created_on');
        event.setLimit(40);
        event.query();
        while (event.next())
            rows.push({
                at: event.getValue('sys_created_on'),
                ok: event.getValue('name') == 'login',
                address: String(event.getValue('parm2') || '')
            });
        return JSON.stringify(rows);
    },

    setFlag: function(userSysId, field, value) {
        if (!(this._allowed() || gs.hasRole('itil')) || !this.FLAGS[field]) return null;
        var user = new GlideRecord('sys_user');
        if (!user.get(String(userSysId))) return null;
        user.setValue(field, value ? true : false);
        if (field == 'locked_out' && !value) user.setValue('failed_attempts', 0);
        user.update();
        var fresh = new GlideRecord('sys_user');
        fresh.get(String(userSysId));
        return fresh.getValue(field) == '1';
    },

    type: 'BarqAccount'
};
