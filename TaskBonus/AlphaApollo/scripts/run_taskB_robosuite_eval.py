#!/usr/bin/env python3
import argparse
import json
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List

import requests
from omegaconf import OmegaConf

from alphaapollo.core.environments.embodied_robosuite.env import EmbodiedRobosuiteEnv


def save_episode_video(env, output_dir: Path, task_name: str, trial_idx: int, success: bool) -> str | None:
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


TASKS = ["cube_lift", "cube_stack", "peg_insertion"]


def call_chat_completion(
    messages: List[Dict[str, Any]],
    server_url: str,
    model: str,
    api_key: str | None,
    temperature: float,
    max_tokens: int,
    timeout: int,
) -> str:
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    resp = requests.post(server_url, headers=headers, json=payload, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def ensure_python_code(text: str) -> str:
    if re.search(r"<python_code>.*?</python_code>", text or "", re.DOTALL | re.IGNORECASE):
        return text
    # Keep the protocol strict but tolerate models that return raw code.
    return f"<python_code>\n{text}\n</python_code>"


def run_episode(args: argparse.Namespace, task_name: str, trial_idx: int) -> Dict[str, Any]:
    seed = args.seed_start + trial_idx
    cfg = OmegaConf.create(
        {
            "task_name": task_name,
            "max_steps": args.max_turns,
            "record_video": args.record_video,
            "log_requests": False,
        }
    ) #临时创建一个配置对象cfg，然后传给env = EmbodiedRobosuiteEnv(cfg)
    env = EmbodiedRobosuiteEnv(cfg) #为当前episode创建临时环境，env 是一个 EmbodiedRobosuiteEnv 对象。
    # env 是 AlphaApollo 对 CaP-X / Robosuite 机器人任务的封装对象；外层负责文本对话和工具调用，内层负责真正执行 Python 代码控制机器人仿真。
    env.reset({"seed": seed, "data_source": task_name}) #重置当前episode的环境状态
    prompt, info = env.init([])
    '''env.init([])
    ↓
    返回 prompt 和 info

    prompt:
    来自 self.task_prompt
    self.task_prompt:
    来自 env.reset(...) 时 self.capx_env.reset(...) 返回的 obs/info
    再经过 _extract_prompt(...) 整理和追加格式要求

    info:
    来自 self.data_source 和 self.task_name
    self.task_name:
    来自 cfg["task_name"]
    self.data_source:
    来自 env.reset({"data_source": task_name})'''
    messages: List[Dict[str, Any]] = [
        {
            "role": "system",
            "content": (
                "You control a Robosuite Franka robot through Python code. "
                "Respond with exactly one <python_code>...</python_code> block. "
                "Inside the block, write executable Python that may call the available S1 APIs."
            ),
        },
        {"role": "user", "content": prompt[0]["content"]},
    ]#要给模型的prompt
    trajectory: List[Dict[str, Any]] = [] #这是一个轨迹记录列表，用来保存当前 episode 每一轮发生了什么。
    success = False
    final_reward = 0.0
    error = None
    started = time.time()

    try:
        for turn in range(args.max_turns):
            model_output = call_chat_completion(
                messages=messages,
                server_url=args.server_url,
                model=args.model,
                api_key=args.api_key,
                temperature=args.temperature,
                max_tokens=args.max_tokens,
                timeout=args.request_timeout,
            ) #得到需要执行的代码
            action = ensure_python_code(model_output) #保证模型输出一定被包裹在<python_code></python_code>
            step_out = env.step(action, action) #把模型生成的 <python_code> 动作交给环境执行，执行后拿回奖励、是否结束、环境反馈和执行元信息。
            reward = float(step_out["reward"])
            done = bool(step_out["done"])
            metadata = step_out.get("metadata", {})
            obs_text = ""
            if step_out["observations"]:
                obs_text = step_out["observations"][0]["content"]

            trajectory.append(
                {
                    "turn": turn,
                    "model_output": model_output,
                    "executed_action": action,
                    "observation": obs_text,
                    "reward": reward,
                    "done": done,
                    "metadata": metadata,
                }
            )

            final_reward = reward
            success = bool(metadata.get("task_completed"))
            messages.append({"role": "assistant", "content": action})
            if obs_text:
                messages.append({"role": "user", "content": obs_text})
            if done or success:
                break
    except Exception as exc:
        error = repr(exc)
    finally:
        video_path = None
        if args.record_video:
            try:
                video_path = save_episode_video(env, Path(args.output_dir), task_name, trial_idx, success)
            except Exception as video_exc:
                error = f"{error}; video_error={video_exc!r}" if error else f"video_error={video_exc!r}"
        try:
            env.close()
        except Exception:
            pass

    result = {
        "task": task_name,
        "trial": trial_idx,
        "seed": seed,
        "success": success,
        "final_reward": final_reward,
        "turns": len(trajectory),
        "elapsed_sec": time.time() - started,
        "error": error,
        "trajectory": trajectory,
        "env_info": info,
        "video_path": video_path,
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", nargs="+", default=TASKS, choices=TASKS)
    parser.add_argument("--trials", type=int, default=30)
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--max-turns", type=int, default=4)
    parser.add_argument("--server-url", default="http://127.0.0.1:8110/chat/completions")
    parser.add_argument("--model", default="qwen3-235b-a22b-instruct-2507")
    parser.add_argument("--api-key", default=os.environ.get("OPENAI_API_KEY"))
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--request-timeout", type=int, default=300)
    parser.add_argument("--record-video", action="store_true")
    parser.add_argument("--output-dir", default="outputs/taskB_robosuite")
    args = parser.parse_args()

    out_root = Path(args.output_dir)
    out_root.mkdir(parents=True, exist_ok=True)
    all_rows = []

    for task_name in args.tasks:
        task_dir = out_root / task_name
        task_dir.mkdir(parents=True, exist_ok=True)
        successes = 0
        for trial_idx in range(args.trials):
            print(f"===== TaskB {task_name} trial {trial_idx + 1}/{args.trials} =====", flush=True)
            result = run_episode(args, task_name, trial_idx)
            successes += int(result["success"])
            traj_path = task_dir / f"episode_{trial_idx:03d}.json"
            traj_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
            print(
                f"success={result['success']} reward={result['final_reward']:.4f} "
                f"turns={result['turns']} error={result['error']}",
                flush=True,
            )

        rate = successes / args.trials if args.trials else 0.0
        row = {
            "task": task_name,
            "trials": args.trials,
            "successes": successes,
            "success_rate": rate,
        }
        all_rows.append(row)
        (task_dir / "summary.json").write_text(json.dumps(row, indent=2))
        print(f"===== Summary {task_name}: {successes}/{args.trials} = {rate:.3f} =====", flush=True)

    summary = {
        "model": args.model,
        "server_url": args.server_url,
        "max_turns": args.max_turns,
        "seed_start": args.seed_start,
        "tasks": all_rows,
    }
    (out_root / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
