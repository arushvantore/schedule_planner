#!/bin/sh
# Write today.md once per run. Point launchd (or cron) at this file.
cd "$(dirname "$0")" || exit 1
exec python3 daily.py
