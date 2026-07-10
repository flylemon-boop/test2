#!/usr/bin/env bash
set -euo pipefail

source /root/autodl-tmp/taskb_env.sh

MODEL="${MODEL:-qwen3-235b-a22b-instruct-2507}"
SERVER="${SERVER:-http://127.0.0.1:8110/chat/completions}"
TRIALS="${TRIALS:-30}"
MAX_TURNS="${MAX_TURNS:-4}"
SEED_START="${SEED_START:-0}"
OUT="${OUT:-outputs/taskB_${MODEL}_${TRIALS}}"
PYROKI_PORT="${PYROKI_PORT:-8116}"

if ! python -c "import requests; requests.get('http://127.0.0.1:${PYROKI_PORT}/docs', timeout=1).raise_for_status()" >/dev/null 2>&1; then
  echo "Starting PyRoKI IK server on 127.0.0.1:${PYROKI_PORT}"
  python scripts/start_taskB_pyroki_server.py --port "${PYROKI_PORT}" >/tmp/taskB_pyroki_${PYROKI_PORT}.log 2>&1 &
  PYROKI_PID=$!
  trap 'kill ${PYROKI_PID} 2>/dev/null || true' EXIT
  sleep 8
else
  echo "PyRoKI IK server already running on 127.0.0.1:${PYROKI_PORT}"
fi

python scripts/run_taskB_robosuite_eval.py \
  --tasks cube_lift cube_stack peg_insertion \
  --trials "$TRIALS" \
  --seed-start "$SEED_START" \
  --max-turns "$MAX_TURNS" \
  --server-url "$SERVER" \
  --model "$MODEL" \
  --temperature 0.0 \
  --max-tokens 4096 \
  --output-dir "$OUT"
