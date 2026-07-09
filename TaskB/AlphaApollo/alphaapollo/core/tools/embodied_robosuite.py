import json
from typing import Any, Dict

from alphaapollo.core.tools.core import ToolGroup, tool


class EmbodiedRobosuiteToolGroup(ToolGroup):
    """Tool group that executes code inside a persistent CaP-X Robosuite env."""

    def __init__(self, capx_env: Any, log_requests: bool = False):
        self.capx_env = capx_env
        self.log_requests = log_requests
        super().__init__(name="EmbodiedRobosuiteToolGroup")

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
            _obs, reward, terminated, truncated, info = self.capx_env.step(code)
            payload = {
                "status": "success" if info.get("sandbox_rc", 1) == 0 else "failed",
                "result": info.get("stdout", ""),
                "stderr": info.get("stderr", ""),
                "reward": float(reward),
                "terminated": bool(terminated),
                "truncated": bool(truncated),
                "task_completed": bool(info.get("task_completed")) if info.get("task_completed") is not None else None,
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
