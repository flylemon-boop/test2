# Task B Code

This directory contains the runnable Task B AlphaApollo code for the Embodied
Robosuite mini-project.

## Layout

```text
run_taskB.sh
AlphaApollo/
  alphaapollo/
  examples/
    demo/taskB_robosuite_api.py
    configs/demo_taskB_robosuite_api.yaml
  scripts/
  cap-x/
```

`AlphaApollo/cap-x` is the bundled CaP-X dependency used by this Task B runner.
The branch does not require a sibling `TaskA/cap-x` directory.

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

The actual Python entry point is:

```text
AlphaApollo/examples/demo/taskB_robosuite_api.py
```

with configuration:

```text
AlphaApollo/examples/configs/demo_taskB_robosuite_api.yaml
```

## API

Place `api.csv` at the repository root, at `TaskB/api.csv`, or at
`/root/autodl-tmp/api.csv`. Alternatively set:

```bash
export OPENAI_API_KEY=<your key>
export SERVER=<OpenAI-compatible /chat/completions URL>
export MODEL=qwen3-235b-a22b-instruct-2507
```

## Implementation Notes

Task B uses AlphaApollo's environment manager and tool abstractions while
delegating actual robot code execution to CaP-X:

```text
examples/demo/taskB_robosuite_api.py
  -> LLMClient
  -> make_envs(config)
  -> EmbodiedRobosuiteEnvironmentManager
  -> EmbodiedRobosuiteEnv.step
  -> EmbodiedRobosuiteToolGroup.python_code
  -> execute_capx_python_code
  -> CaP-X capx_env.step(code)
```

The model emits exactly one code-as-action block:

```xml
<python_code>
...
</python_code>
```
