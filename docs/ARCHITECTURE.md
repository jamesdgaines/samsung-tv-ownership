# Architecture

How a Samsung Tizen TV is organized, and why that matters for debloating.

## Two layers of software

A Tizen TV runs two distinct layers, and debloating each requires a different
method:

### 1. The app layer (packages)

Applications are packages installed via `pkgcmd` and launched by `launchpad`
(the application launcher). Packages have a **type**:

| Type | Meaning | Examples |
|---|---|---|
| `tpk` | Native Tizen app package | voice apps, Bixby, SmartThings Find |
| `rpm` | System service package | `ug-hbbtv-efl`, `org.tizen.voice-onboarding` |
| `wgt` | Web/widget package | Amazon Alexa, Google Duo |

Deactivating a package with `pkgcmd -D -t <type> -n <id> --global` removes it
from the *active* set. Because launchpad processes are tied to their package,
deactivating the package also stops the process.

> Note: `pkgcmd -D` output shows `val[uninstall]`, but this is Samsung's
> internal logging for *per-user deactivation* — nothing is deleted (the system
> partition is read-only).

### 2. The service layer (systemd daemons)

Background daemons are managed by `systemd` and started at boot, independent of
the app layer. Deactivating a package does **not** stop its systemd daemon.

Each daemon is described by a unit file in `/usr/lib/systemd/system/`:

```
[Unit]
Description=...
ConditionPathExists=!/opt/usr/share/systemd/system/<marker>

[Service]
ExecStart=/opt/usr/apps/<pkg>/bin/<binary>
User=owner
Restart=always
```

Two facts matter:

- **`ConditionPathExists=!<marker>`** — when present, creating a file at
  `<marker>` prevents the daemon from starting. This is Samsung's *native*
  deactivation mechanism, and it is reversible by deleting the marker.
- **No marker gate** — some units have no `ConditionPathExists`; they can still
  be D-Bus-activated or started by a boot script, so they return after a
  power-cycle.

## Accounts and privileges

| Account | UID | Role |
|---|---|---|
| `sdk` | 901 | Developer Mode user (what `sdb` gives you) |
| `owner` | 5001 | The TV's normal user account |
| `root` | 0 | Administrative account (reached via the elevation path) |

The elevation path (documented in [AGENTS.md](../AGENTS.md) §6) uses the
capabilities Samsung's own SDK launcher and `.NET` runtime carry, to reach the
administrative account on the owner's device.

## Storage, SMACK labels, and staging

Tizen uses **SMACK** (Simplified Mandatory Access Control Kernel) labels. The
`.NET` runtime refuses to load assemblies from paths labeled `System`
(e.g. `/tmp`). The correct staging area is:

```
/home/owner/share/tmp/sdk_tools/   → label User::App::Shared
```

All probe `.dll` files and signed archives must be staged there.

## The debug channel

On this firmware, `sdb shell` returns no output (intershell is disabled). The
working channel is the `0 appinstall` backtick injection, which runs a command
as `sdk` and streams output over a reverse TCP socket. This is what
`tools/tvrun.py` automates.

Constraints:

- ~400-byte argument cap (stage long scripts, shorten paths with variables).
- Rapid-fire injections wedge the bridge (pace every command).
- `sdb push` is path-whitelisted (use base64-chunked injection instead).
