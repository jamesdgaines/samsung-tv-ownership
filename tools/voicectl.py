#!/usr/bin/env python3
"""
voicectl.py -- disable/enable the voice-assistant packages on the Samsung The Frame TV.

Voice processes are launchpad-managed (children of launchpad-process-pool), NOT
systemd daemons, so `pkgcmd -D --global` actually stops them (unlike the ad
daemons). This is the clean, reversible, native disable for voice.

Commands:
  disable   pkgcmd -D -t <type> -n <id> --global for every voice package
  enable    pkgcmd -A -t <type> -n <id> --global (full reversal)
  status    show which voice packages are still active + which processes run

Paces each command ~5s to avoid wedging the sdbd bridge. Uses tvrun-slow.py's
injection (60s accept / 180s recv).
"""
import importlib.util
import os
import socket
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))

# Pause between pkgcmd calls -- longer is safer to avoid wedging the sdbd bridge.
PAUSE = int(os.environ.get("VOICE_PAUSE", "15"))

_spec = importlib.util.spec_from_file_location(
    "tvrun_slow", os.path.join(HERE, "tvrun-slow.py"))
_tvrun = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_tvrun)
run = _tvrun.run

# (pkg_type, pkg_id) -- 17 tpk + 2 wgt + 1 rpm = 20.
VOICE = [
    ("tpk", "com.samsung.tv.bixby-context-client"),
    ("tpk", "com.samsung.tv.bixby-promotion"),
    ("tpk", "com.samsung.tv.bixby-prov"),
    ("tpk", "com.samsung.tv.bixbycapsuleviewer"),
    ("tpk", "com.samsung.tv.mybixby"),
    ("tpk", "com.samsung.tv.alexa-client"),
    ("tpk", "com.samsung.tv.wakeup-engine-alexa"),
    ("tpk", "com.samsung.tv.wakeup-engine-bixby"),
    ("tpk", "com.samsung.tv.google-assistant"),
    ("tpk", "com.samsung.tv.ondevice-voice"),
    ("tpk", "com.samsung.tv.voice-instant-app"),
    ("tpk", "com.samsung.tv.farfieldvoice"),
    ("tpk", "com.samsung.tv.voiceassistant-music"),
    ("tpk", "com.samsung.tv.vif"),
    ("tpk", "com.samsung.tv.utterance-recommender-service"),
    ("tpk", "org.tizen.voice-client"),
    ("tpk", "org.tizen.voice-app"),
    ("rpm", "org.tizen.voice-onboarding"),
    ("wgt", "AQKO41xyKP"),      # Amazon Alexa
    ("wgt", "IewQEY143t"),      # Google Duo
]


def run_tv(host, command):
    return run(host, command, host + ":26101")


def _pkgcmd(host, flag, ptype, pid):
    cmd = "pkgcmd %s -t %s -n %s --global" % (flag, ptype, pid)
    for attempt in (1, 2):
        try:
            out = run_tv(host, cmd)
            ok = "val[ok]" in out
            return ok, out
        except socket.timeout:
            print("    (timeout attempt %d, waiting 25s)" % attempt)
            time.sleep(25)
    return False, "(timeout)"


# Packages already disabled in a prior partial run (skip to save time).
DONE = {
    "com.samsung.tv.bixby-prov",
    "com.samsung.tv.bixby-context-client",
    "com.samsung.tv.bixby-promotion",
}


def cmd_disable(host):
    results = []
    for ptype, pid in VOICE:
        if pid in DONE:
            print("%-42s SKIP (already done)" % pid)
            continue
        ok, out = _pkgcmd(host, "-D", ptype, pid)
        results.append((pid, ok))
        print("%-42s %s" % (pid, "OK" if ok else "FAIL"))
        if not ok:
            print("    " + (out.strip().splitlines()[-1][:100] if out.strip() else "    (no output)"))
        time.sleep(PAUSE)
    n_ok = sum(1 for _, ok in results if ok)
    print("=== disabled %d/%d voice packages ===" % (n_ok, len(results)))
    return results


def cmd_enable(host):
    results = []
    for ptype, pid in VOICE:
        ok, out = _pkgcmd(host, "-A", ptype, pid)
        results.append((pid, ok))
        print("%-42s %s" % (pid, "OK" if ok else "FAIL"))
        if not ok:
            print("    " + (out.strip().splitlines()[-1][:100] if out.strip() else "    (no output)"))
        time.sleep(PAUSE)
    n_ok = sum(1 for _, ok in results if ok)
    print("=== enabled %d/%d voice packages ===" % (n_ok, len(VOICE)))
    return results


def cmd_status(host):
    print("=== running voice processes ===")
    print(run_tv(host, "ps -eo pid,pcpu,pmem,comm | "
                       "grep -iE 'voice|bixby|alexa|google|vif|farfield|wakeup' | grep -v grep"))
    print("=== active voice packages (pkgcmd -s) ===")
    for ptype, pid in VOICE:
        out = run_tv(host, "pkgcmd -s -t %s -n %s" % (ptype, pid))
        active = "not installed" not in out and "disabled" not in out and out.strip() != ""
        # pkgcmd -s returns the pkg info if active; "not found" if not. Heuristic:
        state = "?" if out.strip() == "" else ("active" if "val[ok]" in out or "appid" in out.lower() or "not installed" not in out else "disabled")
        print("%-42s %s" % (pid, state))
        time.sleep(0.5)


if __name__ == "__main__":
    host = os.environ.get("TV_IP")
    if not host:
        sys.exit("Set TV_IP to your TV's address (e.g. TV_IP=192.168.1.20)")
    action = sys.argv[1] if len(sys.argv) > 1 else "status"
    if action == "disable":
        cmd_disable(host)
    elif action == "enable":
        cmd_enable(host)
    elif action == "status":
        cmd_status(host)
    else:
        raise SystemExit("usage: voicectl.py [disable|enable|status]")
