#!/bin/bash
cd /opt/app/bmbf-foekat/
set -a
. .env
set +a
args=($CRON_ARGS_FOEKAT)
/usr/local/bin/python3 foekat_farmer.py "${args[@]}"