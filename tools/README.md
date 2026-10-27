# Tools

Reference scripts for the debloating workflow. All are plain Python 3 (or small
shell wrappers) and require no third-party packages.

## Setup

Set the TV's IP address once per shell:

```bash
export TV_IP=<your-tv-ip>
```

Every script reads `TV_IP` from the environment. Set it to your own TV's
address (e.g. `TV_IP=192.168.1.20`).

You also need `sdb` from [Tizen Studio](https://developer.tizen.org/) on your
PATH (default macOS path `~/tizen-studio/tools/sdb`).

## Scripts

| Script | Purpose |
|---|---|
| `tvrun.py` | Run one read-only command on the TV and print its output (fast timeouts). |
| `tvrun-slow.py` | Same, but with long timeouts (for slow `pkgcmd`/`systemctl` paths). |
| `transfer.py` | Push a file to the TV via base64-chunked injection (bypasses `sdb push` path whitelist). |
| `stage-probe.py` | Stage the `.NET` probe + signature files into the staging dir. |
| `rootctl.py` | `stop` / `restore` / `status` control for the 8 systemd daemons. |
| `root-stop.sh` | One-shot: re-create markers + stop the daemons (idempotent; re-run after a reboot). |
| `root-restore.sh` | Full reversal: delete markers + start all daemons. |
| `voicectl.py` | `disable` / `enable` / `status` for the 20 voice-assistant packages. |

## Usage examples

```bash
# Read a command's output (injection channel)
TV_IP=<TV_IP> python3 tvrun.py "uptime"
TV_IP=<TV_IP> python3 tvrun.py "ps -eo pid,pcpu,pmem,comm"

# Deactivate a package (note: --global and -t are required)
TV_IP=<TV_IP> python3 tvrun-slow.py "pkgcmd -D -t tpk -n <pkg_id> --global"

# Stop the daemons (administrative account)
TV_IP=<TV_IP> ./root-stop.sh

# Check status
TV_IP=<TV_IP> python3 rootctl.py status
```

## Notes

- Keep injected commands **under ~400 bytes**. For long paths, shorten with a
  shell variable (`d=/home/owner/share/tmp/...`), and stage long scripts to
  `/tmp/*.sh` then `eval "$(cat /tmp/*.sh)"`.
- Pace every command (5–15 s) to avoid wedging the debug bridge.
- `.NET` assemblies must live under `/home/owner/share/tmp/` (SMACK label
  `User::App::Shared`), not `/tmp` (label `System`).

See [../AGENTS.md](../AGENTS.md) for the full procedure.
