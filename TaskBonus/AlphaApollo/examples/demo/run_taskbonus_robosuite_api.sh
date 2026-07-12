#!/usr/bin/env bash
set -euo pipefail

: "${OPENAI_API_KEY:=}"

python3 examples/demo/taskbonus_robosuite_api.py \
  --config examples/configs/demo_taskbonus_robosuite_api.yaml "$@"
