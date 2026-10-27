# Security Policy

## Scope

This project operates on **hardware you own**, over **your own local network**,
using Samsung's **official Developer Mode and SDK tools**. It is an owner-side
utility, not an attack tool.

The administrative-access path it documents:

- requires physical ownership of the device,
- requires Developer Mode to be enabled by the owner,
- requires the same local network,
- cannot affect the display panel or another person's device.

## Reporting a vulnerability

If you discover a security issue **in this project's tooling** (a bug that could
cause data loss, brick a device, or otherwise harm an owner), please report it
responsibly:

1. Open a **private** security advisory (GitHub → Security → Report a
   vulnerability), or email the maintainers.
2. Include: affected script/file, steps to reproduce, and expected vs. actual
   behavior.
3. Allow a reasonable window before public disclosure.

We treat reports seriously and will acknowledge within 48 hours.

## What is out of scope

- The underlying capability path is Samsung's own developer platform, previously
  documented by public research (see README → Prior art). It is not a
  vulnerability in this project and is out of scope here.
- Requests to help bypass DRM, paid features, or to affect devices the reporter
  does not own are **not** accepted.

## Our own commitments

- No destructive operations (no uninstall / delete).
- Every change reversible and documented.
- Clear, calm documentation so owners understand exactly what each step does.
