# Task B Code

This directory contains the runnable Task B AlphaApollo code for the Embodied
Robosuite mini-project.

## Layout

```text
run_taskB.sh
run_taskB_generation.sh
AlphaApollo/
  alphaapollo/
  scripts/
  examples/
  cap-x/
```

`AlphaApollo/cap-x` is the bundled CaP-X dependency used by this Task B runner.
The branch no longer needs a sibling `TaskA/cap-x` directory.

## Run

From a fresh clone of the `taskB` branch:

```bash
git clone -b taskB https://github.com/flylemon-boop/test2.git
cd test2/TaskB
TRIALS=30 MAX_TURNS=4 bash run_taskB.sh
```

For a quick smoke test:

```bash
TASKS=cube_lift TRIALS=1 BATCH_SIZE=1 MAX_TURNS=1 bash run_taskB.sh
```

The script will:

- source `TASKB_ENV` when provided;
- auto-source `/root/autodl-tmp/taskb_env.sh` on the remote machine when it
  exists;
- add `AlphaApollo` and `AlphaApollo/cap-x` to `PYTHONPATH`;
- start or reuse the PyRoKI IK server on `127.0.0.1:8116`;
- call the configured OpenAI-compatible chat completion API;
- write outputs under `results/`.

## API

Place `api.csv` at the repository root, at `TaskB/api.csv`, or at
`/root/autodl-tmp/api.csv`. Alternatively set:

```bash
export OPENAI_API_KEY=<your key>
export SERVER=<OpenAI-compatible /chat/completions URL>
export MODEL=qwen3-235b-a22b-instruct-2507
```

## Implementation Notes

Task B uses AlphaApollo's rollout and tool abstractions while delegating actual
robot code execution to CaP-X:

```text
TrajectoryCollector
  -> EmbodiedRobosuiteEnvironmentManager
  -> EmbodiedRobosuiteEnv.step
  -> EmbodiedRobosuiteToolGroup.python_code
  -> execute_capx_python_code
  -> CaP-X capx_env.step(code)
```

The model still emits exactly one code-as-action block:

```xml
<python_code>
...
</python_code>
```

Inside that block it may call the CaP-X S1 APIs exposed by the task prompt,
such as `get_object_pose`, `sample_grasp_pose`, `goto_pose`, `open_gripper`,
and `close_gripper`.
