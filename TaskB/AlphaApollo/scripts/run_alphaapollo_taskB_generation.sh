#!/usr/bin/env bash
set -euo pipefail
set -x

# This is the normal AlphaApollo generation entry for TaskB.
# It enters:
#   alphaapollo/core/generation/verl/trainer/main_generation.py
# then main_generation.py calls:
#   make_envs(config)
#   TrajectoryCollector.multi_turn_loop(...)
#   envs.reset(...)
#   actor_rollout_wg.generate_sequences(...)
#   envs.step(...)

export HYDRA_FULL_ERROR=1
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
export TOKENIZERS_PARALLELISM=true
export NCCL_DEBUG=WARN
export no_proxy=localhost,127.0.0.1
export NO_PROXY=localhost,127.0.0.1

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

# AlphaApollo has two import roots:
#   1. PROJECT_ROOT: imports alphaapollo.*
#   2. alphaapollo/core/generation: imports verl.*
export PYTHONPATH="${PROJECT_ROOT}/alphaapollo/core/generation:${PROJECT_ROOT}${PYTHONPATH:+:${PYTHONPATH}}"

# Change this to your local model path.
# Example:
#   MODEL_PATH=/root/autodl-tmp/Qwen2.5-3B-Instruct bash scripts/run_alphaapollo_taskB_generation.sh
MODEL_PATH="${MODEL_PATH:-Qwen/Qwen2.5-3B-Instruct}"

TASK_NAME="${TASK_NAME:-cube_lift}"
OUT_DIR="${OUT_DIR:-outputs/alphaapollo_taskB_generation}"
DATA_PATH="${DATA_PATH:-${OUT_DIR}/one_taskB_prompt.parquet}"
SAVE_PATH="${SAVE_PATH:-${OUT_DIR}/generated.parquet}"
JSON_OUTPUT_PATH="${JSON_OUTPUT_PATH:-${OUT_DIR}/generated.json}"

mkdir -p "${OUT_DIR}"

# Minimal dataset for main_generation.py.
# For TaskB, the real task prompt is produced by envs.reset(), so this prompt can be short.
python - <<'PY'
import os
import pandas as pd

data_path = os.environ["DATA_PATH"]
task_name = os.environ["TASK_NAME"]

row = {
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
        "index": 0,
    },
    "env_kwargs": {
        "seed": 0,
        "data_source": task_name,
    },
}

pd.DataFrame([row]).to_parquet(data_path)
print(f"wrote {data_path}")
PY

python -m alphaapollo.core.generation.verl.trainer.main_generation \
    trainer.nnodes=1 \
    trainer.n_gpus_per_node=1 \
    data.path="${DATA_PATH}" \
    data.prompt_key=prompt \
    data.n_samples=1 \
    data.batch_size=1 \
    data.return_raw_chat=True \
    data.truncation=right \
    data.output_path="${SAVE_PATH}" \
    data.save2json=True \
    data.json_output_path="${JSON_OUTPUT_PATH}" \
    data.dataloader_num_workers=0 \
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
    env.seed=0 \
    env.max_steps=2 \
    env.history_length=2 \
    env.rollout.n=1 \
    env.resources_per_worker.num_cpus=1 \
    env.embodied_robosuite.task_name="${TASK_NAME}" \
    env.embodied_robosuite.max_steps=2 \
    env.embodied_robosuite.record_video=false \
    env.embodied_robosuite.log_requests=false \
    "$@"

