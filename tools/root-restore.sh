#!/bin/bash
# Full reversal: delete the 3 marker files + start all 8 daemons.
# Returns the TV to its original state (nothing disabled, nothing uninstalled).
cd "$(dirname "$0")"
TV_IP="${TV_IP:?Set TV_IP to your TV's address}" python3 rootctl.py restore
