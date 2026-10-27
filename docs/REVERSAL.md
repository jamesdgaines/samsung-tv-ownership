# Reversal — undoing every change

Nothing in this project is permanent. Every deactivation has a one-line undo.
This is the canonical reversal table.

## Quick reference

| What was done | Undo command |
|---|---|
| Package deactivated | `pkgcmd -A -t <type> -n <id> --global` |
| Daemon stopped | `systemctl start <unit>` (via `RootExec`) |
| Marker file created | `rm /opt/usr/share/systemd/system/<name>` (via `RootExec`) |
| All 8 daemons | `tools/root-restore.sh` |
| All 20 voice packages | `python3 tools/voicectl.py enable` |

## Full daemon restore (`tools/root-restore.sh`)

Deletes the three markers and starts all eight daemons, returning the TV to its
original always-on state:

```bash
TV_IP=<TV_IP> ./tools/root-restore.sh
```

## Full voice restore

```bash
TV_IP=<TV_IP> python3 tools/voicectl.py enable
```

## Restore telemetry / logging

```bash
# stfind-daemon (package)
TV_IP=<TV_IP> python3 tools/tvrun-slow.py \
  "pkgcmd -A -t tpk -n com.samsung.tv.smartthingsfind-daemon --global"

# emergency-log-transmitter (package)
TV_IP=<TV_IP> python3 tools/tvrun-slow.py \
  "pkgcmd -A -t rpm -n emergency-log-transmitter --global"

# systemd services (via RootExec)
systemctl start emergency-log-transmitter kpi-logging org.tizen.tv.sp-kpi
```

## Restore optional features

```bash
TV_IP=<TV_IP> python3 tools/tvrun-slow.py \
  "pkgcmd -A -t rpm -n ug-hbbtv-efl --global"          # HbbTV

TV_IP=<TV_IP> python3 tools/tvrun-slow.py \
  "pkgcmd -A -t tpk -n com.samsung.tv.mycontents --global"  # My Contents
```

## The one important caveat

`pkgcmd -D` deactivates, it does **not** delete. Packages live on the read-only
system partition and are fully restored by `pkgcmd -A`. If you ever see
`val[uninstall]` in output, that is Samsung's internal logging for per-user
deactivation — not a removal.

The only thing that is *not* automatic is marker-less systemd units (they return
after a power-cycle). Everything else is reversible at any time.
