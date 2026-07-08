#!/usr/bin/env python3
"""Run TaskB through AlphaApollo's API-style loop and env manager.

This runner keeps the AlphaApollo environment path intact:
  EmbodiedRobosuiteEnvironmentManager -> EmbodiedRobosuiteEnv -> python_code tool

The LLM side uses an OpenAI-compatible API, matching AlphaApollo's terminal API
demo style, while avoiding local vLLM model loading.
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

import requests
from omegaconf import OmegaConf
from openai import OpenAI

from alphaapollo.core.environments import make_envs
from alphaapollo.core.environments.env_manager import EmbodiedRobosuiteEnvironmentManager


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
            obs, infos = manager.reset(kwargs=reset_kwargs)
            messages: List[List[Dict[str, str]]] = []
            trajectories: List[List[Dict[str, Any]]] = [[] for _ in range(batch_count)]
            final_rewards = [0.0 for _ in range(batch_count)]
            errors: List[str | None] = [None for _ in range(batch_count)]
            dones = [False for _ in range(batch_count)]
            episode_success = [False for _ in range(batch_count)]

            for prompt_text in obs["text"]:
                messages.append(    # 构造要发送的prompt
                    [
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
                )

            for turn in range(args.max_turns):
                active_indices = [i for i, done in enumerate(dones) if not done]
                if not active_indices:
                    break

                model_outputs: List[str] = ["" for _ in range(batch_count)]
                actions: List[str] = ["" for _ in range(batch_count)]
                for i in active_indices:
                    try:
                        model_outputs[i] = client.generate(messages[i]) # 模型输出如何变成工具调用
                        actions[i] = ensure_python_code(model_outputs[i]) # 保证输出被包装成 <python_code> 动作
                    except Exception as exc:
                        errors[i] = repr(exc)
                        dones[i] = True

                step_actions = [actions[i] if not dones[i] else "" for i in range(batch_count)]
                next_obs, rewards, next_dones, step_infos = manager.step(step_actions, env_dones=dones)

                for i in range(batch_count):
                    if errors[i] and dones[i]:
                        continue
                    reward = float(rewards[i])
                    done = bool(next_dones[i])
                    info = step_infos[i] if i < len(step_infos) else {}
                    obs_text = next_obs["anchor"][i] if i < len(next_obs["anchor"]) else ""
                    tool_infos = info.get("tool_infos", {}) if isinstance(info, dict) else {}
                    task_completed = bool(tool_infos.get("task_completed") or info.get("won"))

                    trajectories[i].append(
                        {
                            "turn": turn,
                            "model_output": model_outputs[i],
                            "executed_action": actions[i],
                            "observation": obs_text,
                            "reward": reward,
                            "done": done,
                            "metadata": info,
                        }
                    )
                    final_rewards[i] = reward
                    episode_success[i] = episode_success[i] or task_completed
                    dones[i] = done or task_completed
                    messages[i].append({"role": "assistant", "content": actions[i]}) #记录轨迹并更新
                    if obs_text:
                        messages[i].append({"role": "user", "content": obs_text})

            for local_idx in range(batch_count):
                trial_idx = batch_start + local_idx
                success = bool(episode_success[local_idx])
                successes += int(success)
                video_path = None
                if args.record_video:
                    try:
                        video_path = save_episode_video(manager, local_idx, out_root, task_name, trial_idx, success)
                    except Exception as exc:
                        errors[local_idx] = f"{errors[local_idx]}; video_error={exc!r}" if errors[local_idx] else f"video_error={exc!r}"

                result = {
                    "task": task_name,
                    "trial": trial_idx,
                    "seed": args.seed_start + trial_idx,
                    "success": success,
                    "final_reward": final_rewards[local_idx],
                    "turns": len(trajectories[local_idx]),
                    "elapsed_sec": time.time() - started,
                    "error": errors[local_idx],
                    "trajectory": trajectories[local_idx],
                    "env_info": infos[local_idx] if local_idx < len(infos) else {},
                    "video_path": video_path,
                }
                all_results.append(result)
                traj_path = task_dir / f"episode_{trial_idx:03d}.json"
                traj_path.write_text(json.dumps(to_jsonable(result), indent=2, ensure_ascii=False))
                print(
                    f"TaskB {task_name} trial {trial_idx + 1}/{args.trials}: "
                    f"success={success} reward={final_rewards[local_idx]:.4f} "
                    f"turns={len(trajectories[local_idx])} error={errors[local_idx]}",
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
        "runner": "alphaapollo_api_manager",
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
