"""Logged-in ServiceNow session for dev434590 (Ali PDI) setup steps the Table API cannot do
(update-set preview/commit through the instance's own GlideAjax processors)."""
import http.cookiejar, re, urllib.parse, urllib.request
from sn import BASE, env
class Session:
    def __init__(self):
        self.jar=http.cookiejar.CookieJar()
        self.op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))
        self.op.open(f"{BASE}/login.do",timeout=60).read()
        data=urllib.parse.urlencode({"user_name":env["SN_ADMIN_USER"],"user_password":env["SN_ADMIN_PASS"],
            "sys_action":"sysverb_login","sysparm_login_url":"welcome.page"}).encode()
        self.op.open(f"{BASE}/login.do",data=data,timeout=60).read()
        html=self.op.open(f"{BASE}/sys_remote_update_set_list.do",timeout=60).read().decode("utf-8","replace")
        m=re.search(r"var g_ck = '([^']+)'",html)
        if not m: raise RuntimeError("login failed: no g_ck on the page")
        self.ck=m.group(1)
    def ajax(self, processor, **params):
        body={"sysparm_processor":processor,"sysparm_scope":"global","sysparm_want_session_messages":"true",**params}
        req=urllib.request.Request(f"{BASE}/xmlhttp.do",data=urllib.parse.urlencode(body).encode(),
            headers={"X-UserToken":self.ck,"Content-Type":"application/x-www-form-urlencoded"})
        out=self.op.open(req,timeout=120).read().decode("utf-8","replace")
        m=re.search(r'answer="([^"]*)"',out)
        return m.group(1) if m else out

def background_script(session, script, scope_sys_id="51a63bbf738bc7502aedfed25ab8b789"):
    """Run a server-side script through /sys.scripts.do in the given scope; returns its output text."""
    import html as _html
    body={"script":script,"runscript":"Run script","sysparm_ck":session.ck,"sys_scope":scope_sys_id,"quota_managed_transaction":"on","record_for_rollback":"on"}
    req=urllib.request.Request(f"{BASE}/sys.scripts.do",data=urllib.parse.urlencode(body).encode(),headers={"Content-Type":"application/x-www-form-urlencoded"})
    out=session.op.open(req,timeout=180).read().decode("utf-8","replace")
    m=re.search(r"<PRE>(.*?)</PRE>",out,re.S|re.I)
    return _html.unescape(re.sub(r"<[^>]+>","",m.group(1))).strip() if m else out[-1500:]
