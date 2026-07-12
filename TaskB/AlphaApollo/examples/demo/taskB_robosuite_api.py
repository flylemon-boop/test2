#!/usr/bin/env python3
"""TaskB Robosuite API runner using AlphaApollo's demo-style API path."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import requests
from omegaconf import OmegaConf
from openai import OpenAI

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

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


class LLMClient:
    def __init__(
        self,
        model_name: str,
        base_url: str,
        api_key: str,
        temperature: float,
        max_tokens: int,
        request_timeout: int,
    ) -> None:
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or "EMPTY"
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.request_timeout = request_timeout
        self._use_raw_chat_endpoint = self.base_url.endswith("/chat/completions")
        self._client = None
        if not self._use_raw_chat_endpoint:
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=normalize_base_url(self.base_url),
                timeout=float(request_timeout),
                max_retries=3,
            )

    def generate(self, user_prompt: str, system_prompt: str = "") -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        if self._use_raw_chat_endpoint:
            headers = {"Content-Type": "application/json"}
            if self.api_key and self.api_key != "EMPTY":
                headers["Authorization"] = f"Bearer {self.api_key}"
            payload = {
                "model": self.model_name,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
            }
            resp = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=self.request_timeout,
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            return content.strip() if content else ""

        assert self._client is not None
        response = self._client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            n=1,
        )
        content = response.choices[0].message.content
        return content.strip() if content else ""


def merge_config(args: argparse.Namespace) -> Dict[str, Any]:
    cfg = {
        "backend": "api",
        "llm": {
            "model_name": args.model,
            "base_url": args.base_url,
            "api_key": args.api_key,
            "temperature": args.temperature,
            "max_tokens": args.max_tokens,
            "request_timeout": args.request_timeout,
            "system_prompt": args.system_prompt,
        },
        "env": {
            "tasks": args.tasks,
            "trials": args.trials,
            "batch_size": args.batch_size,
            "seed_start": args.seed_start,
            "max_steps": args.max_steps,
            "history_length": args.history_length,
            "record_video": args.record_video,
            "log_requests": args.log_requests,
        },
        "output": {
            "dir": args.output_dir,
        },
    }

    if args.config:
        file_cfg = OmegaConf.to_container(OmegaConf.load(args.config), resolve=True)
        cfg = OmegaConf.to_container(
            OmegaConf.merge(OmegaConf.create(file_cfg), OmegaConf.create(cfg)),
            resolve=True,
        )
        if not args.system_prompt:
            cfg["llm"]["system_prompt"] = (
                file_cfg.get("llm", {}).get("system_prompt")
                or cfg["llm"].get("system_prompt", "")
            )

    csv_values = load_api_csv(args.api_csv or os.environ.get("API_CSV", ""))
    if not cfg["llm"]["api_key"]:
        cfg["llm"]["api_key"] = (
            csv_values.get("apiKey") or os.environ.get("OPENAI_API_KEY") or "EMPTY"
        )
    if not cfg["llm"]["base_url"]:
        cfg["llm"]["base_url"] = (
            csv_values.get("openAiCompatible")
            or csv_values.get("apiHost")
            or os.environ.get("SERVER")
            or "https://api.openai.com/v1"
        )

    return cfg


def build_manager(task_name: str, batch_size: int, cfg: Dict[str, Any]) -> EmbodiedRobosuiteEnvironmentManager:
    alpha_cfg = OmegaConf.create(
        {
            "data": {
                "train_batch_size": batch_size,
                "val_batch_size": 1,
            },
            "env": {
                "env_name": "embodied_robosuite",
                "seed": cfg["env"]["seed_start"],
                "max_steps": cfg["env"]["max_steps"],
                "history_length": cfg["env"]["history_length"],
                "rollout": {"n": 1},
                "resources_per_worker": {"num_cpus": 1},
                "embodied_robosuite": {
                    "task_name": task_name,
                    "max_steps": cfg["env"]["max_steps"],
                    "record_video": cfg["env"]["record_video"],
                    "log_requests": cfg["env"]["log_requests"],
                    "video_dir": str(Path(cfg["output"]["dir"]) / task_name / "videos"),
                },
            },
        }
    )
    envs, val_envs = make_envs(alpha_cfg)
    val_envs.envs.close()
    return envs


def save_episode_video(
    manager: EmbodiedRobosuiteEnvironmentManager,
    local_idx: int,
    output_dir: Path,
    task_name: str,
    trial_idx: int,
    success: bool,
) -> str | None:
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


def run_task(task_name: str, client: LLMClient, cfg: Dict[str, Any], out_root: Path) -> Dict[str, Any]:
    task_dir = out_root / task_name
    task_dir.mkdir(parents=True, exist_ok=True)
    trials = int(cfg["env"]["trials"])
    batch_size = int(cfg["env"]["batch_size"])
    successes = 0

    for batch_start in range(0, trials, batch_size):
        batch_count = min(batch_size, trials - batch_start)
        manager = build_manager(task_name, batch_count, cfg)
        started = time.time()
        try:
            reset_kwargs = [
                {
                    "seed": int(cfg["env"]["seed_start"]) + trial_idx,
                    "data_source": task_name,
                }
                for trial_idx in range(batch_start, batch_start + batch_count)
            ]
            obs, _infos = manager.reset(kwargs=reset_kwargs)
            initial_prompts = list(obs["text"])
            dones = [False] * batch_count
            trajectories: List[List[Dict[str, Any]]] = [[] for _ in range(batch_count)]
            final_rewards = [0.0] * batch_count
            success_flags = [False] * batch_count

            for turn in range(int(cfg["env"]["max_steps"])):
                actions = []
                for local_idx in range(batch_count):
                    if dones[local_idx]:
                        actions.append("")
                        continue
                    prompt_text = (
                        initial_prompts[local_idx]
                        + "\n\nCurrent observation:\n"
                        + obs["text"][local_idx]
                    )
                    model_output = client.generate(prompt_text, cfg["llm"]["system_prompt"])
                    actions.append(ensure_python_code(model_output))

                obs, rewards, step_dones, infos = manager.step(actions, env_dones=dones)

                for local_idx in range(batch_count):
                    if dones[local_idx]:
                        continue
                    reward = scalar_float(rewards[local_idx])
                    info = infos[local_idx] if infos else {}
                    tool_infos = info.get("tool_infos", {}) if isinstance(info, dict) else {}
                    won = bool(info.get("won", False)) if isinstance(info, dict) else False
                    final_rewards[local_idx] = reward
                    success_flags[local_idx] = success_flags[local_idx] or won
                    trajectories[local_idx].append(
                        {
                            "turn": turn,
                            "model_output": actions[local_idx],
                            "executed_action": actions[local_idx],
                            "observation": obs["anchor"][local_idx] if obs.get("anchor") else "",
                            "reward": reward,
                            "done": bool(step_dones[local_idx]),
                            "metadata": to_jsonable(tool_infos),
                        }
                    )
                    dones[local_idx] = bool(step_dones[local_idx])

                if all(dones):
                    break

            for local_idx in range(batch_count):
                trial_idx = batch_start + local_idx
                success = bool(success_flags[local_idx])
                successes += int(success)
                video_path = None
                error = None
                if cfg["env"]["record_video"]:
                    try:
                        video_path = save_episode_video(
                            manager, local_idx, out_root, task_name, trial_idx, success
                        )
                    except Exception as exc:
                        error = f"video_error={exc!r}"

                result = {
                    "task": task_name,
                    "trial": trial_idx,
                    "seed": int(cfg["env"]["seed_start"]) + trial_idx,
                    "success": success,
                    "final_reward": final_rewards[local_idx],
                    "turns": len(trajectories[local_idx]),
                    "elapsed_sec": time.time() - started,
                    "error": error,
                    "trajectory": trajectories[local_idx],
                    "video_path": video_path,
                }
                traj_path = task_dir / f"episode_{trial_idx:03d}.json"
                traj_path.write_text(
                    json.dumps(to_jsonable(result), indent=2, ensure_ascii=False)
                )
                print(
                    f"TaskB {task_name} trial {trial_idx + 1}/{trials}: "
                    f"success={success} reward={final_rewards[local_idx]:.4f} "
                    f"turns={len(trajectories[local_idx])} error={error}",
                    flush=True,
                )
        finally:
            manager.envs.close()

    rate = successes / trials if trials else 0.0
    summary = {
        "task": task_name,
        "trials": trials,
        "successes": successes,
        "success_rate": rate,
    }
    (task_dir / "summary.json").write_text(
        json.dumps(to_jsonable(summary), indent=2, ensure_ascii=False)
    )
    print(f"===== Summary {task_name}: {successes}/{trials} = {rate:.3f} =====", flush=True)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TaskB Robosuite API demo runner.")
    parser.add_argument("--config", type=str, default="examples/configs/demo_taskB_robosuite_api.yaml")
    parser.add_argument("--tasks", nargs="+", default=TASKS, choices=TASKS)
    parser.add_argument("--trials", type=int, default=30)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--max-steps", type=int, default=4)
    parser.add_argument("--history-length", type=int, default=2)
    parser.add_argument("--model", default=os.environ.get("MODEL", "qwen3-235b-a22b-instruct-2507"))
    parser.add_argument("--base-url", default=os.environ.get("SERVER", ""))
    parser.add_argument("--api-key", default=os.environ.get("OPENAI_API_KEY", ""))
    parser.add_argument("--api-csv", default=os.environ.get("API_CSV", ""))
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--request-timeout", type=int, default=300)
    parser.add_argument("--system-prompt", type=str, default="")
    parser.add_argument("--record-video", action="store_true")
    parser.add_argument("--log-requests", action="store_true")
    parser.add_argument("--output-dir", default="outputs/taskB_robosuite_api_demo")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = merge_config(args)
    if args.tasks is not None:
        cfg["env"]["tasks"] = args.tasks
    if args.model:
        cfg["llm"]["model_name"] = args.model
    if args.base_url:
        cfg["llm"]["base_url"] = args.base_url
    if args.output_dir:
        cfg["output"]["dir"] = args.output_dir

    out_root = Path(cfg["output"]["dir"])
    out_root.mkdir(parents=True, exist_ok=True)

    client = LLMClient(
        model_name=cfg["llm"]["model_name"],
        base_url=cfg["llm"]["base_url"],
        api_key=cfg["llm"]["api_key"],
        temperature=float(cfg["llm"]["temperature"]),
        max_tokens=int(cfg["llm"]["max_tokens"]),
        request_timeout=int(cfg["llm"]["request_timeout"]),
    )

    rows = [run_task(task_name, client, cfg, out_root) for task_name in cfg["env"]["tasks"]]
    summary = {
        "runner": "alphaapollo_demo_api",
        "model": cfg["llm"]["model_name"],
        "base_url": cfg["llm"]["base_url"],
        "max_steps": cfg["env"]["max_steps"],
        "seed_start": cfg["env"]["seed_start"],
        "batch_size": cfg["env"]["batch_size"],
        "tasks": rows,
    }
    summary_path = out_root / "summary.json"
    summary_path.write_text(json.dumps(to_jsonable(summary), indent=2, ensure_ascii=False))
    print(json.dumps(to_jsonable(summary), indent=2, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
