# Debloat Target Catalog

The complete, evidence-based catalog of services that can be deactivated. Every
entry lists its type, its deactivation method, its persistence behavior, and its
reversal.

> **Rule:** ask the owner before touching anything a person might use (voice
> assistants, Art Mode). Never touch the **protected** list at the bottom.

---

## 1. Advertising / analytics / context daemons (systemd)

These are the always-on background services responsible for ad targeting,
analytics, and context tracking. They are systemd units and require the
administrative account (`systemctl stop`) plus a marker file for persistence.

| Unit | Package | Marker (persistence) | CPU/RAM freed |
|---|---|---|---|
| `adagent-service` | `com.samsung.tv.pisa-service` | `pisa-service` | ~5.3% / 1.5% |
| `pisa-service` | `com.samsung.tv.pisa-service` | `pisa-service` | ~0.4% |
| `com.samsung.tv.context-aware-service` | context-aware | `com.samsung.tv.context-aware-service` | ~0.8% |
| `com.samsung.tv.context-aware-agent` | context-aware | `com.samsung.tv.context-aware-agent` | ~0.0% |
| `com.samsung.tv.activity-inference-service` | activity-inference | *(none)* | ~0.1% |
| `user-presence` | user-presence | *(none)* | ~0.0% |
| `gsl-service` | gsl-service | *(none)* | ~0.0% |
| `media-analytics-service` | media-analytics | *(none, D-Bus activatable)* | ~0.0% |

- The **marker** is a file at `/opt/usr/share/systemd/system/<name>`; its
  presence makes `ConditionPathExists=!<marker>` fail, so the daemon stays off.
- Units marked *(none)* have no marker gate; they return after a power-cycle and
  must be re-stopped (see `tools/root-stop.sh`).

**Method:** `systemctl stop <unit>` (via `RootExec`), then create markers for
the four gated units.

**Reversal:** `rm` the markers + `systemctl start <unit>` (see
[REVERSAL.md](REVERSAL.md)).

---

## 2. Voice assistants (packages — launchpad)

Disable **only** after the owner confirms nobody uses voice control. All are
`pkgcmd -D -t <type> -n <id> --global`.

| Group | Packages |
|---|---|
| Bixby (5) | `com.samsung.tv.bixby-context-client`, `com.samsung.tv.bixby-promotion`, `com.samsung.tv.bixby-prov`, `com.samsung.tv.bixbycapsuleviewer`, `com.samsung.tv.mybixby` |
| Alexa (3) | `com.samsung.tv.alexa-client`, `com.samsung.tv.wakeup-engine-alexa`, `AQKO41xyKP` (wgt) |
| Google (2) | `com.samsung.tv.google-assistant`, `IewQEY143t` (wgt, Google Duo) |
| Wake / framework (10) | `com.samsung.tv.wakeup-engine-bixby`, `com.samsung.tv.ondevice-voice`, `com.samsung.tv.voice-instant-app`, `com.samsung.tv.farfieldvoice`, `com.samsung.tv.voiceassistant-music`, `com.samsung.tv.vif`, `com.samsung.tv.utterance-recommender-service`, `org.tizen.voice-client`, `org.tizen.voice-app`, `org.tizen.voice-onboarding` (rpm) |

Total: **20 packages** (17 tpk + 2 wgt + 1 rpm).

> `tts-engine-vd-i` (text-to-speech) is **not** included — it serves
> accessibility screen-reading, not the voice assistants.

**Reversal:** `python3 tools/voicectl.py enable`.

---

## 3. Telemetry / logging (mixed)

| Process | Package / unit | Type | Method |
|---|---|---|---|
| `stfind-daemon` | `com.samsung.tv.smartthingsfind-daemon` | tpk (launchpad) | `pkgcmd -D` |
| `emergencyLogTransmitter` | `emergency-log-transmitter` (rpm) **and** `emergency-log-transmitter.service` | both | `pkgcmd -D` + `systemctl stop` |
| `kpi-logging` | `kpi-logging.service` | systemd (no marker) | `systemctl stop` |
| `sp-kpi` | `org.tizen.tv.sp-kpi.service` | systemd (no marker) | `systemctl stop` |

The marker-less systemd units may return after a power-cycle.

---

## 4. Optional features (ask the owner)

| Feature | Package | Type | Ask |
|---|---|---|---|
| HbbTV ("red button" interactive TV) | `ug-hbbtv-efl` | rpm | "Do you use red-button interactive TV?" |
| My Contents gallery | `com.samsung.tv.mycontents` | tpk | "Do you view photos/video off a USB stick?" |

**Do not** disable Art Mode (`DN_izen.art-app`) — it is The Frame's signature
feature; confirm with the owner.

---

## Protected — never touch

These are required for core function or family use. **Do not deactivate:**

- Setup / initial setup (`easysetup-*`, `registertv`, `registerav`,
  `register-device-ux`, `smarthub-reset`)
- Settings (`menu`, `homesetting`, `NetworkSetting`)
- Input & remote (`sboard-app`, `SmartRC`, `virtual-remote`, `PanelKeyApp`,
  `btapp`, `remoteapp`)
- Casting (`airplay-app`, `DN_.multiscreen`, `csfs`, mirroring providers)
- Viewing (`tv-viewer`, `browser`, `EPG`)
- Art Mode (`DN_izen.art-app`)

When in doubt, **ask** and default to *not* touching it.
