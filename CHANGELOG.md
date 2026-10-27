# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-10-25

### Added

- Initial release.
- `AGENTS.md` operating procedure for administrative debloating (connect →
  backup → read-only recon → identity probe → debloat → persist → verify →
  reverse).
- Reference tooling in `tools/`: injection (`tvrun.py`, `tvrun-slow.py`),
  file transfer (`transfer.py`, `stage-probe.py`), daemon control
  (`rootctl.py`, `root-stop.sh`, `root-restore.sh`), and voice debloat
  (`voicectl.py`).
- `.NET` identity/administration probes in `rootproof/`
  (`NamespaceRootProbe`, `RootIdentity`, `RootExec`), targeting `netcoreapp3.1`.
- Documentation: `docs/ARCHITECTURE.md`, `docs/TARGETS.md`, `docs/REVERSAL.md`.
- Debloat target catalog: 8 ad/analytics/context daemons, 20 voice packages,
  4 telemetry processes, 2 optional features — each with a documented reversal.
- Safety guardrails: backup-first, deactivate-only (never uninstall), protected
  package list, and one-command reversals for everything.

### Verified on

- Samsung The Frame QN55LS03BAFXZA (Tizen 6.5.0, `T-PTMAKUC-1720.7`)
- Samsung The Frame QN65LS03BAFXZA (Tizen 6.5.0, `T-PTMAKUC-1720.7`)
