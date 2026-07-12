import json
from typing import Any, Dict

from alphaapollo.core.tools.capx_python_code import execute_capx_python_code
from alphaapollo.core.tools.core import ToolGroup, tool


class EmbodiedRobosuiteToolGroup(ToolGroup):
    """Tool group that executes code inside a persistent CaP-X Robosuite env."""

    def __init__(self, capx_env: Any, log_requests: bool = False):
        self.capx_env = capx_env
        self.log_requests = log_requests
        super().__init__(name="EmbodiedRobosuiteToolGroup")

    @tool
    def python_code(self, code: str) -> Dict[str, Any]: #把 AlphaApollo 的工具调用转成 CaP-X 的环境执行
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
