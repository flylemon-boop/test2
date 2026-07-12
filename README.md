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

## Architecture and Data Flow

Task B keeps the code-as-action interface:

```text
model -> <python_code>...</python_code> -> AlphaApollo tool -> CaP-X env.step(code)
```

The execution path follows AlphaApollo's demo-style API runner, with CaP-X
used as the Robosuite control backend:

```text
Shell env / api.csv / CLI vars
        |
        v
+------------------------------+
| TaskB/run_taskB.sh           |
| - load API key + base URL    |
| - set model / trials / tasks |
| - start PyRoKI if needed     |
+---------------+--------------+
                |
                | command-line args + environment
                v
+--------------------------------------------------------------+
| AlphaApollo demo runner                                      |
| TaskB/AlphaApollo/examples/demo/taskB_robosuite_api.py       |
|                                                              |
|  config YAML + task list + seeds                             |
|          |                                                   |
|          v                                                   |
|  +----------------------+    prompt/messages     +---------+ |
|  | make_envs/reset      | ---------------------> | LLM API | |
|  | Robosuite task envs  |                        | client  | |
|  +----------+-----------+ <--------------------- +---------+ |
|             |              <python_code>...</python_code>    |
|             v                                                |
|  +----------------------+    executable code                 |
|  | EnvManager.step      | --------------------------------+  |
|  | batch episode loop   |                                 |  |
|  +----------+-----------+                                 |  |
+-------------|---------------------------------------------|--+
              |                                             |
              v                                             v
+-----------------------------+        +-----------------------------+
| EmbodiedRobosuiteEnv.step   |        | EmbodiedRobosuiteToolGroup  |
| - parse model action        | -----> | python_code tool            |
| - call selected tool        | code   | execute_capx_python_code    |
+--------------+--------------+        +--------------+--------------+
               |                                      |
               | Python code calls S1 primitives      |
               v                                      v
+--------------------------------------------------------------+
| CaP-X + Robosuite backend                                    |
| TaskB/AlphaApollo/third_party/cap-x                          |
|                                                              |
| get_object_pose / sample_grasp_pose / goto_pose /            |
| open_gripper / close_gripper / task reward + success check   |
+------------------------------+-------------------------------+
                               |
                               | observation + reward + success
                               v
+--------------------------------------------------------------+
| Result store                                                 |
| - per-episode JSON logs                                      |
| - summary.json / summary.csv                                 |
| - optional videos                                            |
+--------------------------------------------------------------+
```

Important data flows:

```text
api.csv or environment variables
  -> OPENAI_API_KEY / SERVER / MODEL
  -> LLMClient chat-completions request

demo_taskB_robosuite_api.yaml + TASKS/TRIALS/MAX_TURNS/SEED_START
  -> runner config
  -> make_envs()
  -> Robosuite episodes

environment prompt + current observation
  -> LLM messages
  -> model output containing one <python_code> block

<python_code> block
  -> EmbodiedRobosuiteToolGroup.python_code
  -> execute_capx_python_code
  -> CaP-X S1 primitive calls
  -> Robosuite state transition

Robosuite observation/reward/success
  -> next model turn if unfinished
  -> episode JSON
  -> summary.csv / summary.json
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

TaskA vs TaskB improved turn-25 comparison:

```text
results/taskB/taskA_vs_taskB_improved_turn25_comparison.csv
```

| Task group | TaskA task | TaskA success | TaskA avg reward | TaskB task | TaskB success | Delta |
| --- | --- | ---: | ---: | --- | ---: | ---: |
| Cube lift | cube_lifting | 30/30 = 100.0% | 1.000 | cube_lift | 30/30 = 100.0% | +0.0 pp |
| Cube stack | cube_stack | 29/30 = 96.7% | 0.967 | cube_stack | 30/30 = 100.0% | +3.3 pp |
| Peg / nut insertion | nut_assembly | 4/30 = 13.3% | 0.254 | peg_insertion | 3/30 = 10.0% | -3.3 pp |

`peg_insertion` is compared with TaskA `nut_assembly` because both are
insertion-style Robosuite manipulation tasks.
