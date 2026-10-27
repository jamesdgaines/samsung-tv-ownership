# Contributing

Thanks for helping more TV owners take control of their own hardware. This
project is deliberately calm, reversible, and well-documented — please keep it
that way.

## Scope

We welcome contributions that:

- **Add support for new models/firmwares** (see below).
- **Improve documentation** (especially `AGENTS.md`, which agents rely on).
- **Add debloat targets** with clear evidence of what they do and how to undo.
- **Harden the tooling** (better pacing, clearer errors, cleaner reversals).
- **Fix bugs** in the reference scripts.

We will **not** accept contributions that:

- Bypass DRM, enable piracy, or access paid content.
- Touch other people's devices or operate remotely without ownership.
- Remove reversibility or add destructive ("uninstall") steps.
- Touch the protected packages (setup, Wi-Fi, input, casting, browser).

## Adding support for a new model / firmware

1. Open an issue with:
   - Model number and firmware version (`cat /etc/micom/version`).
   - Whether Developer Mode / `sdb` work.
   - The output of `pkgcmd -l -t all` (or a sanitized excerpt).
   - The `sdbd-tarlauncher` details if the elevation path differs.

2. Confirm the capability prerequisites on that firmware:
   - `sdbd-tarlauncher` has `cap_setuid,cap_setgid+eip`.
   - `/usr/bin/dotnet` has `cap_sys_admin+ei`.
   - The `.NET` runtime version on the TV.
   - The SMACK label of the intended staging directory.

3. Add a row to the **Supported devices** table in `README.md` and a note in
   `CHANGELOG.md`.

## Development workflow

1. Fork and branch from `main`.
2. Follow the style of the existing scripts (plain Python 3, `TV_IP` env var,
   no hard-coded credentials).
3. Keep every action reversible and documented.
4. Open a PR with a description of what changed and why.

## Code of conduct

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Be kind; this is a project about
helping people, not about scoring points.

## License

By contributing, you agree your work is licensed under the same
[MIT](LICENSE) license as the project.
