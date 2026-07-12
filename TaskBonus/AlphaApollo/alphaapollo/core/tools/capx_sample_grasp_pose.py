from typing import Any, Dict

from alphaapollo.core.tools.capx_tool_utils import (
    execute_named_primitive,
    get_capx_api_functions,
    payload_with_pose,
    status_payload,
    tool_result,
)


def execute_sample_grasp_pose(capx_env: Any, object_name: str) -> Dict[str, Any]:
    funcs = get_capx_api_functions(capx_env)
    if "sample_grasp_pose" not in funcs:
        return execute_named_primitive(
            capx_env,
            "sample_grasp_pose",
            object_name=object_name,
        )

    try:
        raw_result = funcs["sample_grasp_pose"](object_name=object_name) #TaskBonus/AlphaApollo/third_party/cap-x/capx/integrations/franka/control_privileged.py
        return tool_result(payload_with_pose(capx_env, raw_result), 1)
    except Exception as exc:
        payload = status_payload(capx_env, "error", stderr=repr(exc))
        return tool_result(payload, 0)
