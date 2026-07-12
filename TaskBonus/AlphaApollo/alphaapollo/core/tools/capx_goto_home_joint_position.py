from typing import Any, Dict

from alphaapollo.core.tools.capx_tool_utils import execute_named_primitive


def execute_goto_home_joint_position(capx_env: Any) -> Dict[str, Any]:
    return execute_named_primitive(capx_env, "goto_home_joint_position")
