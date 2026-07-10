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


TASKS = ["cube_lift", "cube_stack", "peg_insertion"]
TOOL_NAMES = [
    "get_object_pose",
    "sample_grasp_pose",
    "goto_pose",
    "open_gripper",
    "close_gripper",
    "goto_home_joint_position",
]


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


def call_chat_completion(
    messages: List[Dict[str, Any]],
    server_url: str,
    model: str,
    api_key: str | None,
    temperature: float,
    max_tokens: int,
    timeout: int,
) -> tuple[str, dict[str, Any]]:
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
    return data["choices"][0]["message"]["content"], data.get("usage", {})


def extract_single_tool_call(text: str) -> str:
    allowed = "|".join(re.escape(name) for name in TOOL_NAMES)
    stripped = (text or "").strip()
    match = re.fullmatch(
        rf"<(?P<tool>{allowed})>(?P<body>.*?)</(?P=tool)>",
        stripped,
        re.IGNORECASE | re.DOTALL,
    )
    if match:
        return match.group(0)
    self_closing = re.fullmatch(rf"<(?P<tool>{allowed})\s*/>", stripped, re.IGNORECASE)
    if self_closing:
        return f"<{self_closing.group('tool')}>{{}}</{self_closing.group('tool')}>"
    missing_closing = re.fullmatch(
        rf"<(?P<tool>{allowed})>(?P<body>\s*\{{.*\}}\s*)",
        stripped,
        re.IGNORECASE | re.DOTALL,
    )
    if missing_closing:
        body = missing_closing.group("body").strip()
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, dict):
            tool = missing_closing.group("tool")
            return f"<{tool}>{body}</{tool}>"
    return stripped


def run_episode(args: argparse.Namespace, task_name: str, trial_idx: int) -> Dict[str, Any]:
    seed = args.seed_start + trial_idx
    cfg = OmegaConf.create(
        {
            "task_name": task_name,
            "max_steps": args.max_turns,
            "record_video": args.record_video,
            "log_requests": False,
        }
    )
    env = EmbodiedRobosuiteEnv(cfg)
    env.reset({"seed": seed, "data_source": task_name})
    prompt, info = env.init([])
    messages: List[Dict[str, Any]] = [
        {
            "role": "system",
            "content": (
                "You control a Robosuite Franka robot through tool calls. "
                "Respond with exactly one XML tool call and no extra text. "
                "Never respond with <python_code>, Python imports, comments, or a multi-step program. "
                "Each turn may call only one S1 primitive. Use JSON arguments inside the tag. "
                "Use prior <tool_response> values for later calls."
            ),
        },
        {"role": "user", "content": prompt[0]["content"]},
    ]

    trajectory: List[Dict[str, Any]] = []
    success = False
    final_reward = 0.0
    error = None
    usage_totals = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    prompt_chars = 0
    completion_chars = 0
    started = time.time()

    try:
        for turn in range(args.max_turns):
            prompt_chars += sum(len(str(message.get("content", ""))) for message in messages)
            model_output, usage = call_chat_completion(
                messages=messages,
                server_url=args.server_url,
                model=args.model,
                api_key=args.api_key,
                temperature=args.temperature,
                max_tokens=args.max_tokens,
                timeout=args.request_timeout,
            )
            completion_chars += len(model_output)
            for key in usage_totals:
                usage_totals[key] += int(usage.get(key, 0) or 0)

            action = extract_single_tool_call(model_output)
            step_out = env.step(action, action)
            reward = float(step_out["reward"])
            done = bool(step_out["done"])
            metadata = step_out.get("metadata", {})
            obs_text = step_out["observations"][0]["content"] if step_out["observations"] else ""

            trajectory.append(
                {
                    "turn": turn,
                    "model_output": model_output,
                    "executed_action": action,
                    "observation": obs_text,
                    "reward": reward,
                    "done": done,
                    "metadata": metadata,
                    "usage": usage,
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

    return {
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
        "usage": usage_totals,
        "prompt_chars": prompt_chars,
        "completion_chars": completion_chars,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", nargs="+", default=TASKS, choices=TASKS)
    parser.add_argument("--trials", type=int, default=30)
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--max-turns", type=int, default=12)
    parser.add_argument("--server-url", default="http://127.0.0.1:8110/chat/completions")
    parser.add_argument("--model", default="qwen3-235b-a22b-instruct-2507")
    parser.add_argument("--api-key", default=os.environ.get("OPENAI_API_KEY"))
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=2048)
    parser.add_argument("--request-timeout", type=int, default=300)
    parser.add_argument("--record-video", action="store_true")
    parser.add_argument("--output-dir", default="outputs/task_bonus_robosuite")
    args = parser.parse_args()

    out_root = Path(args.output_dir)
    out_root.mkdir(parents=True, exist_ok=True)
    all_rows = []

    for task_name in args.tasks:
        task_dir = out_root / task_name
        task_dir.mkdir(parents=True, exist_ok=True)
        successes = 0
        total_turns = 0
        total_tokens = 0
        total_prompt_chars = 0
        total_completion_chars = 0
        for trial_idx in range(args.trials):
            print(f"===== TaskBonus {task_name} trial {trial_idx + 1}/{args.trials} =====", flush=True)
            result = run_episode(args, task_name, trial_idx)
            successes += int(result["success"])
            total_turns += int(result["turns"])
            total_tokens += int(result["usage"].get("total_tokens", 0) or 0)
            total_prompt_chars += int(result["prompt_chars"])
            total_completion_chars += int(result["completion_chars"])
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
            "avg_turns": total_turns / args.trials if args.trials else 0.0,
            "avg_total_tokens": total_tokens / args.trials if args.trials else 0.0,
            "avg_prompt_chars": total_prompt_chars / args.trials if args.trials else 0.0,
            "avg_completion_chars": total_completion_chars / args.trials if args.trials else 0.0,
        }
        all_rows.append(row)
        (task_dir / "summary.json").write_text(json.dumps(row, indent=2))
        print(f"===== Summary {task_name}: {successes}/{args.trials} = {rate:.3f} =====", flush=True)

    summary = {
        "model": args.model,
        "server_url": args.server_url,
        "max_turns": args.max_turns,
        "seed_start": args.seed_start,
        "action_mode": "tool-call-as-action",
        "tasks": all_rows,
    }
    (out_root / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
