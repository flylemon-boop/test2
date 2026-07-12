import json
from typing import Any, Dict

from alphaapollo.core.tools.capx_close_gripper import execute_close_gripper
from alphaapollo.core.tools.capx_get_object_pose import execute_get_object_pose
from alphaapollo.core.tools.capx_goto_home_joint_position import (
    execute_goto_home_joint_position,
)
from alphaapollo.core.tools.capx_goto_pose import execute_goto_pose
from alphaapollo.core.tools.capx_open_gripper import execute_open_gripper
from alphaapollo.core.tools.capx_sample_grasp_pose import execute_sample_grasp_pose
from alphaapollo.core.tools.capx_python_code import execute_capx_python_code
from alphaapollo.core.tools.capx_tool_utils import get_capx_api_functions
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
            if name in available or name == "python_code"
        }

    def _api_functions(self) -> Dict[str, Any]:
        return get_capx_api_functions(self.capx_env)

    @tool
    def python_code(self, code: str) -> Dict[str, Any]:
        if not code or not code.strip():
            return {
                "text_result": json.dumps(
                    {"status": "error", "result": "No code provided."}
                ),
                "score": 0,
            }

        try:
            execution_result = execute_capx_python_code(
                capx_env=self.capx_env,
                code=code,
                log_requests=self.log_requests,
            )
            run_status = execution_result.get("run_status", "Unknown")
            payload = {
                "status": "success" if run_status == "Finished" else "failed",
                "result": execution_result.get("stdout", ""),
                "stderr": execution_result.get("stderr", ""),
                "reward": float(execution_result.get("reward", 0.0)),
                "terminated": bool(execution_result.get("terminated", False)),
                "truncated": bool(execution_result.get("truncated", False)),
                "task_completed": execution_result.get("task_completed"),
            }
            score = 1 if payload["status"] == "success" else 0
        except Exception as exc:
            payload = {
                "status": "error",
                "result": "",
                "stderr": repr(exc),
                "reward": 0.0,
                "terminated": False,
                "truncated": False,
                "task_completed": False,
            }
            score = 0

        return {"text_result": json.dumps(payload), "score": score}

    @tool
    def get_object_pose(self, object_name: str, return_bbox_extent: bool = False) -> Dict[str, Any]:
        return execute_get_object_pose(
            self.capx_env,
            object_name=object_name,
            return_bbox_extent=return_bbox_extent,
        )

    @tool
    def sample_grasp_pose(self, object_name: str) -> Dict[str, Any]:
        return execute_sample_grasp_pose(self.capx_env, object_name=object_name)

    @tool
    def goto_pose(
        self,
        position: list[float],
        quaternion_wxyz: list[float],
        z_approach: float = 0.0,
    ) -> Dict[str, Any]:
        return execute_goto_pose(
            self.capx_env,
            position=position,
            quaternion_wxyz=quaternion_wxyz,
            z_approach=z_approach,
        )

    @tool
    def open_gripper(self) -> Dict[str, Any]:
        return execute_open_gripper(self.capx_env)

    @tool
    def close_gripper(self) -> Dict[str, Any]:
        return execute_close_gripper(self.capx_env)

    @tool
    def goto_home_joint_position(self) -> Dict[str, Any]:
        return execute_goto_home_joint_position(self.capx_env)


EmbodiedRobosuiteToolGroup = EmbodiedToolGroup
