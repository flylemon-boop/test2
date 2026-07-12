import json
from typing import Any, Dict

import numpy as np


def get_capx_api_functions(capx_env: Any) -> Dict[str, Any]:
    funcs: Dict[str, Any] = {}
    for api in getattr(capx_env, "_apis", {}).values():
        funcs.update(api.functions())
    return funcs


def jsonable(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    if isinstance(value, tuple):
        return [jsonable(v) for v in value]
    if isinstance(value, list):
        return [jsonable(v) for v in value]
    if isinstance(value, dict):
        return {k: jsonable(v) for k, v in value.items()}
    return value


def pose_dict(result: Any) -> Any:
    if not isinstance(result, tuple) or len(result) < 2:
        return result
    pose = {
        "position": jsonable(result[0]),
        "quaternion_wxyz": jsonable(result[1]),
    }
    if len(result) >= 3 and result[2] is not None:
        pose["bbox_extent"] = jsonable(result[2])
    return pose


def status_payload(
    capx_env: Any,
    status: str,
    result: Any = None,
    stderr: str = "",
) -> Dict[str, Any]:
    reward = float(capx_env.compute_reward())
    low_level = capx_env.low_level_env
    task_completed = (
        low_level.task_completed() if hasattr(low_level, "task_completed") else None
    )
    truncated = getattr(low_level, "_sim_step_count", 0) >= getattr(
        low_level, "max_steps", 999999
    )
    return {
        "status": status,
        "result": jsonable(result),
        "stderr": stderr,
        "reward": reward,
        "terminated": bool(reward == 1.0),
        "truncated": bool(truncated),
        "task_completed": (
            bool(task_completed) if task_completed is not None else None
        ),
    }


def payload_with_pose(capx_env: Any, raw_result: Any) -> Dict[str, Any]:
    return status_payload(capx_env, "success", result=pose_dict(raw_result))


def tool_result(payload: Dict[str, Any], score: int) -> Dict[str, Any]:
    return {"text_result": json.dumps(payload), "score": score}


def execute_named_primitive(
    capx_env: Any,
    name: str,
    **kwargs: Any,
) -> Dict[str, Any]:
    funcs = get_capx_api_functions(capx_env)
    if name not in funcs:
        payload = status_payload(
            capx_env,
            "error",
            stderr=f"Primitive '{name}' is not available.",
        )
        return tool_result(payload, 0)

    try:
        result = funcs[name](**kwargs) #TaskBonus copy/AlphaApollo/cap-x/capx/integrations/franka/control_privileged.py
        payload = status_payload(capx_env, "success", result=pose_dict(result))
        return tool_result(payload, 1)
    except Exception as exc:
        payload = status_payload(capx_env, "error", stderr=repr(exc))
        return tool_result(payload, 0)
