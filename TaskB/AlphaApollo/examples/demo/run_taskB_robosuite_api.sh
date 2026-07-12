#!/usr/bin/env bash
set -euo pipefail

: "${OPENAI_API_KEY:=}"

python3 examples/demo/taskB_robosuite_api.py \
  --config examples/configs/demo_taskB_robosuite_api.yaml "$@"
