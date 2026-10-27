#!/usr/bin/env python3
"""
rootctl.py -- one-shot root control for the Samsung The Frame TV.

Commands:
  stop     Recreate the 3 marker files (persistent disable) and stop all 8
           ad/analytics/context daemons. Idempotent -- safe to run after a
           reboot to re-kill the marker-less daemons.
  restore  Full reversal: delete the 3 marker files and start all 8 daemons.
  status   Read-only: show marker files and any running target daemons.

Set TV_IP to your TV's address (e.g. `TV_IP=192.168.1.20`).

Mechanism: reuses tvrun-slow.py's `0 appinstall` injection to run commands as
the sdk user; for root work it stages a short script to /tmp/rt.sh and runs it
through RootExec.dll via `eval "$(cat /tmp/rt.sh)"` (the vendor shell refuses
unsigned script *files*, so we read the file as data and eval it instead).
"""
import base64
import importlib.util
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))

# Reuse tvrun-slow.py's injection (60s accept / 180s recv) without a hyphen import.
_spec = importlib.util.spec_from_file_location(
    "tvrun_slow", os.path.join(HERE, "tvrun-slow.py"))
_tvrun = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_tvrun)
run = _tvrun.run

# RootExec staging dir (matches RootExec.Program.cs's hard-coded ProbeName).
DIR = "/home/owner/share/tmp/sdk_tools/codex-namespace-proof"

# Marker files gating the daemons via ConditionPathExists=!<marker>.
MARKERS = [
    "/opt/usr/share/systemd/system/pisa-service",                                  # gates adagent-service AND pisa-service
    "/opt/usr/share/systemd/system/com.samsung.tv.context-aware-service",
    "/opt/usr/share/systemd/system/com.samsung.tv.context-aware-agent",
]

# All target daemons (gated + marker-less). stfind-daemon is intentionally left
# out (SmartThings Find, launchpad app, 0.0% CPU -- package-level decision later).
DAEMONS = [
    "adagent-service",
    "pisa-service",
    "com.samsung.tv.context-aware-service",
    "com.samsung.tv.context-aware-agent",
    "com.samsung.tv.activity-inference-service",
    "user-presence",
    "gsl-service",
    "media-analytics-service",
]


def run_tv(host, command):
    return run(host, command, host + ":26101")


def _stage(host, text):
    """Write `text` to /tmp/rt.sh on the TV via base64 chunks (72-char safe)."""
    b64 = base64.b64encode(text.encode()).decode()
    run_tv(host, "rm -f /tmp/rt.sh /tmp/rt.b64")
    for i in range(0, len(b64), 72):
        run_tv(host, "echo %s >>/tmp/rt.b64" % b64[i:i + 72])
        time.sleep(0.2)
    run_tv(host, "base64 -d /tmp/rt.b64 > /tmp/rt.sh")


def _exec_root(host, command):
    """Run `command` as root via RootExec (eval-file workaround for UEP gate)."""
    _stage(host, command)
    cmd = ('d=%s;dotnet $d/RootExec.dll $d "eval \\"\\$(cat /tmp/rt.sh)\\""'
           % DIR)
    return run_tv(host, cmd)


def cmd_stop(host):
    lines = ["touch " + m for m in MARKERS]
    lines += ["systemctl stop " + d for d in DAEMONS]
    lines.append("echo STOP-DONE")
    return _exec_root(host, "\n".join(lines))


def cmd_restore(host):
    lines = ["rm -f " + m for m in MARKERS]
    lines += ["systemctl start " + d for d in DAEMONS]
    lines.append("echo RESTORE-DONE")
    return _exec_root(host, "\n".join(lines))


def cmd_status(host):
    out = []
    out.append("=== marker files ===")
    out.append(run_tv(
        host,
        "ls /opt/usr/share/systemd/system/ | "
        "grep -E 'pisa-service|context-aware'"))
    out.append("=== running target daemons ===")
    out.append(run_tv(
        host,
        "ps -eo pid,pcpu,pmem,comm | grep -iE "
        "'adagent|pisa|analytics|context|infere|presence|gsl' | grep -v grep"))
    return "\n".join(out)


if __name__ == "__main__":
    host = os.environ.get("TV_IP")
    if not host:
        sys.exit("Set TV_IP to your TV's address (e.g. TV_IP=192.168.1.20)")
    action = sys.argv[1] if len(sys.argv) > 1 else "status"
    if action == "stop":
        print(cmd_stop(host))
    elif action == "restore":
        print(cmd_restore(host))
    elif action == "status":
        print(cmd_status(host))
    else:
        raise SystemExit("usage: rootctl.py [stop|restore|status]")
