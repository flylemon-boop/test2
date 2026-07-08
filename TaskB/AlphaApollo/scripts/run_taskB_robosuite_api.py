#!/usr/bin/env python3
"""Run TaskB through AlphaApollo's rollout loop with an API model backend.

This runner keeps AlphaApollo's multi-turn rollout path intact:
  TrajectoryCollector.multi_turn_loop -> EnvironmentManager -> python_code tool

The model side uses an OpenAI-compatible API worker instead of local vLLM.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import requests
import torch
from omegaconf import OmegaConf
from openai import OpenAI
from tensordict import TensorDict

from alphaapollo.core.environments import make_envs
from alphaapollo.core.environments.env_manager import EmbodiedRobosuiteEnvironmentManager
from alphaapollo.core.generation.multi_turn_rollout import TrajectoryCollector
from alphaapollo.core.generation.verl import DataProto


TASKS = ["cube_lift", "cube_stack", "peg_insertion"]


def to_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    if hasattr(value, "tolist"):
        return value.tolist()
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    return value


def load_api_csv(path: str | None) -> Dict[str, str]:
    if not path:
        return {}
    csv_path = Path(path)
    if not csv_path.exists():
        return {}
    values: Dict[str, str] = {}
    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        for row in csv.reader(f):
            if len(row) >= 2:
                values[row[0].strip()] = row[1].strip()
    return values


def normalize_base_url(url: str) -> str:
    url = url.rstrip("/")
    if url.endswith("/chat/completions"):
        return url[: -len("/chat/completions")]
    return url


class ApiClient:
    def __init__(
        self,
        model: str,
        server_url: str,
        api_key: str | None,
        temperature: float,
        max_tokens: int,
        timeout: int,
    ) -> None:
        self.model = model
        self.server_url = server_url.rstrip("/")
        self.api_key = api_key or "EMPTY"
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self._use_raw_chat_endpoint = self.server_url.endswith("/chat/completions")
        self._client = None
        if not self._use_raw_chat_endpoint:
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=normalize_base_url(self.server_url),
                timeout=float(timeout),
                max_retries=3,
            )

    def generate(self, messages: List[Dict[str, str]]) -> str:   # 请求 OpenAI-compatible API，得到模型文本
        if self._use_raw_chat_endpoint:
            headers = {"Content-Type": "application/json"}
            if self.api_key and self.api_key != "EMPTY":
                headers["Authorization"] = f"Bearer {self.api_key}"
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
            }
            resp = requests.post(
                self.server_url,
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            return content.strip() if content else ""

        assert self._client is not None
        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            n=1,
        )   # 调用的是 OpenAI Python SDK 的聊天补全接口。
        content = response.choices[0].message.content
        return content.strip() if content else ""


def ensure_python_code(text: str) -> str:
    if re.search(r"<python_code>.*?</python_code>", text or "", re.DOTALL | re.IGNORECASE):
        return text
    return f"<python_code>\n{text}\n</python_code>"


def scalar_float(value: Any, default: float = 0.0) -> float:
    if isinstance(value, np.ndarray):
        if value.size == 0:
            return default
        return float(value.astype(float).sum())
    if isinstance(value, (list, tuple)):
        if not value:
            return default
        return float(np.array(value, dtype=float).sum())
    if value is None:
        return default
    return float(value)


class SimpleChatTokenizer:
    """Small reversible tokenizer for API-driven rollout.

    AlphaApollo's TrajectoryCollector expects a tokenizer because the normal
    worker talks in token tensors. For an API backend we only need reversible
    text <-> ids conversion; the remote model does the real tokenization.
    """

    pad_token_id = 0
    eos_token_id = 1
    pad_token = "<pad>"
    eos_token = "<eos>"

    def apply_chat_template(
        self,
        chat,
        add_generation_prompt: bool = True,
        tokenize: bool = False,
        **_: Any,
    ):
        parts = []
        for message in list(chat):
            role = str(message.get("role", "user"))
            content = str(message.get("content", ""))
            parts.append(f"{role}: {content}")
        if add_generation_prompt:
            parts.append("assistant:")
        text = "\n".join(parts)
        return self.encode(text, add_special_tokens=False) if tokenize else text

    def encode(self, text: str, add_special_tokens: bool = False, **_: Any) -> List[int]:
        ids = [ord(ch) + 2 for ch in text]
        if add_special_tokens:
            ids.append(self.eos_token_id)
        return ids

    def decode(self, ids, skip_special_tokens: bool = True, **_: Any) -> str:
        if isinstance(ids, torch.Tensor):
            ids = ids.detach().cpu().tolist()
        chars = []
        for token_id in ids:
            token_id = int(token_id)
            if skip_special_tokens and token_id in {self.pad_token_id, self.eos_token_id}:
                continue
            if token_id >= 2:
                chars.append(chr(token_id - 2))
        return "".join(chars)

    def batch_decode(self, sequences, skip_special_tokens: bool = True, **kwargs: Any) -> List[str]:
        return [self.decode(seq, skip_special_tokens=skip_special_tokens, **kwargs) for seq in sequences]

    def __call__(
        self,
        text: str,
        return_tensors: str | None = None,
        add_special_tokens: bool = False,
        **_: Any,
    ) -> Dict[str, torch.Tensor | List[int]]:
        ids = self.encode(text, add_special_tokens=add_special_tokens)
        attention = [1] * len(ids)
        if return_tensors == "pt":
            return {
                "input_ids": torch.tensor([ids], dtype=torch.long),
                "attention_mask": torch.tensor([attention], dtype=torch.long),
            }
        return {"input_ids": ids, "attention_mask": attention}


class ApiRolloutWorkerGroup:
    """Drop-in worker group for TrajectoryCollector using chat completions API."""

    world_size = 1

    def __init__(self, client: ApiClient, tokenizer: SimpleChatTokenizer, response_length: int):
        self.client = client
        self.tokenizer = tokenizer
        self.response_length = response_length

    def _prompt_to_messages(self, prompt_ids: List[int]) -> List[Dict[str, str]]:
        prompt_text = self.tokenizer.decode(prompt_ids, skip_special_tokens=True)
        if prompt_text.endswith("assistant:"):
            prompt_text = prompt_text[: -len("assistant:")].rstrip()
        if prompt_text.startswith("user:"):
            prompt_text = prompt_text[len("user:"):].strip()
        return [
            {
                "role": "system",
                "content": (
                    "You control a Robosuite Franka robot through Python code. "
                    "Respond with exactly one <python_code>...</python_code> block. "
                    "Inside the block, write executable Python that may call the available S1 APIs."
                ),
            },
            {"role": "user", "content": prompt_text},
        ]

    def generate_sequences(self, prompts: DataProto) -> DataProto:
        prompt_ids_batch = prompts.non_tensor_batch.get("raw_prompt_ids")
        if prompt_ids_batch is None:
            prompt_ids_batch = [
                row.tolist()
                for row in prompts.batch["input_ids"].detach().cpu()
            ]

        responses = []
        for prompt_ids in prompt_ids_batch:
            prompt_ids = list(prompt_ids)
            output = self.client.generate(self._prompt_to_messages(prompt_ids))
            action = ensure_python_code(output)
            response_ids = self.tokenizer.encode(action, add_special_tokens=True)
            response_ids = response_ids[: self.response_length]
            if len(response_ids) < self.response_length:
                response_ids += [self.tokenizer.pad_token_id] * (self.response_length - len(response_ids))
            responses.append(response_ids)

        response = torch.tensor(responses, dtype=torch.long)
        idx = prompts.batch["input_ids"].detach().cpu()
        attention_mask = prompts.batch["attention_mask"].detach().cpu()
        position_ids = prompts.batch["position_ids"].detach().cpu()
        response_attention_mask = (response != self.tokenizer.pad_token_id).long()
        seq = torch.cat([idx, response], dim=-1)
        response_positions = (
            position_ids[:, -1:] + torch.arange(1, response.shape[1] + 1).unsqueeze(0)
        )
        full_attention_mask = torch.cat([attention_mask, response_attention_mask], dim=-1)
        full_position_ids = torch.cat([position_ids, response_positions], dim=-1)
        rollout_log_probs = torch.zeros_like(response, dtype=torch.float32)

        batch = TensorDict(
            {
                "prompts": idx,
                "responses": response,
                "input_ids": seq,
                "rollout_log_probs": rollout_log_probs,
                "attention_mask": full_attention_mask,
                "position_ids": full_position_ids,
            },
            batch_size=response.shape[0],
        )
        return DataProto(batch=batch)


def make_manager(task_name: str, batch_size: int, args: argparse.Namespace) -> EmbodiedRobosuiteEnvironmentManager:
    cfg = OmegaConf.create(
        {
            "data": {
                "train_batch_size": batch_size,
                "val_batch_size": 1,
            },
            "env": {
                "env_name": "embodied_robosuite",
                "seed": args.seed_start,
                "max_steps": args.max_turns,
                "history_length": args.history_length,
                "rollout": {"n": 1},
                "resources_per_worker": {"num_cpus": 1},
                "embodied_robosuite": {
                    "task_name": task_name,
                    "max_steps": args.max_turns,
                    "record_video": args.record_video,
                    "log_requests": args.log_requests,
                    "video_dir": str(Path(args.output_dir) / task_name / "videos"),
                },
            },
        }
    )
    envs, val_envs = make_envs(cfg)
    val_envs.envs.close()
    return envs


def make_rollout_config(task_name: str, batch_size: int, args: argparse.Namespace):
    return OmegaConf.create(
        {
            "data": {
                "max_prompt_length": args.max_prompt_length,
                "max_response_length": args.max_response_length,
                "truncation": "right",
                "return_raw_chat": True,
            },
            "env": {
                "env_name": "embodied_robosuite",
                "seed": args.seed_start,
                "max_steps": args.max_turns,
                "history_length": args.history_length,
                "rollout": {"n": 1},
                "resources_per_worker": {"num_cpus": 1},
                "embodied_robosuite": {
                    "task_name": task_name,
                    "max_steps": args.max_turns,
                    "record_video": args.record_video,
                    "log_requests": args.log_requests,
                    "video_dir": str(Path(args.output_dir) / task_name / "videos"),
                },
            },
            "algorithm": {
                "filter_groups": {"enable": False},
            },
        }
    )


def make_gen_batch(task_name: str, reset_kwargs: List[Dict[str, Any]], tokenizer: SimpleChatTokenizer) -> DataProto:
    batch_size = len(reset_kwargs)
    input_ids = torch.full((batch_size, 1), tokenizer.pad_token_id, dtype=torch.long)
    attention_mask = torch.ones((batch_size, 1), dtype=torch.long)
    position_ids = torch.zeros((batch_size, 1), dtype=torch.long)
    batch = TensorDict(
        {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "position_ids": position_ids,
        },
        batch_size=batch_size,
    )
    non_tensors = {
        "raw_prompt": np.array(
            [[{"role": "user", "content": "Start the embodied Robosuite task."}] for _ in range(batch_size)],
            dtype=object,
        ),
        "index": np.arange(batch_size, dtype=object),
        "data_source": np.array([task_name for _ in range(batch_size)], dtype=object),
        "env_kwargs": np.array(reset_kwargs, dtype=object),
    }
    return DataProto(
        batch=batch,
        non_tensor_batch=non_tensors,
        meta_info={
            "eos_token_id": tokenizer.eos_token_id,
            "pad_token_id": tokenizer.pad_token_id,
            "recompute_log_prob": False,
            "do_sample": False,
            "validate": False,
        },
    )


def save_episode_video(manager: EmbodiedRobosuiteEnvironmentManager, local_idx: int, output_dir: Path, task_name: str, trial_idx: int, success: bool) -> str | None:
    env = manager.envs.envs[local_idx]
    if not hasattr(env.capx_env, "get_video_frames"):
        return None
    frames = env.capx_env.get_video_frames(clear=True)
    if not frames:
        return None
    import imageio.v2 as imageio

    video_dir = output_dir / task_name / "videos"
    video_dir.mkdir(parents=True, exist_ok=True)
    video_path = video_dir / f"episode_{trial_idx:03d}_success_{int(success)}.mp4"
    imageio.mimsave(video_path, frames, fps=20)
    return str(video_path)


def run_task(task_name: str, client: ApiClient, args: argparse.Namespace, out_root: Path) -> Dict[str, Any]:
    task_dir = out_root / task_name
    task_dir.mkdir(parents=True, exist_ok=True)
    successes = 0
    all_results: List[Dict[str, Any]] = []

    for batch_start in range(0, args.trials, args.batch_size):
        batch_count = min(args.batch_size, args.trials - batch_start)
        manager = make_manager(task_name, batch_count, args)
        ''' EmbodiedRobosuiteEnvironmentManager
            └── envs: EmbodiedRobosuiteMultiProcessEnv
                └── envs: list[EmbodiedRobosuiteEnv]
                    ├── EmbodiedRobosuiteEnv # trial 0
                    ├── EmbodiedRobosuiteEnv # trial 1
                    ├── EmbodiedRobosuiteEnv # trial 2
                    └── ...'''
        started = time.time()
        try:
            reset_kwargs = [
                {
                    "seed": args.seed_start + trial_idx,
                    "data_source": task_name,
                }
                for trial_idx in range(batch_start, batch_start + batch_count)
            ]
            tokenizer = SimpleChatTokenizer()
            rollout_cfg = make_rollout_config(task_name, batch_count, args)
            traj_collector = TrajectoryCollector(config=rollout_cfg, tokenizer=tokenizer, processor=None)
            api_rollout_wg = ApiRolloutWorkerGroup(
                client=client,
                tokenizer=tokenizer,
                response_length=args.max_response_length,
            )
            gen_batch = make_gen_batch(task_name, reset_kwargs, tokenizer)
            rollout_output = traj_collector.multi_turn_loop(
                gen_batch=gen_batch,
                actor_rollout_wg=api_rollout_wg,
                envs=manager,
                is_train=False,
            )

            by_index: Dict[int, List[Any]] = {idx: [] for idx in range(batch_count)}
            for item_idx in range(len(rollout_output)):
                item = rollout_output[item_idx]
                index = int(item.non_tensor_batch.get("index", item_idx % batch_count))
                if index in by_index:
                    by_index[index].append(item)

            for local_idx in range(batch_count):
                trial_idx = batch_start + local_idx
                items = by_index.get(local_idx, [])
                trajectory: List[Dict[str, Any]] = []
                final_reward = 0.0
                success = False
                error = None
                for turn, item in enumerate(items):
                    response_ids = item.batch["responses"] if item.batch is not None else []
                    action = tokenizer.decode(response_ids, skip_special_tokens=True)
                    reward = scalar_float(item.non_tensor_batch.get("rewards", 0.0))
                    final_reward = reward
                    success = success or bool(scalar_float(item.non_tensor_batch.get("episode_success", 0.0)))
                    trajectory.append(
                        {
                            "turn": turn,
                            "model_output": action,
                            "executed_action": action,
                            "reward": reward,
                            "metadata": to_jsonable(item.non_tensor_batch),
                        }
                    )
                success = bool(success)
                successes += int(success)
                video_path = None
                if args.record_video:
                    try:
                        video_path = save_episode_video(manager, local_idx, out_root, task_name, trial_idx, success)
                    except Exception as exc:
                        error = f"video_error={exc!r}"

                result = {
                    "task": task_name,
                    "trial": trial_idx,
                    "seed": args.seed_start + trial_idx,
                    "success": success,
                    "final_reward": final_reward,
                    "turns": len(trajectory),
                    "elapsed_sec": time.time() - started,
                    "error": error,
                    "trajectory": trajectory,
                    "env_info": {},
                    "video_path": video_path,
                }
                all_results.append(result)
                traj_path = task_dir / f"episode_{trial_idx:03d}.json"
                traj_path.write_text(json.dumps(to_jsonable(result), indent=2, ensure_ascii=False))
                print(
                    f"TaskB {task_name} trial {trial_idx + 1}/{args.trials}: "
                    f"success={success} reward={final_reward:.4f} "
                    f"turns={len(trajectory)} error={error}",
                    flush=True,
                )
        finally:
            manager.envs.close()

    rate = successes / args.trials if args.trials else 0.0
    summary = {
        "task": task_name,
        "trials": args.trials,
        "successes": successes,
        "success_rate": rate,
    }
    (task_dir / "summary.json").write_text(json.dumps(to_jsonable(summary), indent=2, ensure_ascii=False))
    print(f"===== Summary {task_name}: {successes}/{args.trials} = {rate:.3f} =====", flush=True)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TaskB Robosuite API runner using AlphaApollo env manager.")
    parser.add_argument("--tasks", nargs="+", default=TASKS, choices=TASKS)
    parser.add_argument("--trials", type=int, default=30)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--max-turns", type=int, default=4)
    parser.add_argument("--history-length", type=int, default=2)
    parser.add_argument("--server-url", default=os.environ.get("SERVER", "http://127.0.0.1:8110/chat/completions"))
    parser.add_argument("--model", default=os.environ.get("MODEL", "qwen3-235b-a22b-instruct-2507"))
    parser.add_argument("--api-key", default=os.environ.get("OPENAI_API_KEY"))
    parser.add_argument("--api-csv", default=os.environ.get("API_CSV", ""))
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--max-prompt-length", type=int, default=8192)
    parser.add_argument("--max-response-length", type=int, default=4096)
    parser.add_argument("--request-timeout", type=int, default=300)
    parser.add_argument("--record-video", action="store_true")
    parser.add_argument("--log-requests", action="store_true")
    parser.add_argument("--output-dir", default="outputs/taskB_robosuite_api")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.batch_size < 1:
        raise ValueError("--batch-size must be >= 1")

    csv_values = load_api_csv(args.api_csv)
    if not args.api_key:
        args.api_key = csv_values.get("apiKey") or os.environ.get("OPENAI_API_KEY")
    if not args.server_url:
        args.server_url = csv_values.get("openAiCompatible") or csv_values.get("apiHost") or ""
    if not args.server_url:
        raise ValueError("Missing --server-url or SERVER/openAiCompatible/apiHost.")
    if not args.api_key:
        raise ValueError("Missing --api-key or OPENAI_API_KEY/api.csv apiKey.")

    out_root = Path(args.output_dir)
    out_root.mkdir(parents=True, exist_ok=True)
    client = ApiClient(
        model=args.model,
        server_url=args.server_url,
        api_key=args.api_key,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        timeout=args.request_timeout,
    )

    rows = [run_task(task_name, client, args, out_root) for task_name in args.tasks]
    summary = {
        "runner": "alphaapollo_api_rollout",
        "model": args.model,
        "server_url": args.server_url,
        "max_turns": args.max_turns,
        "seed_start": args.seed_start,
        "batch_size": args.batch_size,
        "tasks": rows,
    }
    summary_path = out_root / "summary.json"
    summary_path.write_text(json.dumps(to_jsonable(summary), indent=2, ensure_ascii=False))
    print(json.dumps(to_jsonable(summary), indent=2, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
