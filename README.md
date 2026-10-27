# Samsung TV Ownership Toolkit

A toolkit for Samsung The Frame TV owners (Tizen). It turns off the background
services you don't want — ads, analytics, telemetry, and voice assistants.

It only works on a TV you own, on your own network. Nothing gets deleted, and
every change can be undone.

---

## Why this exists

Modern Samsung TVs ship with a large set of background services that run 24/7,
even when you're not using them. Many owners simply want to understand and
reduce that footprint. This toolkit gives you:

- **Transparency** — a full inventory of what's actually running and what each
  service is.
- **Control** — the ability to deactivate advertising, analytics, and telemetry
  services you don't want.
- **Reversibility** — every change is a *deactivation*, not a removal, and every
  step has a one-line undo.

The work is done with **administrative access** reached through Samsung's own
developer capabilities — the same account and mechanisms Samsung's update and
launcher services use. Nothing here requires disassembly, and nothing here can
harm the display panel (the panel is a "dumb" screen; the compute lives in the
One Connect box).

---

## What it does / does not do

### ✅ Does

- Enumerate every package and running service on the TV.
- Produce a full backup before any change.
- Deactivate advertising / analytics / context / telemetry services.
- Deactivate voice-assistant services (Bixby, Alexa, Google Assistant) if you
  don't use them.
- Deactivate optional features (HbbTV "red button", the My Contents gallery) if
  you don't use them.
- Make some deactivations persistent across a power-cycle (via Samsung's native
  marker-file mechanism).
- Provide a complete, one-command reversal for every change.

### ❌ Does **not**

- Uninstall or delete anything. All changes are reversible deactivations.
- Touch critical packages: setup, Wi-Fi, input, casting (AirPlay / mirroring),
  or the web browser.
- Modify or bypass DRM, paid apps, or subscriptions.
- Enable piracy or access to content you didn't pay for.
- Affect the display panel or any hardware (the panel cannot be "bricked" this
  way).
- Void anything silently — you are expected to read and understand each step
  (see [AGENTS.md](AGENTS.md)).

---

## Is this normal / safe?

Yes. Taking administrative control of hardware you own — to inspect it and turn
off services you don't want — is a well-established practice for phones, PCs,
and increasingly for smart TVs. The technique described here only works when:

1. You have **physical ownership** of the TV.
2. You have **enabled Developer Mode** (a supported Samsung feature, available
   on every retail unit).
3. You are on the **same local network**.

It does not work remotely, does not affect anyone else's device, and every
change is reversible.

---

## Supported devices

Verified on:

| Model | Firmware | Platform |
|---|---|---|
| Samsung The Frame QN55LS03BAFXZA | T-PTMAKUC-1720.7 | Tizen 6.5.0 (armv7l) |
| Samsung The Frame QN65LS03BAFXZA | T-PTMAKUC-1720.7 | Tizen 6.5.0 (armv7l) |

The general approach applies to Samsung Tizen TVs (2018–2022 and adjacent
years). See [CONTRIBUTING.md](CONTRIBUTING.md) for how to add support for a new
model/firmware.

---

## Quick start

The full, step-by-step operating procedure is in **[AGENTS.md](AGENTS.md)** —
written so an AI coding agent can follow it directly, and detailed enough for a
careful human to follow too.

At a high level:

1. **Enable Developer Mode** on the TV (Settings → Apps → Developer Mode) and
   note the TV's IP address.
2. **Back up** the full package inventory (`tv-backup/`).
3. **Prove administrative access** with a read-only identity probe.
4. **Deactivate** the target services (ad/analytics/voice/telemetry).
5. **Persist** the deactivations you want to survive a reboot.
6. **Verify** and document the final state.

---

## Repository layout

```
samsung-tv-ownership/
├── README.md              ← you are here
├── AGENTS.md              ← the operating procedure (for agents + humans)
├── CONTRIBUTING.md        ← how to add models/firmwares, report issues
├── SECURITY.md            ← scope & responsible-disclosure policy
├── CODE_OF_CONDUCT.md
├── CHANGELOG.md
├── LICENSE
├── docs/
│   ├── ARCHITECTURE.md    ← how the TV is organized (services, packages, markers)
│   ├── TARGETS.md         ← the full debloat target catalog
│   └── REVERSAL.md        ← how to undo every change
├── tools/                 ← reference scripts (injection, transfer, control)
└── rootproof/             ← the .NET identity/administration probes
```

---

## Safety & reversibility

- **Backup first.** The procedure refuses to proceed without a full package
  inventory first.
- **Deactivate, never delete.** There is no "uninstall" step anywhere.
- **Every change has an undo.** See [docs/REVERSAL.md](docs/REVERSAL.md).
- **The display cannot be harmed.** The panel is a passive screen; all compute
  is in the One Connect box, and a soft-brick is recoverable via USB re-flash.

---

## Prior art & credit

The administrative-access technique builds on public research into Samsung's
Tizen developer platform, most notably the [couchroot](https://github.com/splitcipher/couchroot)
project, which first documented the capability path through Samsung's own SDK
launcher and the `.NET` runtime. This project repackages that understanding as
a calm, step-by-step, owner-focused workflow with a strong emphasis on
reversibility and safety.

---

## License

[MIT](LICENSE). Use it on your own hardware, adapt it, share it. Attribution
appreciated.
