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
from alphaapollo.core.tools.embodied_robosuite import EmbodiedToolGroup

# TASK_SPECS 把任务名映射到 CaP-X 的高层环境类、底层 robosuite 类和 API 名称。
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


def _load_symbol(path: str): #把 "某个模块.某个类名" 这种字符串，转换成真正可用的 Python 类/函数对象。
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
        self.capx_env = self._build_capx_env() #创建真正的 CaP-X / Robosuite 环境。
        self.tool_group = EmbodiedToolGroup(
            self.capx_env,
            log_requests=self.log_requests,
        ) #把 self.capx_env.step(code) 包装成 AlphaApollo 可以调用的工具。把 AlphaApollo 的“工具调用机制”和 CaP-X 的“执行 Python 控制机器人”机制接起来。
        self.init_tool_groups([self.tool_group]) #把整个工具组挂到当前环境上。
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

        low_level_cls = _load_symbol(spec["low_level_cls"]) #low-level env 类本来就在 CaP-X 里，TaskB 只是根据字符串路径把它们导入出来，并传参数创建实例。
        # 在类似TaskA/cap-x/capx/envs/simulators/robosuite_cube_lift.py:22地方有定义
        env_cls = _load_symbol(spec["env_cls"])
        #"env_cls"定义在 TaskA 的这里：TaskA/cap-x/capx/envs/tasks/franka/franka_lift.py:35 它是一个 CaP-X high-level env 类
        capx_root = Path(__import__("capx").__file__).resolve().parents[1]
        controller_cfg = spec.get(
            "controller_cfg",
            str(
                capx_root
                / "capx/integrations/robosuite/controllers/config/robots/panda_joint_ctrl.json"
            ),
        ) # 告诉 Robosuite：Franka/Panda 机械臂用什么控制器。
        low_level = low_level_cls(
            controller_cfg=controller_cfg,
            privileged=bool(spec.get("privileged", True)),
            enable_render=bool(spec.get("enable_render", self.record_video)),
            max_steps=int(spec.get("sim_max_steps", 1500)),
        ) # 实例化上面拿到的low_level_cls 创建低层 Robosuite 环境
        cfg = CodeExecEnvConfig(   #CodeExecEnvConfig 是 CaP-X 里的配置 dataclass，定义在：TaskA/cap-x/capx/envs/tasks/base.py
            low_level=low_level,
            apis=[spec["api"]],
            privileged=bool(spec.get("privileged", True)),
            enable_render=bool(spec.get("enable_render", self.record_video)),
        ) # 创建 CaP-X 高层代码执行配置
        '''它告诉 high-level env：

        你底下控制的是这个 low_level Robosuite 环境
        你要暴露的 API 是 FrankaControlPrivilegedApi
        你可以使用 privileged 模式
        是否开启渲染取决于 record_video'''
        return env_cls(cfg) #env_cls实际就是FrankaLiftCodeEnv  而 FrankaLiftCodeEnv 定义在 CaP-X 里，
        #例如：TaskA/cap-x/capx/envs/tasks/franka/franka_lift.py:35
        #重点是：FrankaLiftCodeEnv 自己没有写 __init__()，所以当执行：

        #env_cls(cfg)

        #也就是：

        #FrankaLiftCodeEnv(cfg)

        #Python 会自动调用它父类的构造函数：

        #TaskA/cap-x/capx/envs/tasks/base.py:91

        #class CodeExecutionEnvBase(Env):
        #   def __init__(self, cfg: CodeExecEnvConfig) -> None:

        #所以调用链是：

        #EmbodiedRobosuiteEnv.__init__()
        #   ↓
        #self.capx_env = self._build_capx_env()
        # ↓
        #env_cls = _load_symbol(spec["env_cls"])
        # ↓
        #return env_cls(cfg)
        #  ↓
        #FrankaLiftCodeEnv(cfg)
         # ↓
        #因为 FrankaLiftCodeEnv 没有 __init__
        # ↓
        #自动调用 CodeExecutionEnvBase.__init__(cfg)
    def reset(self, extras: Optional[Dict[str, Any]] = None) -> None:
        extras = extras or {}
        self.seed = extras.get("seed")
        self.data_source = extras.get("data_source", self.task_name) #保存 seed 和 data_source
        self.turns = 0
        self.done = False
        self.last_reward = 0.0
        self.last_info: Dict[str, Any] = {}
        self.chat_history: ConversationType = []
        obs, info = self.capx_env.reset(seed=self.seed) #重置底层 cap-X 环境调用的是TaskA/cap-x/capx/envs/tasks/base.py:243
        if self.record_video and hasattr(self.capx_env, "enable_video_capture"):
            self.capx_env.enable_video_capture(True, clear=True)
        self.initial_obs = obs
        self.reset_info = info
        self.task_prompt = self._extract_prompt(obs, info) #得到他的prompt

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

        tool_examples = [
            '<get_object_pose>{"object_name":"red cube","return_bbox_extent":true}</get_object_pose>',
            '<sample_grasp_pose>{"object_name":"red cube"}</sample_grasp_pose>',
            '<goto_pose>{"position":[0.1,0.2,0.3],"quaternion_wxyz":[0,0,1,0],"z_approach":0.1}</goto_pose>',
            "<open_gripper>{}</open_gripper>",
            "<close_gripper>{}</close_gripper>",
            "<goto_home_joint_position>{}</goto_home_joint_position>",
        ]
        available_tools = set(self.tool_group._api_functions())
        visible_examples = [
            example for example in tool_examples if example[1 : example.index(">")] in available_tools
        ]

        return (
            prompt.strip()
            + "\n\nUse tool-call-as-action. In each turn, output exactly one XML tool call "
            + "and no extra text. Ignore any earlier instruction that asks for executable Python. "
            + "Never output <python_code>, imports, assignments, comments, or multi-step programs. "
            + "The environment persists across turns; do not reset it. "
            + "Tool arguments must be JSON inside the XML tag. Available S1 tools:\n"
            + "\n".join(visible_examples)
            + "\n"
            + "Use values returned in <tool_response> for later tool calls. Returned poses have "
            + "named fields position and quaternion_wxyz."
        )

    def init(self, prompt: ConversationType) -> Tuple[ConversationType, Dict[str, Any]]:
        return [{"role": "user", "content": self.task_prompt}], {
            "data_source": self.data_source,
            "task_name": self.task_name,
        }

    def _parse_action(self, action: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        available_tools = set(self.tool_group._api_functions()) # 当前 CaP-X API 真正支持的工具
        registered_tools = set(self.tool_group.get_tool_names()) # 当前 ToolGroup 注册过的工具
        allowed_tools = sorted(registered_tools & available_tools)
        allowed = "|".join(re.escape(name) for name in allowed_tools)
        if not allowed:
            return None, None
        match = re.fullmatch(
            rf"<(?P<tool>{allowed})>(?P<body>.*?)</(?P=tool)>",
            (action or "").strip(),
            re.IGNORECASE | re.DOTALL,
        )
        if not match:
            self_closing = re.fullmatch(
                rf"<(?P<tool>{allowed})\s*/>", (action or "").strip(), re.IGNORECASE
            )
            if self_closing:
                return self_closing.group("tool").lower(), {}
            return None, None

        body = match.group("body").strip()
        if not body:
            return match.group("tool").lower(), {}
        try:
            tool_input = json.loads(body)
        except json.JSONDecodeError:
            return None, None
        if not isinstance(tool_input, dict):
            return None, None
        return match.group("tool").lower(), tool_input

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

        tool_name, tool_input = self._parse_action(raw_action) #提取单步工具调用
        if tool_name is None:
            self.done = True
            return BaseTextEnvStepOutput(
                observations=[],
                reward=0.0,
                done=True,
                metadata={
                    "tool_calling": False,
                    "data_source": self.data_source,
                    "error": "No valid single S1 tool call found.",
                },
                postprocessed_action=action,
            )

        tool_output = super()._execute_tool(
            "EmbodiedToolGroup",
            tool_name,
            tool_input or {},
        ) #调用单个原语工具执行
        payload = json.loads(tool_output.get("text_result", "{}")) #解析执行结果
        self.last_reward = float(payload.get("reward", 0.0))
        self.last_info = payload
        self.done = self._is_done()

        observation = "\n<tool_response>" + json.dumps(payload) + "</tool_response>\n"
        new_obs = {"role": "user", "content": observation, "text_actions": raw_action}
        self.chat_history.append(new_obs)

        metadata = {
            "tool_calling": True,
            "tool_group": "EmbodiedToolGroup",
            "tool_name": tool_name,
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
