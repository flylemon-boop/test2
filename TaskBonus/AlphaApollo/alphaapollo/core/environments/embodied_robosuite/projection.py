import json
import re
from typing import List, Tuple


TOOL_NAMES = [
    "get_object_pose",
    "sample_grasp_pose",
    "goto_pose",
    "open_gripper",
    "close_gripper",
    "goto_home_joint_position",
]


def embodied_robosuite_projection(actions: List[str]) -> Tuple[List[str], List[int]]:
    # TaskBonus uses one S1 XML tool call per turn, not TaskB's <python_code> mode.
    # This projection normalizes model text into a single tool call and marks invalid actions.
    results: List[str] = []
    valids: List[int] = [1] * len(actions)
    allowed = "|".join(re.escape(name) for name in TOOL_NAMES)
    pattern = re.compile(
        rf"<(?P<tool>{allowed})>(?P<body>.*?)</(?P=tool)>",
        re.IGNORECASE | re.DOTALL,
    )
    missing_closing_pattern = re.compile(
        rf"<(?P<tool>{allowed})>(?P<body>\s*\{{.*\}}\s*)",
        re.IGNORECASE | re.DOTALL,
    )

    for i, action in enumerate(actions):
        stripped = (action or "").strip()
        match = pattern.fullmatch(stripped)
        if not match:
            self_closing = re.fullmatch(
                rf"<(?P<tool>{allowed})\s*/>",
                stripped,
                re.IGNORECASE,
            )
            if self_closing:
                tool = self_closing.group("tool").lower()
                results.append(f"<{tool}>{{}}</{tool}>")
                continue
            missing_closing = missing_closing_pattern.fullmatch(stripped)
            if missing_closing:
                body = missing_closing.group("body").strip()
                try:
                    parsed = json.loads(body)
                except json.JSONDecodeError:
                    parsed = None
                if isinstance(parsed, dict):
                    tool = missing_closing.group("tool").lower()
                    results.append(f"<{tool}>{body}</{tool}>")
                    continue
            results.append("")
            valids[i] = 0
            continue
        tool = match.group("tool").lower()
        body = match.group("body").strip() or "{}"
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            parsed = None
        if not isinstance(parsed, dict):
            results.append("")
            valids[i] = 0
            continue
        results.append(f"<{tool}>{body}</{tool}>")

    return results, valids
