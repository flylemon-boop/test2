#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any


SYSTEM_PROMPT = (
    "You control a Robosuite Franka robot through tool calls. "
    "Respond with exactly one XML tool call and no extra text. "
    "Never respond with <python_code>, Python imports, comments, or a multi-step program. "
    "Each turn may call only one S1 primitive. Use JSON arguments inside the tag. "
    "Use prior <tool_response> values for later calls."
)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _initial_user_prompt(episode: dict[str, Any]) -> str | None:
    env_info = episode.get("env_info") or {}
    prompt = env_info.get("prompt") or env_info.get("task_prompt")
    if isinstance(prompt, str):
        return prompt

    trajectory = episode.get("trajectory") or []
    if trajectory:
        first = trajectory[0]
        prompt = first.get("prompt") or first.get("input_prompt")
        if isinstance(prompt, str):
            return prompt
    return None


def episode_to_examples(path: Path, include_failed: bool = False) -> list[dict[str, Any]]:
    episode = _read_json(path)
    if not include_failed and not episode.get("success"):
        return []

    trajectory = episode.get("trajectory") or []
    if not trajectory:
        return []

    user_prompt = _initial_user_prompt(episode)
    if user_prompt is None:
        task = episode.get("task") or path.parent.name
        user_prompt = (
            f"Task: {task}. Use tool-call-as-action. In each turn, output exactly one "
            "XML tool call and no extra text."
        )

    messages: list[dict[str, str]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
    examples: list[dict[str, Any]] = []

    for step in trajectory:
        action = step.get("executed_action") or step.get("model_output")
        if not isinstance(action, str) or not action.strip().startswith("<"):
            break

        examples.append(
            {
                "task": episode.get("task") or path.parent.name,
                "trial": episode.get("trial"),
                "seed": episode.get("seed"),
                "turn": step.get("turn"),
                "source_episode": str(path),
                "messages": messages + [{"role": "assistant", "content": action.strip()}],
            }
        )

        messages.append({"role": "assistant", "content": action.strip()})
        observation = step.get("observation")
        if isinstance(observation, str) and observation.strip():
            messages.append({"role": "user", "content": observation.strip()})

    return examples


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--include-failed", action="store_true")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    examples: list[dict[str, Any]] = []
    episodes = sorted(input_dir.glob("*/episode_*.json"))
    for path in episodes:
        examples.extend(episode_to_examples(path, include_failed=args.include_failed))

    with output.open("w", encoding="utf-8") as f:
        for example in examples:
            f.write(json.dumps(example, ensure_ascii=False) + "\n")

    counts: dict[str, int] = {}
    for example in examples:
        counts[example["task"]] = counts.get(example["task"], 0) + 1

    print(json.dumps({"examples": len(examples), "by_task": counts}, indent=2))


if __name__ == "__main__":
    main()
