import json
from typing import Any, Dict

import numpy as np

from alphaapollo.core.tools.core import ToolGroup, tool


class EmbodiedToolGroup(ToolGroup):
    """Tool-call-as-action wrappers around CaP-X S1 Robosuite primitives."""

    def __init__(self, capx_env: Any, log_requests: bool = False):
        self.capx_env = capx_env
        self.log_requests = log_requests
        super().__init__(name="EmbodiedToolGroup")
        available = set(self._api_functions())
        self._tool_registry = {
            name: tool_fn
            for name, tool_fn in self._tool_registry.items()
            if name in available
        }

    def _api_functions(self) -> Dict[str, Any]:
        funcs: Dict[str, Any] = {}
        for api in getattr(self.capx_env, "_apis", {}).values():
            funcs.update(api.functions())
        return funcs

    def _jsonable(self, value: Any) -> Any:
        if isinstance(value, np.ndarray):
            return value.tolist()
        if isinstance(value, (np.floating, np.integer)):
            return value.item()
        if isinstance(value, tuple):
            return [self._jsonable(v) for v in value]
        if isinstance(value, list):
            return [self._jsonable(v) for v in value]
        if isinstance(value, dict):
            return {k: self._jsonable(v) for k, v in value.items()}
        return value

    def _status_payload(self, status: str, result: Any = None, stderr: str = "") -> Dict[str, Any]:
        reward = float(self.capx_env.compute_reward())
        low_level = self.capx_env.low_level_env
        task_completed = low_level.task_completed() if hasattr(low_level, "task_completed") else None
        truncated = getattr(low_level, "_sim_step_count", 0) >= getattr(low_level, "max_steps", 999999)
        return {
            "status": status,
            "result": self._jsonable(result),
            "stderr": stderr,
            "reward": reward,
            "terminated": bool(reward == 1.0),
            "truncated": bool(truncated),
            "task_completed": bool(task_completed) if task_completed is not None else None,
        }

    def _pose_dict(self, result: Any) -> Any:
        if not isinstance(result, tuple) or len(result) < 2:
            return result
        pose = {
            "position": self._jsonable(result[0]),
            "quaternion_wxyz": self._jsonable(result[1]),
        }
        if len(result) >= 3 and result[2] is not None:
            pose["bbox_extent"] = self._jsonable(result[2])
        return pose

    def _payload_with_pose(self, raw_result: Any) -> Dict[str, Any]:
        result = self._pose_dict(raw_result)
        return self._status_payload("success", result=result)

    def _call_primitive(self, name: str, **kwargs: Any) -> Dict[str, Any]:
        funcs = self._api_functions()
        if name not in funcs:
            return {
                "text_result": json.dumps(
                    self._status_payload("error", stderr=f"Primitive '{name}' is not available.")
                ),
                "score": 0,
            }

        try:
            result = funcs[name](**kwargs)
            payload = self._status_payload("success", result=self._pose_dict(result))
            score = 1
        except Exception as exc:
            payload = self._status_payload("error", stderr=repr(exc))
            score = 0

        return {"text_result": json.dumps(payload), "score": score}

    @tool
    def get_object_pose(self, object_name: str, return_bbox_extent: bool = False) -> Dict[str, Any]:
        kwargs = {"object_name": object_name}
        funcs = self._api_functions()
        if "get_object_pose" in funcs:
            try:
                result = funcs["get_object_pose"](**kwargs, return_bbox_extent=return_bbox_extent)
                return {
                    "text_result": json.dumps(self._payload_with_pose(result)),
                    "score": 1,
                }
            except TypeError:
                try:
                    result = funcs["get_object_pose"](**kwargs)
                    return {
                        "text_result": json.dumps(self._payload_with_pose(result)),
                        "score": 1,
                    }
                except Exception as exc:
                    return {
                        "text_result": json.dumps(self._status_payload("error", stderr=repr(exc))),
                        "score": 0,
                    }
            except Exception as exc:
                return {
                    "text_result": json.dumps(self._status_payload("error", stderr=repr(exc))),
                    "score": 0,
                }
        result = self._call_primitive("get_object_pose", **kwargs)
        return result

    @tool
    def sample_grasp_pose(self, object_name: str) -> Dict[str, Any]:
        funcs = self._api_functions()
        if "sample_grasp_pose" not in funcs:
            return self._call_primitive("sample_grasp_pose", object_name=object_name)
        try:
            raw_result = funcs["sample_grasp_pose"](object_name=object_name)
            return {
                "text_result": json.dumps(self._payload_with_pose(raw_result)),
                "score": 1,
            }
        except Exception as exc:
            return {
                "text_result": json.dumps(self._status_payload("error", stderr=repr(exc))),
                "score": 0,
            }

    @tool
    def goto_pose(
        self,
        position: list[float],
        quaternion_wxyz: list[float],
        z_approach: float = 0.0,
    ) -> Dict[str, Any]:
        return self._call_primitive(
            "goto_pose",
            position=np.asarray(position, dtype=np.float64),
            quaternion_wxyz=np.asarray(quaternion_wxyz, dtype=np.float64),
            z_approach=float(z_approach),
        )

    @tool
    def open_gripper(self) -> Dict[str, Any]:
        return self._call_primitive("open_gripper")

    @tool
    def close_gripper(self) -> Dict[str, Any]:
        return self._call_primitive("close_gripper")

    @tool
    def goto_home_joint_position(self) -> Dict[str, Any]:
        return self._call_primitive("goto_home_joint_position")


EmbodiedRobosuiteToolGroup = EmbodiedToolGroup
