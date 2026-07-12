from typing import Any, Dict

import numpy as np

from alphaapollo.core.tools.capx_tool_utils import execute_named_primitive


def execute_goto_pose(
    capx_env: Any,
    position: list[float],
    quaternion_wxyz: list[float],
    z_approach: float = 0.0,
) -> Dict[str, Any]:
    return execute_named_primitive(
        capx_env,
        "goto_pose",
        position=np.asarray(position, dtype=np.float64),
        quaternion_wxyz=np.asarray(quaternion_wxyz, dtype=np.float64),
        z_approach=float(z_approach),
    )
