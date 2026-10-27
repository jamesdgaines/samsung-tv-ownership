#!/usr/bin/env python3
"""Stage the namespace-root-probe artifacts onto the TV.

Writes each file's base64 to a short /tmp path in paced chunks (so the per-chunk
injection stays well under the 400-byte cap), then base64-decodes to the long
final path under /home/owner/share/tmp/sdk_tools/... (which carries the
User::App::Shared SMACK label that dotnet can read). Read-only TV state except
for the staging directories we created.
"""
import base64
import os
import sys
import time

from tvrun import run

HOST = os.environ["TV_IP"]
SERIAL = HOST + ":26101"
CHUNK = 72  # safe for the short /tmp temp path

BASE = "/home/owner/share/tmp/sdk_tools"

FILES = [
    ("rootproof/stage/codex-namespace-proof/RootIdentity.dll",
     BASE + "/codex-namespace-proof/RootIdentity.dll"),
    ("rootproof/stage/codex-namespace-proof/RootIdentity.runtimeconfig.json",
     BASE + "/codex-namespace-proof/RootIdentity.runtimeconfig.json"),
    ("rootproof/stage/codex-namespace-proof/RootIdentity.deps.json",
     BASE + "/codex-namespace-proof/RootIdentity.deps.json"),
    ("rootproof/stage/codex-namespace-proof/NamespaceRootProbe.dll",
     BASE + "/codex-namespace-proof/NamespaceRootProbe.dll"),
    ("rootproof/stage/codex-namespace-proof/NamespaceRootProbe.runtimeconfig.json",
     BASE + "/codex-namespace-proof/NamespaceRootProbe.runtimeconfig.json"),
    ("rootproof/stage/codex-namespace-proof/NamespaceRootProbe.deps.json",
     BASE + "/codex-namespace-proof/NamespaceRootProbe.deps.json"),
    ("rootproof/stage/codex-namespace-proof/public.pem",
     BASE + "/codex-namespace-proof/public.pem"),
    ("rootproof/stage/on-demand/codex-namespace-proof.tar.gz",
     BASE + "/on-demand/codex-namespace-proof.tar.gz"),
    ("rootproof/stage/on-demand/codex-namespace-proof.tar.gz.signature",
     BASE + "/on-demand/codex-namespace-proof.tar.gz.signature"),
]


def push_one(local: str, remote: str) -> None:
    data = open(local, "rb").read()
    b64 = base64.b64encode(data).decode()
    tmp = "/tmp/sp.b64"
    run(HOST, "rm -f %s" % tmp, SERIAL)
    for i in range(0, len(b64), CHUNK):
        part = b64[i:i + CHUNK]
        run(HOST, "echo %s >>%s" % (part, tmp), SERIAL)
        time.sleep(0.35)
    out = run(HOST, "base64 -d %s >%s" % (tmp, remote), SERIAL)
    run(HOST, "rm -f %s" % tmp, SERIAL)
    check = run(HOST, "ls -lZ %s" % remote, SERIAL)
    print("  -> %s (%d bytes): %s" % (remote, len(data),
          check.strip().splitlines()[-1] if check.strip() else "NO RESULT"),
          flush=True)


def main():
    for local, remote in FILES:
        if not os.path.exists(local):
            print("MISSING LOCAL: %s" % local, flush=True)
            sys.exit(2)
        print("transfer %s -> %s" % (local, remote), flush=True)
        push_one(local, remote)
        time.sleep(1.0)
    print("STAGING COMPLETE", flush=True)


if __name__ == "__main__":
    main()
