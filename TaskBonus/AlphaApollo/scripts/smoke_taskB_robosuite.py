from omegaconf import OmegaConf

from alphaapollo.core.environments.embodied_robosuite.env import EmbodiedRobosuiteEnv


def main():
    cfg = OmegaConf.create(
        {
            "task_name": "cube_lift",
            "max_steps": 2,
            "log_requests": False,
            "record_video": False,
        }
    )
    env = EmbodiedRobosuiteEnv(cfg)
    prompt, info = env.init([])
    print("TASK", info["task_name"])
    print("PROMPT_CHARS", len(prompt[0]["content"]))
    out = env.step(
        "<python_code>print('obs keys', sorted(list(obs.keys()))[:8])</python_code>",
        "<python_code>print('obs keys', sorted(list(obs.keys()))[:8])</python_code>",
    )
    print("DONE", out["done"])
    print("REWARD", out["reward"])
    print("OBS_CHARS", len(out["observations"][0]["content"]) if out["observations"] else 0)
    env.close()


if __name__ == "__main__":
    main()
