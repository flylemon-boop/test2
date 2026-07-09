#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${SCRIPT_DIR}/cap-x"

if [[ ! -d "${PROJECT_DIR}" ]]; then
  echo "CaP-X project directory not found: ${PROJECT_DIR}" >&2
  exit 1
fi

# Optional environment bootstrap. On the remote machine, taskb_env.sh already
# activates the conda env with the Robosuite/CaP-X dependencies.
if [[ -n "${TASKA_ENV:-}" && -f "${TASKA_ENV}" ]]; then
  # shellcheck disable=SC1090
  source "${TASKA_ENV}"
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
API_KEY="${API_KEY:-${OPENAI_API_KEY:-}}"
TRIALS="${TRIALS:-30}"
WORKERS="${WORKERS:-1}"
OUT_ROOT="${OUT_ROOT:-outputs/taskA_${MODEL}_${TRIALS}}"
LOG_ROOT="${LOG_ROOT:-outputs/logs}"
PYTHON_BIN="${PYTHON:-python}"

cd "${PROJECT_DIR}"

mkdir -p "$OUT_ROOT" "$LOG_ROOT"

api_key_args=()
if [[ -n "${API_KEY}" ]]; then
  api_key_args+=(--api-key "${API_KEY}")
fi

TASKS=(
  "cube_lifting::env_configs/cube_lifting/franka_robosuite_cube_lifting_privileged.yaml"
  "cube_stack::env_configs/cube_stack/franka_robosuite_cube_stack_privileged.yaml"
  "spill_wipe::env_configs/spill_wipe/franka_robosuite_spill_wipe_privileged.yaml"
  "nut_assembly::env_configs/nut_assembly/franka_robosuite_nut_assembly_privileged.yaml"
  "two_arm_lift::env_configs/two_arm_lift/franka_robosuite_two_arm_lift_privileged.yaml"
  "two_arm_handover::env_configs/two_arm_handover/two_arm_handover_privileged.yaml"
)

for item in "${TASKS[@]}"; do
  name="${item%%::*}"
  config="${item#*::}"

  echo "===== Running ${name} ====="
  "${PYTHON_BIN}" capx/envs/launch.py \
    --config-path "$config" \
    --server-url "$SERVER" \
    "${api_key_args[@]}" \
    --model "$MODEL" \
    --total-trials "$TRIALS" \
    --num-workers "$WORKERS" \
    --record-video False \
    --output-dir "${OUT_ROOT}/${name}" \
    2>&1 | tee "${LOG_ROOT}/taskA_${name}_${TRIALS}.log"

  rc="${PIPESTATUS[0]}"
  echo "===== ${name} rc=${rc} ====="
  if [[ "$rc" -ne 0 ]]; then
    exit "$rc"
  fi
done
