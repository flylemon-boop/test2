#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${SCRIPT_DIR}/AlphaApollo"

if [[ ! -d "${PROJECT_DIR}" ]]; then
  echo "AlphaApollo project directory not found: ${PROJECT_DIR}" >&2
  exit 1
fi

# Optional environment bootstrap. On the remote machine this is usually:
#   /root/autodl-tmp/taskb_env.sh
if [[ -n "${TASKB_ENV:-}" && -f "${TASKB_ENV}" ]]; then
  # shellcheck disable=SC1090
  source "${TASKB_ENV}"
elif [[ -f /root/autodl-tmp/taskb_env.sh ]]; then
  # shellcheck disable=SC1091
  source /root/autodl-tmp/taskb_env.sh
fi

export MUJOCO_GL="${MUJOCO_GL:-egl}"
export PYOPENGL_PLATFORM="${PYOPENGL_PLATFORM:-egl}"

API_CSV="${API_CSV:-}"
for candidate in \
  "${SCRIPT_DIR}/../api.csv" \
  "${SCRIPT_DIR}/api.csv" \
  "/root/autodl-tmp/api.csv"; do
  if [[ -z "${API_CSV}" && -f "${candidate}" ]]; then
    API_CSV="${candidate}"
  fi
done

if [[ -n "${API_CSV}" && -f "${API_CSV}" && ( -z "${OPENAI_API_KEY:-}" || -z "${SERVER:-}" ) ]]; then
  api_env_file="$(mktemp)"
  "${PYTHON:-python}" - "${API_CSV}" >"${api_env_file}" <<'PY'
import csv
import shlex
import sys
from pathlib import Path

kv = {}
with Path(sys.argv[1]).open(newline="", encoding="utf-8-sig") as f:
    for row in csv.reader(f):
        if len(row) >= 2:
            kv[row[0].strip()] = row[1].strip()

if "apiKey" in kv:
    print("export OPENAI_API_KEY=" + shlex.quote(kv["apiKey"]))
base = (kv.get("openAiCompatible") or kv.get("apiHost") or "").rstrip("/")
if base:
    if not base.endswith("/chat/completions"):
        base = base + "/chat/completions"
    print("export SERVER=" + shlex.quote(base))
PY
  # shellcheck disable=SC1090
  source "${api_env_file}"
  rm -f "${api_env_file}"
fi

MODEL="${MODEL:-qwen3-235b-a22b-instruct-2507}"
SERVER="${SERVER:-http://127.0.0.1:8110/chat/completions}"
TASKS="${TASKS:-cube_lift cube_stack peg_insertion}"
TRIALS="${TRIALS:-30}"
BATCH_SIZE="${BATCH_SIZE:-1}"
MAX_TURNS="${MAX_TURNS:-4}"
SEED_START="${SEED_START:-0}"
PYROKI_PORT="${PYROKI_PORT:-8116}"
RECORD_VIDEO="${RECORD_VIDEO:-0}"
PYTHON_BIN="${PYTHON:-python}"
OUT="${OUT:-${SCRIPT_DIR}/results/taskB_${MODEL}_${TRIALS}}"

export PYTHONPATH="${PROJECT_DIR}:${PYTHONPATH:-}"
for candidate in \
  "${PROJECT_DIR}/cap-x" \
  "${SCRIPT_DIR}/cap-x" \
  "${SCRIPT_DIR}/../TaskA/cap-x" \
  "${SCRIPT_DIR}/../cap-x" \
  "${SCRIPT_DIR}/../../cap-x" \
  "/root/autodl-tmp/cap-x"; do
  if [[ -d "${candidate}/capx" ]]; then
    export PYTHONPATH="${candidate}:${PYTHONPATH}"
    break
  fi
done

mkdir -p "${OUT}"
cd "${PROJECT_DIR}"

pyroki_started=0
if ! "${PYTHON_BIN}" -c "import requests; requests.get('http://127.0.0.1:${PYROKI_PORT}/docs', timeout=1).raise_for_status()" >/dev/null 2>&1; then
  echo "Starting PyRoKI IK server on 127.0.0.1:${PYROKI_PORT}"
  "${PYTHON_BIN}" scripts/start_taskB_pyroki_server.py --port "${PYROKI_PORT}" >"${OUT}/pyroki_${PYROKI_PORT}.log" 2>&1 &
  PYROKI_PID=$!
  pyroki_started=1
  trap 'if [[ "${pyroki_started}" == "1" ]]; then kill "${PYROKI_PID}" 2>/dev/null || true; fi' EXIT

  for _ in $(seq 1 60); do
    if "${PYTHON_BIN}" -c "import requests; requests.get('http://127.0.0.1:${PYROKI_PORT}/docs', timeout=1).raise_for_status()" >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done
else
  echo "PyRoKI IK server already running on 127.0.0.1:${PYROKI_PORT}"
fi

video_args=()
if [[ "${RECORD_VIDEO}" == "1" || "${RECORD_VIDEO}" == "true" || "${RECORD_VIDEO}" == "True" ]]; then
  video_args+=(--record-video)
fi
read -r -a task_args <<<"${TASKS}"

"${PYTHON_BIN}" examples/demo/taskB_robosuite_api.py \
  --config examples/configs/demo_taskB_robosuite_api.yaml \
  --tasks "${task_args[@]}" \
  --trials "${TRIALS}" \
  --batch-size "${BATCH_SIZE}" \
  --seed-start "${SEED_START}" \
  --max-steps "${MAX_TURNS}" \
  --base-url "${SERVER}" \
  --model "${MODEL}" \
  --temperature 0.0 \
  --max-tokens 4096 \
  --output-dir "${OUT}" \
  "${video_args[@]}"

"${PYTHON_BIN}" - "${OUT}" <<'PY'
import csv
import json
import sys
from pathlib import Path

out = Path(sys.argv[1])
summary_path = out / "summary.json"
if not summary_path.exists():
    raise SystemExit(f"summary.json not found: {summary_path}")

summary = json.loads(summary_path.read_text())
rows = summary.get("tasks", [])
csv_path = out / "summary.csv"
with csv_path.open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["task", "trials", "successes", "success_rate"])
    writer.writeheader()
    writer.writerows(rows)

print(f"TaskB results saved to: {out}")
print(f"Summary JSON: {summary_path}")
print(f"Summary CSV: {csv_path}")
PY
