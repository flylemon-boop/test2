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

export HYDRA_FULL_ERROR="${HYDRA_FULL_ERROR:-1}"
export MUJOCO_GL="${MUJOCO_GL:-egl}"
export PYOPENGL_PLATFORM="${PYOPENGL_PLATFORM:-egl}"
export TOKENIZERS_PARALLELISM="${TOKENIZERS_PARALLELISM:-true}"
export NCCL_DEBUG="${NCCL_DEBUG:-WARN}"
export no_proxy="${no_proxy:-localhost,127.0.0.1}"
export NO_PROXY="${NO_PROXY:-localhost,127.0.0.1}"

PYTHON_BIN="${PYTHON:-python}"
TASK_NAME="${TASK_NAME:-cube_lift}"
TASKB_GENERATION_BACKEND="${TASKB_GENERATION_BACKEND:-api}"
TRIALS="${TRIALS:-1}"
SEED_START="${SEED_START:-0}"
MAX_TURNS="${MAX_TURNS:-4}"
PYROKI_PORT="${PYROKI_PORT:-8116}"
MODEL_PATH="${MODEL_PATH:-Qwen/Qwen2.5-3B-Instruct}"
CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
OUT="${OUT:-${SCRIPT_DIR}/results/taskB_generation_${TASK_NAME}_${TRIALS}}"
DATA_PATH="${DATA_PATH:-${OUT}/taskB_generation_prompts.parquet}"
SAVE_PATH="${SAVE_PATH:-${OUT}/generated.parquet}"
JSON_OUTPUT_PATH="${JSON_OUTPUT_PATH:-${OUT}/generated.jsonl}"

if [[ "${TASKB_GENERATION_BACKEND}" == "api" ]]; then
  export TASKS="${TASKS:-${TASK_NAME}}"
  export MODEL="${MODEL:-qwen3-235b-a22b-instruct-2507}"
  echo "TASKB_GENERATION_BACKEND=api: using the same API model as TaskA: ${MODEL}"
  echo "Delegating to ${SCRIPT_DIR}/run_taskB.sh with TASKS=${TASKS}"
  exec "${SCRIPT_DIR}/run_taskB.sh" "$@"
elif [[ "${TASKB_GENERATION_BACKEND}" != "local" ]]; then
  echo "Unsupported TASKB_GENERATION_BACKEND=${TASKB_GENERATION_BACKEND}; expected api or local" >&2
  exit 1
fi

export CUDA_VISIBLE_DEVICES
export TASK_NAME TRIALS SEED_START DATA_PATH

# AlphaApollo has two import roots:
#   1. PROJECT_DIR: imports alphaapollo.*
#   2. alphaapollo/core/generation: imports verl.*
export PYTHONPATH="${PROJECT_DIR}/alphaapollo/core/generation:${PROJECT_DIR}:${PYTHONPATH:-}"
for candidate in \
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

# main_generation.py reads a dataset, but TaskB's real task prompt is produced
# by EmbodiedRobosuiteEnv.reset(). This dataset only supplies per-episode
# metadata such as seed and data_source.
"${PYTHON_BIN}" - <<'PY'
import os
from pathlib import Path

import pandas as pd

data_path = Path(os.environ["DATA_PATH"])
task_name = os.environ["TASK_NAME"]
trials = int(os.environ["TRIALS"])
seed_start = int(os.environ["SEED_START"])

rows = []
for trial_idx in range(trials):
    rows.append(
        {
            "data_source": task_name,
            "prompt": [
                {
                    "role": "user",
                    "content": "Start the embodied Robosuite task.",
                }
            ],
            "reward_model": {
                "style": "rule",
                "ground_truth": "",
            },
            "extra_info": {
                "index": trial_idx,
                "task_name": task_name,
            },
            "env_kwargs": {
                "seed": seed_start + trial_idx,
                "data_source": task_name,
            },
        }
    )

data_path.parent.mkdir(parents=True, exist_ok=True)
pd.DataFrame(rows).to_parquet(data_path)
print(f"wrote {data_path} with {len(rows)} rows")
PY

echo "Running AlphaApollo standard generation entry for TaskB"
echo "  task: ${TASK_NAME}"
echo "  trials/data rows: ${TRIALS}"
echo "  output: ${OUT}"

"${PYTHON_BIN}" -m alphaapollo.core.generation.verl.trainer.main_generation \
  trainer.nnodes=1 \
  trainer.n_gpus_per_node=1 \
  data.path="${DATA_PATH}" \
  data.prompt_key=prompt \
  data.n_samples=1 \
  data.batch_size="${TRIALS}" \
  data.return_raw_chat=True \
  data.truncation=right \
  data.output_path="${SAVE_PATH}" \
  data.save2json=True \
  data.json_output_path="${JSON_OUTPUT_PATH}" \
  +data.dataloader_num_workers=0 \
  model.path="${MODEL_PATH}" \
  rollout.name=vllm \
  rollout.temperature=0.0 \
  rollout.do_sample=False \
  rollout.top_k=-1 \
  rollout.top_p=1.0 \
  rollout.prompt_length=4096 \
  rollout.response_length=2048 \
  rollout.tensor_model_parallel_size=1 \
  rollout.gpu_memory_utilization=0.70 \
  rollout.max_num_batched_tokens=8192 \
  rollout.enforce_eager=True \
  env.env_name=embodied_robosuite \
  env.seed="${SEED_START}" \
  env.max_steps="${MAX_TURNS}" \
  env.history_length=2 \
  env.rollout.n=1 \
  env.resources_per_worker.num_cpus=1 \
  +env.embodied_robosuite.task_name="${TASK_NAME}" \
  +env.embodied_robosuite.max_steps="${MAX_TURNS}" \
  +env.embodied_robosuite.record_video=false \
  +env.embodied_robosuite.log_requests=false \
  "$@"

echo "AlphaApollo generation results saved to: ${OUT}"
echo "Parquet: ${SAVE_PATH}"
echo "JSONL: ${JSON_OUTPUT_PATH}"
