// Scripted REST "BARQ account", GET /facts?incident=<sys_id>[&user=<user_name|email|name>]
// What BARQ AI Agent may know about a person while it works an incident: account status,
// recent sign-ins, groups and roles. Read only. Only the agent's integration role may call
// it. Without "user" it describes the incident's caller; with it, another person (for
// checking a story) — the agent is never allowed to act on that person.
(function process(request, response) {
    var AGENT_ROLE = 'x_2215032_ai_inc_0.integration_writer';
    if (!gs.hasRole(AGENT_ROLE)) {
        response.setStatus(403);
        return {error: 'not_allowed'};
    }
    var incident = new GlideRecord('incident');
    if (!incident.get(String(request.queryParams.incident || ''))) {
        response.setStatus(404);
        return {error: 'incident_not_found'};
    }
    var callerId = incident.getValue('caller_id');
    var wanted = String(request.queryParams.user || '').replace(/^\s+|\s+$/g, '');
    var user = new GlideRecord('sys_user');
    if (!wanted) {
        if (!callerId || !user.get(callerId)) {
            response.setStatus(404);
            return {error: 'no_caller'};
        }
    } else {
        var condition = user.addQuery('user_name', wanted);
        condition.addOrCondition('email', wanted);
        condition.addOrCondition('name', wanted);
        user.setLimit(2);
        user.query();
        if (!user.next()) {
            response.setStatus(404);
            return {error: 'user_not_found'};
        }
        if (user.hasNext()) {
            response.setStatus(409);
            return {error: 'more_than_one_user_matches'};
        }
    }
    var userId = user.getUniqueValue();
    var userName = user.getValue('user_name');

    var roles = [];
    var privileged = false;
    var hasRole = new GlideRecord('sys_user_has_role');
    hasRole.addQuery('user', userId);
    hasRole.addQuery('state', 'active');
    hasRole.setLimit(60);
    hasRole.query();
    while (hasRole.next()) {
        var roleName = String(hasRole.role.name);
        if (roles.indexOf(roleName) < 0) roles.push(roleName);
        if (roleName == 'admin' || /(^|[._])(security_)?admin$/.test(roleName) || roleName == 'user_admin')
            privileged = true;
    }

    var groups = [];
    var member = new GlideRecord('sys_user_grmember');
    member.addQuery('user', userId);
    member.setLimit(25);
    member.query();
    while (member.next()) groups.push(String(member.group.name));

    // Sign-ins from the platform's own event log (login / login.failed), last 7 days,
    // read by the global helper (app code may not read the event log).
    var events = JSON.parse(new global.BarqAccount().signins(userName) || '[]');
    var signins = [];
    var failed1h = 0, failed24h = 0, addresses = [];
    var lastSuccess = null;
    var hourAgo = new GlideDateTime();
    hourAgo.addSeconds(-3600);
    var dayAgo = new GlideDateTime();
    dayAgo.addSeconds(-86400);
    for (var i = 0; i < events.length; i++) {
        var row = events[i];
        var at = new GlideDateTime(row.at);
        if (signins.length < 15) signins.push(row);
        if (!row.ok && at.compareTo(hourAgo) >= 0) failed1h++;
        if (!row.ok && at.compareTo(dayAgo) >= 0) failed24h++;
        if (row.address && addresses.indexOf(row.address) < 0) addresses.push(row.address);
        if (row.ok && !lastSuccess) lastSuccess = {at: row.at, address: row.address};
    }

    return {
        user: {
            sys_id: userId,
            user_name: userName,
            name: user.getValue('name'),
            title: user.getValue('title') || '',
            department: user.getDisplayValue('department') || '',
            manager: user.getDisplayValue('manager') || '',
            vip: user.getValue('vip') == '1',
            active: user.getValue('active') == '1',
            locked_out: user.getValue('locked_out') == '1',
            password_needs_reset: user.getValue('password_needs_reset') == '1',
            failed_attempts: parseInt(user.getValue('failed_attempts') || '0', 10) || 0,
            last_login: user.getValue('last_login_time') || '',
            created: user.getValue('sys_created_on') || ''
        },
        is_caller: userId == callerId,
        privileged: privileged,
        roles: roles,
        groups: groups,
        signins: {
            failed_last_hour: failed1h,
            failed_last_day: failed24h,
            addresses_last_week: addresses,
            last_success: lastSuccess,
            recent: signins
        }
    };
})(request, response);
