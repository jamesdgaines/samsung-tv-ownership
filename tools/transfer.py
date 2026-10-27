#!/usr/bin/env python3
"""Transfer a file to the TV via base64 chunked injection into /tmp.

Paced (sleep between chunks) to avoid wedging the sdbd bridge. Reuses the
injection from tvrun.py (same directory). Read-only TV state aside from /tmp.
"""
import base64
import os
import sys
import time

from tvrun import run

HOST = os.environ["TV_IP"]
SERIAL = HOST + ":26101"
CHUNK = 72  # safe base64 chars per injection, under the 400-byte argument cap


def push_bytes(data: bytes, remote: str) -> None:
    b64 = base64.b64encode(data).decode()
    tmp = remote + ".b64"
    run(HOST, "rm -f " + tmp, SERIAL)
    for i in range(0, len(b64), CHUNK):
        part = b64[i:i + CHUNK]
        out = run(HOST, "echo %s >>%s" % (part, tmp), SERIAL)
        if "ok" not in out and out.strip():
            # Some injections return empty on success; just keep pacing.
            pass
        time.sleep(0.4)
    run(HOST, "base64 -d %s >%s" % (tmp, remote), SERIAL)
    run(HOST, "rm -f %s" % tmp, SERIAL)
    run(HOST, "ls -l %s" % remote, SERIAL)


if __name__ == "__main__":
    local = sys.argv[1]
    remote = sys.argv[2]
    data = open(local, "rb").read()
    print("transferring %s (%d bytes) -> %s in %d chunks" %
          (local, len(data), remote, -(-len(base64.b64encode(data).decode()) // CHUNK)),
          flush=True)
    push_bytes(data, remote)
    print("done", flush=True)
