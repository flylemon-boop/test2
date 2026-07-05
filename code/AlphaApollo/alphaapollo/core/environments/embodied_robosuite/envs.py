import asyncio
import concurrent.futures
from copy import deepcopy
from typing import Any, Dict, List

import gymnasium as gym
from omegaconf import DictConfig


class EmbodiedRobosuiteMultiProcessEnv(gym.Env):
    def __init__(
        self,
        seed: int = 0,
        env_num: int = 1,
        group_n: int = 1,
        is_train: bool = True,
        env_config: DictConfig | None = None,
    ) -> None:
        super().__init__()
        from alphaapollo.core.environments.embodied_robosuite.env import (
            EmbodiedRobosuiteEnv,
        )

        self.env_num = env_num
        self.group_n = group_n
        self.batch_size = env_num * group_n
        self.is_train = is_train
        self.max_steps = int(getattr(env_config, "max_steps", 8))
        embodied_cfg = getattr(env_config, "embodied_robosuite", env_config)

        self.envs = []
        for _idx in range(self.batch_size):
            self.envs.append(EmbodiedRobosuiteEnv(deepcopy(embodied_cfg)))

        max_workers = min(self.batch_size, 64)
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._closed = False

    def _sync_reset(self, env, kwargs: Dict[str, Any]):
        env.reset(kwargs)
        prompt, info = env.init([])
        obs = prompt[0]["content"]
        return obs, info

    def _sync_step(self, env, action: str, text_action: str):
        out = env.step(action, text_action)
        obs_items = out["observations"]
        obs = "" if len(obs_items) == 0 else obs_items[0]["content"].strip()
        reward = out["reward"]
        done = out["done"]
        info = {"tool_infos": out.get("metadata", {})}
        info["postprocessed_action"] = out.get("postprocessed_action")
        info["won"] = bool(done and reward > 0.0)
        return obs, reward, done, info

    def reset(self, kwargs: List[Dict]):
        kwargs = kwargs or [{} for _ in range(self.batch_size)]
        if len(kwargs) > self.batch_size:
            raise ValueError(
                f"Got {len(kwargs)} kwarg dicts, but total envs is {self.batch_size}"
            )
        padded = list(kwargs) + [{} for _ in range(self.batch_size - len(kwargs))]
        valid_mask = [True] * len(kwargs) + [False] * (self.batch_size - len(kwargs))
        tasks = [
            self._loop.run_in_executor(self._executor, self._sync_reset, env, kw)
            for env, kw in zip(self.envs, padded)
        ]
        results = self._loop.run_until_complete(asyncio.gather(*tasks))
        obs_list, info_list = map(list, zip(*results))
        obs_list = [o for o, keep in zip(obs_list, valid_mask) if keep]
        info_list = [i for i, keep in zip(info_list, valid_mask) if keep]
        return obs_list, info_list

    def step(self, actions: List[str], text_actions: List[str]):
        if len(actions) > self.batch_size:
            raise ValueError(
                f"Got {len(actions)} actions, but total envs is {self.batch_size}"
            )
        padded_actions = list(actions) + [""] * (self.batch_size - len(actions))
        padded_text_actions = list(text_actions) + [""] * (
            self.batch_size - len(text_actions)
        )
        valid_mask = [True] * len(actions) + [False] * (self.batch_size - len(actions))
        tasks = [
            self._loop.run_in_executor(
                self._executor, self._sync_step, env, action, text_action
            )
            for env, action, text_action in zip(
                self.envs, padded_actions, padded_text_actions
            )
        ]
        results = self._loop.run_until_complete(asyncio.gather(*tasks))
        obs_list, reward_list, done_list, info_list = map(list, zip(*results))
        obs_list = [o for o, keep in zip(obs_list, valid_mask) if keep]
        reward_list = [r for r, keep in zip(reward_list, valid_mask) if keep]
        done_list = [d for d, keep in zip(done_list, valid_mask) if keep]
        info_list = [i for i, keep in zip(info_list, valid_mask) if keep]
        return obs_list, reward_list, done_list, info_list

    def close(self):
        if self._closed:
            return
        for env in self.envs:
            env.close()
        self._executor.shutdown(wait=True)
        if self._loop is not None and not self._loop.is_closed():
            self._loop.close()
        self._closed = True


def build_embodied_robosuite_envs(
    seed: int = 0,
    env_num: int = 1,
    group_n: int = 1,
    is_train: bool = True,
    env_config=None,
):
    return EmbodiedRobosuiteMultiProcessEnv(
        seed=seed,
        env_num=env_num,
        group_n=group_n,
        is_train=is_train,
        env_config=env_config,
    )
