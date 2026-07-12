# TaskBonus Code

This directory contains the runnable TaskBonus AlphaApollo code for the
Embodied Robosuite mini-project.

## Layout

```text
run_task_bonus.sh
AlphaApollo/
  alphaapollo/
  examples/
    demo/taskbonus_robosuite_api.py
    configs/demo_taskbonus_robosuite_api.yaml
  scripts/
  cap-x/
```

`AlphaApollo/cap-x` is the bundled CaP-X dependency used by this TaskBonus
runner. The branch does not require a sibling `TaskA/cap-x` directory.

## Run

From a fresh clone of the `taskBonus` branch:

```bash
git clone -b taskBonus https://github.com/flylemon-boop/test2.git
cd test2/TaskBonus
MAX_TURNS=25 TRIALS=30 BATCH_SIZE=1 bash run_task_bonus.sh
```

Quick smoke test:

```bash
TASKS=cube_lift TRIALS=1 BATCH_SIZE=1 MAX_TURNS=2 bash run_task_bonus.sh
```

The actual Python entry point is:

```text
AlphaApollo/examples/demo/taskbonus_robosuite_api.py
```

with configuration:

```text
AlphaApollo/examples/configs/demo_taskbonus_robosuite_api.yaml
```

## API

Place `api.csv` at the repository root, at `TaskBonus/api.csv`, or at
`/root/autodl-tmp/api.csv`. Alternatively set:

```bash
export OPENAI_API_KEY=<your key>
export SERVER=<OpenAI-compatible /chat/completions URL>
export MODEL=qwen3-235b-a22b-instruct-2507
```

## Implementation Notes

TaskBonus exposes each S1 primitive as an independent XML tool call:

```xml
<open_gripper>{}</open_gripper>
<sample_grasp_pose>{"object_name":"red cube"}</sample_grasp_pose>
<goto_pose>{"position":[0.1,0.2,0.3],"quaternion_wxyz":[0,0,1,0],"z_approach":0.1}</goto_pose>
```

The current API path follows AlphaApollo's demo style:

```text
examples/demo/taskbonus_robosuite_api.py
  -> LLMClient
  -> make_envs(config)
  -> EmbodiedRobosuiteEnvironmentManager
  -> EmbodiedRobosuiteEnv.step
  -> EmbodiedToolGroup single S1 XML tool
  -> CaP-X API / Robosuite
```

The historical full-run results are documented in the repository root README.
