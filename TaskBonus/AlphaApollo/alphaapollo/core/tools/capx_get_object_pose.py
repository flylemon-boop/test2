from typing import Any, Dict

from alphaapollo.core.tools.capx_tool_utils import (
    execute_named_primitive,
    get_capx_api_functions,
    payload_with_pose,
    status_payload,
    tool_result,
)


def execute_get_object_pose(
    capx_env: Any,
    object_name: str,
    return_bbox_extent: bool = False,
) -> Dict[str, Any]:
    funcs = get_capx_api_functions(capx_env)
    kwargs = {"object_name": object_name}
    if "get_object_pose" not in funcs:
        return execute_named_primitive(capx_env, "get_object_pose", **kwargs)

    try:
        result = funcs["get_object_pose"](
            **kwargs,
            return_bbox_extent=return_bbox_extent,
        )
        return tool_result(payload_with_pose(capx_env, result), 1)
    except TypeError:
        try:
            result = funcs["get_object_pose"](**kwargs)
            return tool_result(payload_with_pose(capx_env, result), 1)
        except Exception as exc:
            payload = status_payload(capx_env, "error", stderr=repr(exc))
            return tool_result(payload, 0)
    except Exception as exc:
        payload = status_payload(capx_env, "error", stderr=repr(exc))
        return tool_result(payload, 0)
