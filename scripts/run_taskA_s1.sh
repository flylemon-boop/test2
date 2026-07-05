#!/usr/bin/env bash
set -euo pipefail

export MUJOCO_GL="${MUJOCO_GL:-egl}"
export PYOPENGL_PLATFORM="${PYOPENGL_PLATFORM:-egl}"

MODEL="${MODEL:-qwen3-235b-a22b-instruct-2507}"
SERVER="${SERVER:-http://127.0.0.1:8110/chat/completions}"
TRIALS="${TRIALS:-30}"
WORKERS="${WORKERS:-1}"
OUT_ROOT="${OUT_ROOT:-outputs/taskA_${MODEL}_${TRIALS}}"
LOG_ROOT="${LOG_ROOT:-outputs/logs}"

mkdir -p "$OUT_ROOT" "$LOG_ROOT"

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
  python capx/envs/launch.py \
    --config-path "$config" \
    --server-url "$SERVER" \
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
