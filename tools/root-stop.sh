#!/bin/bash
# Stop all ad/analytics/context daemons + recreate the 3 marker files (persistent).
# Idempotent: safe to run again after a reboot to re-kill the marker-less daemons
# (activity-inference-service, user-presence, gsl-service, media-analytics-service).
cd "$(dirname "$0")"
TV_IP="${TV_IP:?Set TV_IP to your TV's address}" python3 rootctl.py stop
