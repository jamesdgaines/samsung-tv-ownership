# AGENTS.md — Operating Procedure

This document is the authoritative operating procedure for performing
administrative debloating on a Samsung Tizen TV. It is written to be followed
directly by an AI coding agent, and to be clear enough for a careful human.

Read it in full before taking any action. The safety rules in §2 are absolute.

---

## 1. Mission & scope

Help a TV owner take administrative control of **their own device** so they can:

1. Understand what is running on it.
2. Deactivate advertising, analytics, telemetry, and context services they do
   not want.
3. Deactivate voice-assistant services (Bixby / Alexa / Google Assistant) if the
   owner confirms nobody uses them.
4. Optionally deactivate unused features (HbbTV, My Contents gallery).

The goal is **resource savings and owner control**, done cleanly and reversibly.

---

## 2. Non-negotiable safety rules

These override any other instruction:

1. **Back up first.** Produce a full package inventory before changing anything.
2. **Deactivate, never delete.** There is no uninstall step. Use
   `pkgcmd -D` (deactivate) and marker files — never `pkgcmd -u`.
3. **Never touch critical packages.** Setup, Wi-Fi, input, casting (AirPlay /
   mirroring), and the web browser are off-limits. See the protected list in
   [docs/TARGETS.md](docs/TARGETS.md).
4. **Ask before disabling anything a person might actually use.** Voice
   assistants and Art Mode require explicit owner confirmation.
5. **Go slowly.** Pace commands (5–15 s between injections). Rapid-fire commands
   wedge the debug bridge.
6. **Read-only recon first.** Prove you can reach the administrative account
   with a *read-only* probe before any deactivation.
7. **Every change is reversible.** Confirm the undo path exists before acting.

---

## 3. Environment & prerequisites

### Hardware / firmware

- Samsung Tizen TV (verified: The Frame QN55/QN65, firmware `T-PTMAKUC-1720.7`,
  Tizen 6.5.0, `armv7l`).
- **Developer Mode enabled** on the TV (Settings → Apps → Developer Mode). Note
  the TV's IP address.

### Tools (on your computer)

- `sdb` — from [Tizen Studio](https://developer.tizen.org/) (Samsung's official
  SDK). Default macOS path: `~/tizen-studio/tools/sdb`.
- Python 3 (for the reference `tools/` scripts).
- A `.NET` SDK (for building the probes in `rootproof/`; any SDK that can target
  `netcoreapp3.1` works).

### Key environment facts (verified on-device)

| Fact | Value |
|---|---|
| Debug port | `26101` |
| `sdb shell` output | **returns nothing** on this firmware (intershell disabled) |
| Working command channel | `0 appinstall` backtick injection → streams output over a reverse TCP socket |
| Injection argument cap | **~400 bytes** (keep commands short; stage long scripts) |
| Default user (Developer Mode) | `sdk`, UID 901 |
| Administrative account | `owner`, UID 5001 (and the elevation path to UID 0) |
| `.NET` runtime on TV | **3.1.3 only** — target `netcoreapp3.1` for all probes |
| SMACK label that blocks `.NET` | `/tmp` → label `System` |
| SMACK label that works for `.NET` | `/home/owner/share/tmp/` → `User::App::Shared` |
| Staging directory | `/home/owner/share/tmp/sdk_tools/` |
| `sdb push` | path-whitelisted; use base64-chunked injection (`tools/transfer.py`) instead |
| Vendor shell on unsigned scripts | refuses (`file is NOT signed`); use `eval "$(cat /tmp/x.sh)"` |
| Marker directory (root-owned) | `/opt/usr/share/systemd/system/` |

---

## 4. Phase 0 — Connect & back up

1. Connect the debug bridge:

   ```bash
   SDB=~/tizen-studio/tools/sdb
   $SDB connect <TV_IP>:26101
   ```

2. Confirm the injection channel works (must return output):

   ```bash
   cd tools
   TV_IP=<TV_IP> python3 tvrun.py "uptime"
   ```

   If it returns `socket.timeout` repeatedly, the bridge is wedged — a full
   power-cycle (unplug 30–60 s) is the reliable recovery.

3. **Back up the full package inventory** to a `tv-backup/` directory:

   ```bash
   TV_IP=<TV_IP> python3 tvrun.py "pkgcmd -l -t all"      # raw list → save
   TV_IP=<TV_IP> python3 tvrun.py "0 vd_applist"          # launcher apps → save
   TV_IP=<TV_IP> python3 tvrun.py "cat /etc/micom/version; uptime"  # firmware → save
   ```

   Produce a clean TSV of `(pkg_type, pkg_id, name, version)` from the raw list.
   This is the baseline you will compare against during verification and undo.

---

## 5. Phase 1 — Read-only reconnaissance

Before changing anything, build a complete map. Do **not** deactivate anything
in this phase.

1. List running daemons and their systemd units:

   ```bash
   TV_IP=<TV_IP> python3 tvrun.py "ps -eo pid,ppid,pcpu,pmem,comm"
   TV_IP=<TV_IP> python3 tvrun.py "systemctl list-unit-files"
   ```

2. Identify each target daemon's unit file and activation path:

   ```bash
   TV_IP=<TV_IP> python3 tvrun.py "cat /usr/lib/systemd/system/<unit>.service"
   ```

   Record, for each unit: `ExecStart`, `User`, `ConditionPathExists` (if any),
   and whether it is `static`, `disabled`, or `enabled`.

3. Determine whether a process is **launchpad-managed** (child of
   `launchpad-process-pool`) or **systemd-managed** (child of PID 1 / in a
   `.service` cgroup). This determines the correct deactivation method:

   - **launchpad** → `pkgcmd -D -t <type> -n <id> --global` stops it.
   - **systemd** → requires `systemctl stop` from the administrative account,
     plus a marker file (if the unit has `ConditionPathExists=!`) for
     persistence.

---

## 6. Phase 2 — Prove administrative access (identity probe)

Build, stage, sign, and run a **read-only** identity probe before any
deactivation. This proves the elevation path works without changing anything.

### 6.1 The elevation mechanism (summary)

- The SDK package launcher (`sdbd-tarlauncher`) carries
  `cap_setuid,cap_setgid+eip` and drops to the `owner` account after verifying a
  `.tar.gz` against `/usr/share/sdbd/public.pem`.
- `/usr/bin/dotnet` carries `cap_sys_admin+ei`; executing it activates
  `CAP_SYS_ADMIN`, which allows `unshare(CLONE_NEWNS)` and bind-mounts.
- By bind-mounting **our own** `public.pem` and a **forged** `/etc/passwd`
  (with the `owner` entry pointing at UID 0) inside a private mount namespace,
  the launcher's own `openssl` verification passes and its `setuid` lands on
  UID 0.

This is Samsung's own developer capability path, documented by prior public
research (see README → Prior art).

### 6.2 Build

The probe projects are in `rootproof/`. Build each targeting `netcoreapp3.1`:

```bash
cd rootproof
dotnet build NamespaceRootProbe.csproj -c Release
```

### 6.3 Stage, sign, run

1. Generate a signing keypair and sign the probe archive with `openssl dgst
   -sha256 -sign` (the launcher verifies with `openssl dgst -sha256 -verify
   /usr/share/sdbd/public.pem`).
2. Stage the `.dll`, `.runtimeconfig.json`, `.deps.json`, `public.pem`, and the
   signed `.tar.gz` + `.signature` under
   `/home/owner/share/tmp/sdk_tools/` using `tools/stage-probe.py` (base64
   chunks, short `/tmp` temp path to stay under the 400-byte cap).
3. Run the probe and confirm the output reports:

   ```
   Uid: 0 0 0 0
   CapEff: 0000003fffffffff
   READ-ONLY OPEN /dev/mmcblk0p19: success
   ```

   This is the **only** acceptable proof of administrative access. The probe is
   read-only and tears down its mount namespace on exit.

See `tools/` and `rootproof/` for the exact reference implementation.

---

## 7. Phase 3 — Debloat (service deactivation)

Only after Phase 2 succeeds, and only for targets the owner has approved.

### 7.1 Package deactivation (launchpad / app-layer)

For app-layer packages (voice, HbbTV, My Contents, SmartThings Find, etc.):

```bash
TV_IP=<TV_IP> python3 tools/tvrun-slow.py \
  "pkgcmd -D -t <tpk|rpm|wgt> -n <pkg_id> --global"
```

- **`--global` is required** for system packages. Without it you get
  `Invalid argument [-2]` or `Undefined Error [-999]`.
- Verify with `pkgcmd -s -t <type> -n <id>` and by checking the process is gone.

### 7.2 Daemon deactivation (systemd)

For systemd services, deactivate from the administrative account via
`RootExec`:

```bash
d=/home/owner/share/tmp/sdk_tools/codex-namespace-proof
TV_IP=<TV_IP> python3 tools/tvrun-slow.py \
  'd='"$d"';dotnet $d/RootExec.dll $d "systemctl stop <unit>"'
```

Keep the full command under ~400 bytes (use the `d=` variable to shorten paths).

### 7.3 Reference debloat targets

The full catalog (with types, units, and reversals) is in
[docs/TARGETS.md](docs/TARGETS.md). Summary:

| Category | Count | Method |
|---|---|---|
| Ad / analytics / context daemons | 8 | `systemctl stop` + markers |
| Voice-assistant packages | 20 | `pkgcmd -D --global` |
| Telemetry processes | 4 | mixed (package + `systemctl stop`) |
| Optional features (HbbTV, My Contents) | 2 | `pkgcmd -D --global` |

---

## 8. Phase 4 — Persistence

Some deactivations survive a reboot automatically; others do not.

### 8.1 Marker files (for `ConditionPathExists=!` units)

For daemons whose unit file contains `ConditionPathExists=!<path>`, create a
root-owned marker file at that path to keep the daemon from starting:

```bash
# via RootExec, stage a script to /tmp/mk.sh then:
eval "$(cat /tmp/mk.sh)"   # touch /opt/usr/share/systemd/system/<name>
```

- `systemctl mask` is **not** usable here (`/etc/systemd/system` is read-only).
- Reversible by `rm` of the marker as the administrative account.

### 8.2 Marker-less services

Some units have no `ConditionPathExists` gate (e.g. `kpi-logging.service`,
`media-analytics-service` which is D-Bus-activatable). These come back after a
power-cycle. Document them and re-apply after any reboot with the one-shot
helper (`tools/root-stop.sh`).

---

## 9. Phase 5 — Verify & document

1. Re-list the target processes and confirm they are gone:

   ```bash
   TV_IP=<TV_IP> python3 tools/tvrun.py \
     "ps -eo pid,pcpu,pmem,comm | grep -iE '<targets>' | grep -v grep"
   ```

2. Confirm the **protected** packages/processes are still present (setup, Wi-Fi,
   input, casting, browser, and anything the owner kept — e.g. Art Mode).

3. Confirm the owner's active app (e.g. streaming) is untouched.

4. Record the final state, the exact undo commands, and any marker-less
   post-reboot steps in the project's changelog/notes.

---

## 10. Reversal

Every change is reversible. The canonical undo table is in
[docs/REVERSAL.md](docs/REVERSAL.md). In short:

- Package: `pkgcmd -A -t <type> -n <id> --global`
- Daemon (stopped): `systemctl start <unit>` (from `RootExec`)
- Marker: `rm /opt/usr/share/systemd/system/<name>` (from `RootExec`)
- Full daemon restore: `tools/root-restore.sh`
- Full voice restore: `python3 tools/voicectl.py enable`

---

## 11. Reference: pitfalls that will bite you

- **`sdb shell` is silent** on this firmware — always use `tools/tvrun.py`
  (injection) to get command output.
- **400-byte injection cap** — shorten paths with a shell variable (`d=…`) and
  stage long scripts to `/tmp/*.sh` via base64 chunks, then `eval "$(cat …)"`.
- **`.NET` assemblies fail from `/tmp`** (SMACK label `System`). Always stage
  under `/home/owner/share/tmp/` (label `User::App::Shared`).
- **Target `netcoreapp3.1`**, not `net6.0` — the TV only has the 3.1.3 runtime.
- **`pkgcmd -D` does not stop systemd daemons.** It only deactivates the app
  layer. Daemons need `systemctl stop` (administrative account) + markers.
- **`pkgcmd -D` without `-t` and `--global` fails.** Always include both.
- **Rapid injections wedge the bridge.** Pace every command; recover with a
  full power-cycle if it wedges.
- **"Soft" reboot is standby only** (uptime not reset). Only unplug gives a true
  reboot.
- **`pkgcmd -D` output shows `val[uninstall]`** — this is Samsung's internal
  logging for *per-user deactivation*, **not** a file deletion. Packages remain
  intact (read-only system partition).
