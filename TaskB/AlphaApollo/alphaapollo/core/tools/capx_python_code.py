import logging
from typing import Any, Dict


logger = logging.getLogger(__name__)


def execute_capx_python_code(
    capx_env: Any,
    code: str,
    log_requests: bool = False,
) -> Dict[str, Any]:
    """Execute Python code through a persistent CaP-X Robosuite environment."""
    if log_requests:
        logger.info("Executing python_code in CaP-X Robosuite environment")

    _obs, reward, terminated, truncated, info = capx_env.step(code) # TaskB/AlphaApollo/third_party/cap-x/capx/envs/tasks/base.py
    sandbox_rc = info.get("sandbox_rc", 1)
    run_status = "Finished" if sandbox_rc == 0 else "Error"
    return {
        "stdout": info.get("stdout", ""),
        "stderr": info.get("stderr", ""),
        "returncode": sandbox_rc,
        "run_status": run_status,
        "reward": float(reward),
        "terminated": bool(terminated),
        "truncated": bool(truncated),
        "task_completed": (
            bool(info.get("task_completed"))
            if info.get("task_completed") is not None
            else None
        ),
    }
