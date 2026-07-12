# AlphaApollo Embodied Robosuite - Task B

This `taskB` branch contains the runnable Task B AlphaApollo integration for
the Embodied Robosuite mini-project.

## Contents

```text
TaskB/
  run_taskB.sh
  run_taskB_generation.sh
  AlphaApollo/
    alphaapollo/
    scripts/
    examples/
    cap-x/
```

`TaskA/` is intentionally not included on this branch. The CaP-X code needed by
Task B is bundled under:

```text
TaskB/AlphaApollo/cap-x
```

The runner adds this bundled CaP-X path to `PYTHONPATH` before falling back to
any external CaP-X checkout.

## Main Entry Point

Run Task B from the repository root with:

```bash
cd TaskB
TRIALS=30 MAX_TURNS=4 bash run_taskB.sh
```

For a quick smoke test:

```bash
cd TaskB
TASKS=cube_lift TRIALS=1 BATCH_SIZE=1 MAX_TURNS=1 bash run_taskB.sh
```

## Environment

The script can source a machine-local setup file before running:

```bash
export TASKB_ENV=/path/to/taskb_env.sh
```

On the submitted remote machine it also auto-sources:

```text
/root/autodl-tmp/taskb_env.sh
```

The runner sets the Robosuite rendering defaults:

```bash
MUJOCO_GL=egl
PYOPENGL_PLATFORM=egl
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

## Task B Implementation

Task B keeps the code-as-action interface:

```text
model -> <python_code>...</python_code> -> AlphaApollo tool -> CaP-X env.step(code)
```

Important files:

```text
TaskB/AlphaApollo/alphaapollo/core/environments/embodied_robosuite/env.py
TaskB/AlphaApollo/alphaapollo/core/environments/embodied_robosuite/envs.py
TaskB/AlphaApollo/alphaapollo/core/environments/env_manager.py
TaskB/AlphaApollo/alphaapollo/core/tools/embodied_robosuite.py
TaskB/AlphaApollo/alphaapollo/core/tools/capx_python_code.py
TaskB/AlphaApollo/scripts/run_taskB_robosuite_api.py
```

`capx_python_code.py` mirrors the original AlphaApollo pattern where the
ToolGroup method delegates execution to a separate helper:

```text
EmbodiedRobosuiteToolGroup.python_code
  -> execute_capx_python_code
  -> capx_env.step(code)
```

## Supported Tasks

The default runner evaluates:

```text
cube_lift
cube_stack
peg_insertion
```

Results are written under:

```text
TaskB/results/
```

Runtime results, API keys, local caches, and virtual environments are excluded
from the repository.
