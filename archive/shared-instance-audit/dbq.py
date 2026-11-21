import os, subprocess, sys
sys.path.insert(0, os.path.dirname(__file__))
from sn_admin import ENV
def q(sql):
    cmd = "docker exec -i barq-postgres sh -c 'psql -U \"$POSTGRES_USER\" -d \"$POSTGRES_DB\" -At -F\"|\"'"
    r = subprocess.run(["ssh", "-i", os.path.expanduser("~/.ssh/barq-ec2"), "-o", "BatchMode=yes", f"ubuntu@{ENV['SHARED_BACKEND_HOST']}", cmd], input=sql, capture_output=True, text=True, timeout=90)
    return [l.split("|") for l in r.stdout.strip().splitlines() if l], r.stderr.strip()
