# AlphaApollo Embodied Robosuite - Task B

This `taskB` branch contains the runnable Task B AlphaApollo integration for
the Embodied Robosuite mini-project.

## Contents

```text
TaskB/
  run_taskB.sh
  AlphaApollo/
    alphaapollo/
    examples/
      demo/taskB_robosuite_api.py
      configs/demo_taskB_robosuite_api.yaml
    scripts/
    third_party/
      cap-x/
```

`TaskA/` is intentionally not included on this branch. The CaP-X code needed by
Task B is bundled under:

```text
TaskB/AlphaApollo/third_party/cap-x
```

The runner adds this bundled CaP-X path to `PYTHONPATH` before falling back to
any external CaP-X checkout.

## Run

```bash
cd TaskB
TRIALS=30 MAX_TURNS=25 bash run_taskB.sh
```

Quick smoke test:

```bash
cd TaskB
TASKS=cube_lift TRIALS=1 BATCH_SIZE=1 MAX_TURNS=25 bash run_taskB.sh
```

`run_taskB.sh` now calls the AlphaApollo demo-style API runner:

```text
TaskB/AlphaApollo/examples/demo/taskB_robosuite_api.py
```

with config:

```text
TaskB/AlphaApollo/examples/configs/demo_taskB_robosuite_api.yaml
```

## API Configuration

The runner reads API settings from one of:

```text
api.csv
TaskB/api.csv
/root/autodl-tmp/api.csv
```

or from environment variables:

```bash
export OPENAI_API_KEY=<your key>
export SERVER=<OpenAI-compatible /chat/completions URL>
export MODEL=qwen3-235b-a22b-instruct-2507
```

Secrets are not committed.

## Implementation

Task B keeps the code-as-action interface:

```text
model -> <python_code>...</python_code> -> AlphaApollo tool -> CaP-X env.step(code)
```

The current API path follows AlphaApollo's original demo style:

```text
run_taskB.sh
  -> examples/demo/taskB_robosuite_api.py
  -> LLMClient calls an OpenAI-compatible API
  -> make_envs(config)
  -> EmbodiedRobosuiteEnvironmentManager.reset/step
  -> EmbodiedRobosuiteEnv.step
  -> EmbodiedRobosuiteToolGroup.python_code
  -> execute_capx_python_code
  -> CaP-X capx_env.step(code)
```

Results are written under:

```text
TaskB/results/
```

The improved turn-25 summary committed with this branch is available at:

```text
results/taskB/taskB_improved_turn25/summary.csv
```

| Task | Trials | Successes | Success rate |
| --- | ---: | ---: | ---: |
| cube_lift | 30 | 30 | 100.00% |
| cube_stack | 30 | 30 | 100.00% |
| peg_insertion | 30 | 3 | 10.00% |
