// Scripted REST "BARQ account", POST /action  {incident, action, by}
// The only account changes BARQ AI Agent can make, each with its undo:
//   unlock <-> lock, require_password_change <-> clear_password_change.
// Enforced here as well as in the backend: only the agent's integration role, only the
// CALLER of an open incident that no engineer has taken over, never a privileged account
// (admin rights) and never an inactive one. Returns the account before and after.
(function process(request, response) {
    var AGENT_ROLE = 'x_2215032_ai_inc_0.integration_writer';
    var ACTIONS = {
        unlock: {field: 'locked_out', value: false},
        lock: {field: 'locked_out', value: true},
        require_password_change: {field: 'password_needs_reset', value: true},
        clear_password_change: {field: 'password_needs_reset', value: false}
    };
    function refuse(status, reason) {
        response.setStatus(status);
        return {ok: false, error: reason};
    }
    if (!gs.hasRole(AGENT_ROLE)) return refuse(403, 'not_allowed');
    var body = request.body ? request.body.data : {};
    var action = ACTIONS[String(body.action || '')];
    if (!action) return refuse(400, 'unknown_action');

    var incident = new GlideRecord('incident');
    if (!incident.get(String(body.incident || ''))) return refuse(404, 'incident_not_found');
    if (incident.getValue('active') != '1') return refuse(409, 'incident_closed');
    if (incident.getValue('x_2215032_ai_inc_0_ai_human_lock') == '1') return refuse(409, 'engineer_has_taken_over');

    var user = new GlideRecord('sys_user');
    if (!incident.getValue('caller_id') || !user.get(incident.getValue('caller_id')))
        return refuse(404, 'no_caller');
    if (user.getValue('active') != '1') return refuse(409, 'account_inactive');

    var hasRole = new GlideRecord('sys_user_has_role');
    hasRole.addQuery('user', user.getUniqueValue());
    hasRole.addQuery('state', 'active');
    hasRole.query();
    while (hasRole.next()) {
        var roleName = String(hasRole.role.name);
        if (roleName == 'admin' || /(^|[._])(security_)?admin$/.test(roleName) || roleName == 'user_admin')
            return refuse(403, 'privileged_account');
    }

    var before = {
        locked_out: user.getValue('locked_out') == '1',
        password_needs_reset: user.getValue('password_needs_reset') == '1'
    };
    // The write itself is done by the global helper (app code may not update sys_user).
    var now = new global.BarqAccount().setFlag(user.getUniqueValue(), action.field, action.value);
    var after = {
        locked_out: action.field == 'locked_out' ? now : before.locked_out,
        password_needs_reset: action.field == 'password_needs_reset' ? now : before.password_needs_reset
    };
    var applied = after[action.field] === action.value;
    gs.info('BARQ account action ' + body.action + ' on ' + user.getValue('user_name') + ' for ' +
        incident.getValue('number') + ': ' + (applied ? 'applied' : 'NOT applied'));
    if (!applied) response.setStatus(500);
    return {ok: applied, action: String(body.action), user_name: user.getValue('user_name'), before: before, after: after};
})(request, response);
