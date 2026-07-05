import re
from typing import List, Tuple


def embodied_robosuite_projection(actions: List[str]) -> Tuple[List[str], List[int]]:
    results: List[str] = []
    valids: List[int] = [1] * len(actions)
    pattern = re.compile(r"<python_code>(.*?)</python_code>", re.IGNORECASE | re.DOTALL)

    for i, action in enumerate(actions):
        match = pattern.search(action or "")
        if not match:
            results.append("")
            valids[i] = 0
            continue
        results.append(f"<python_code>{match.group(1).strip()}</python_code>")

    return results, valids
