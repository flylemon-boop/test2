import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from omegaconf import DictConfig, OmegaConf

from alphaapollo.core.environments.informal_math_training.base_text_env import (
    BaseTextEnv,
    BaseTextEnvStepOutput,
    ConversationType,
)
from alphaapollo.core.tools.embodied_robosuite import EmbodiedRobosuiteToolGroup


TASK_SPECS = {
    "cube_lift": {
        "env_cls": "capx.envs.tasks.franka.franka_lift.FrankaLiftCodeEnv",
        "low_level_cls": "capx.envs.simulators.robosuite_cube_lift.FrankaRobosuiteCubeLiftLowLevel",
        "api": "FrankaControlPrivilegedApi",
    },
    "cube_lifting": {
        "env_cls": "capx.envs.tasks.franka.franka_lift.FrankaLiftCodeEnv",
        "low_level_cls": "capx.envs.simulators.robosuite_cube_lift.FrankaRobosuiteCubeLiftLowLevel",
        "api": "FrankaControlPrivilegedApi",
    },
    "cube_stack": {
        "env_cls": "capx.envs.tasks.franka.franka_pick_place.FrankaPickPlaceCodeEnv",
        "low_level_cls": "capx.envs.simulators.robosuite_cubes.FrankaRobosuiteCubesLowLevel",
        "api": "FrankaControlPrivilegedApi",
    },
    "peg_insertion": {
        "env_cls": "capx.envs.tasks.franka.franka_nut_assembly.FrankaNutAssemblyCodeEnv",
        "low_level_cls": "capx.envs.simulators.robosuite_nut_assembly.FrankaRobosuiteNutAssembly",
        "api": "FrankaControlNutAssemblyPrivilegedApi",
    },
    "nut_assembly": {
        "env_cls": "capx.envs.tasks.franka.franka_nut_assembly.FrankaNutAssemblyCodeEnv",
        "low_level_cls": "capx.envs.simulators.robosuite_nut_assembly.FrankaRobosuiteNutAssembly",
        "api": "FrankaControlNutAssemblyPrivilegedApi",
    },
}


def _load_symbol(path: str):
    module_name, symbol_name = path.rsplit(".", 1)
    module = __import__(module_name, fromlist=[symbol_name])
    return getattr(module, symbol_name)


def _to_plain_dict(cfg: Any) -> Dict[str, Any]:
    if cfg is None:
        return {}
    if OmegaConf.is_config(cfg):
        return OmegaConf.to_container(cfg, resolve=True) or {}
    return dict(cfg)


class EmbodiedRobosuiteEnv(BaseTextEnv):
    """AlphaApollo text env wrapper around CaP-X Robosuite code execution envs."""

    def __init__(self, env_config: DictConfig):
        super().__init__()
        self.env_config = env_config
        self.task_name = str(getattr(env_config, "task_name", "cube_lift"))
        self.max_steps = int(getattr(env_config, "max_steps", 8))
        self.log_requests = bool(getattr(env_config, "log_requests", False))
        self.record_video = bool(getattr(env_config, "record_video", False))
        self.video_dir = str(getattr(env_config, "video_dir", "outputs/taskB_videos"))
        self.capx_env = self._build_capx_env()
        self.tool_group = EmbodiedRobosuiteToolGroup(
            self.capx_env,
            log_requests=self.log_requests,
        )
        self.init_tool_groups([self.tool_group])
        self.reset({})

    def _build_capx_env(self):
        spec_cfg = _to_plain_dict(getattr(self.env_config, "task_specs", None))
        spec = {**TASK_SPECS.get(self.task_name, {}), **spec_cfg.get(self.task_name, {})}
        if not spec:
            raise ValueError(f"Unsupported embodied Robosuite task: {self.task_name}")

        # Register only the privileged APIs needed by Task B. Importing
        # capx.integrations top-level also imports optional visual APIs.
        from capx.envs.tasks.base import CodeExecEnvConfig
        from capx.integrations.base_api import list_apis, register_api
        from capx.integrations.franka.control_privileged import (
            FrankaControlPrivilegedApi,
        )
        from capx.integrations.franka.nut_assembly_privileged import (
            FrankaControlNutAssemblyPrivilegedApi,
        )

        if "FrankaControlPrivilegedApi" not in list_apis():
            register_api("FrankaControlPrivilegedApi", FrankaControlPrivilegedApi)
        if "FrankaControlNutAssemblyPrivilegedApi" not in list_apis():
            register_api(
                "FrankaControlNutAssemblyPrivilegedApi",
                FrankaControlNutAssemblyPrivilegedApi,
            )

        low_level_cls = _load_symbol(spec["low_level_cls"])
        env_cls = _load_symbol(spec["env_cls"])
        capx_root = Path(__import__("capx").__file__).resolve().parents[1]
        controller_cfg = spec.get(
            "controller_cfg",
            str(
                capx_root
                / "capx/integrations/robosuite/controllers/config/robots/panda_joint_ctrl.json"
            ),
        )
        low_level = low_level_cls(
            controller_cfg=controller_cfg,
            privileged=bool(spec.get("privileged", True)),
            enable_render=bool(spec.get("enable_render", self.record_video)),
            max_steps=int(spec.get("sim_max_steps", 1500)),
        )
        cfg = CodeExecEnvConfig(
            low_level=low_level,
            apis=[spec["api"]],
            privileged=bool(spec.get("privileged", True)),
            enable_render=bool(spec.get("enable_render", self.record_video)),
        )
        return env_cls(cfg)

    def reset(self, extras: Optional[Dict[str, Any]] = None) -> None:
        extras = extras or {}
        self.seed = extras.get("seed")
        self.data_source = extras.get("data_source", self.task_name)
        self.turns = 0
        self.done = False
        self.last_reward = 0.0
        self.last_info: Dict[str, Any] = {}
        self.chat_history: ConversationType = []
        obs, info = self.capx_env.reset(seed=self.seed)
        if self.record_video and hasattr(self.capx_env, "enable_video_capture"):
            self.capx_env.enable_video_capture(True, clear=True)
        self.initial_obs = obs
        self.reset_info = info
        self.task_prompt = self._extract_prompt(obs, info)

    def _extract_prompt(self, obs: Dict[str, Any], info: Dict[str, Any]) -> str:
        full_prompt = obs.get("full_prompt")
        if isinstance(full_prompt, list):
            parts = []
            for message in full_prompt:
                content = message.get("content", "")
                if isinstance(content, list):
                    parts.extend(
                        item.get("text", "") for item in content if isinstance(item, dict)
                    )
                else:
                    parts.append(str(content))
            prompt = "\n".join(part for part in parts if part)
        else:
            prompt = str(info.get("task_prompt") or obs.get("task_prompt") or "")

        return (
            prompt.strip()
            + "\n\nUse <python_code>...</python_code> to execute one Python code block. "
            + "The environment persists across turns; do not reset it inside the episode. "
            + "You may use the listed S1 APIs such as get_object_pose, sample_grasp_pose, "
            + "goto_pose, open_gripper, and close_gripper when available."
        )

    def init(self, prompt: ConversationType) -> Tuple[ConversationType, Dict[str, Any]]:
        return [{"role": "user", "content": self.task_prompt}], {
            "data_source": self.data_source,
            "task_name": self.task_name,
        }

    def _parse_action(self, action: str) -> Tuple[Optional[str], Optional[str]]:
        match = re.search(
            r"<python_code>(.*?)</python_code>",
            action or "",
            re.IGNORECASE | re.DOTALL,
        )
        if not match:
            return None, None
        return "python_code", match.group(1).strip()

    def _is_done(self) -> bool:
        if self.turns >= self.max_steps:
            return True
        if bool(self.last_info.get("terminated")) or bool(self.last_info.get("truncated")):
            return True
        return bool(self.last_info.get("task_completed"))

    def step(self, action: str, text_actions: Optional[str] = None) -> BaseTextEnvStepOutput:
        raw_action = text_actions if isinstance(text_actions, str) else action
        self.turns += 1
        self.chat_history.append(
            {"role": "assistant", "content": raw_action, "text_actions": raw_action}
        )

        tool_name, tool_input = self._parse_action(raw_action)
        if tool_name is None:
            self.done = True
            return BaseTextEnvStepOutput(
                observations=[],
                reward=0.0,
                done=True,
                metadata={
                    "tool_calling": False,
                    "data_source": self.data_source,
                    "error": "No <python_code> block found.",
                },
                postprocessed_action=action,
            )

        tool_output = super()._execute_tool(
            "EmbodiedRobosuiteToolGroup",
            "python_code",
            {"code": tool_input},
        )
        payload = json.loads(tool_output.get("text_result", "{}"))
        self.last_reward = float(payload.get("reward", 0.0))
        self.last_info = payload
        self.done = self._is_done()

        observation = "\n<tool_response>" + json.dumps(payload) + "</tool_response>\n"
        new_obs = {"role": "user", "content": observation, "text_actions": raw_action}
        self.chat_history.append(new_obs)

        metadata = {
            "tool_calling": True,
            "tool_group": "EmbodiedRobosuiteToolGroup",
            "tool_name": "python_code",
            "tool_input": tool_input,
            "data_source": self.data_source,
            "task_name": self.task_name,
            "task_completed": payload.get("task_completed"),
            "terminated": payload.get("terminated"),
            "truncated": payload.get("truncated"),
            "sandbox_status": payload.get("status"),
        }

        return BaseTextEnvStepOutput(
            observations=[new_obs] if not self.done else [],
            reward=self.last_reward,
            done=self.done,
            metadata=metadata,
            postprocessed_action=action,
        )

    def close(self):
        if hasattr(self.capx_env, "close"):
            self.capx_env.close()
