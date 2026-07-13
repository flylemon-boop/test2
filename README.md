# AlphaApollo Embodied Robosuite MiniProject - TaskBonus

This branch contains the TaskBonus tool-call-as-action implementation for the
Robosuite mini-project. It keeps the AlphaApollo multi-turn rollout loop, but
changes the model action format from Task B's single `python_code` tool to
one XML tool call per turn.

## 1. What Is Included

- TaskBonus source code under `TaskBonus/`.
- AlphaApollo Robosuite environment bridge:
  - `TaskBonus/AlphaApollo/alphaapollo/core/environments/embodied_robosuite/`
  - `TaskBonus/AlphaApollo/alphaapollo/core/environments/env_manager.py`
- Tool-call wrapper for CaP-X S1 primitives:
  - `TaskBonus/AlphaApollo/alphaapollo/core/tools/embodied_robosuite.py`
- Demo-style API runner:
  - `TaskBonus/AlphaApollo/examples/demo/taskbonus_robosuite_api.py`
  - `TaskBonus/AlphaApollo/examples/configs/demo_taskbonus_robosuite_api.yaml`
- One-command runner:
  - `TaskBonus/run_task_bonus.sh`
- Bundled CaP-X backend:
  - `TaskBonus/AlphaApollo/third_party/cap-x`
- Full TaskBonus evaluation results:
  - `results/taskBonus/taskBonus_improved_turn25/`
- One successful tool-call demo video:
  - `results/taskBonus/taskbonus_video_cube_lift_seed1/cube_lift/videos/episode_000_success_1.mp4`

TaskBonus exposes each S1 primitive as an independent tool. The model must
output exactly one XML call per turn, for example:

```xml
<open_gripper>{}</open_gripper>
<sample_grasp_pose>{"object_name":"red cube"}</sample_grasp_pose>
<goto_pose>{"position":[0.1,0.2,0.3],"quaternion_wxyz":[0,0,1,0],"z_approach":0.1}</goto_pose>
```

The primitive set and parameter semantics match the Task B S1 API. The
difference is action granularity: Task B uses one `python_code` tool that may
call multiple primitives in one program; TaskBonus uses one primitive tool call
per model turn.

## 2. Environment Setup

Clone the repository into any directory. The commands below use `$REPO` to mean
the repository root:

```bash
git clone -b taskBonus https://github.com/flylemon-boop/test2.git
cd test2
export REPO="$(pwd)"
```

The submitted remote run used a shared environment file at
`/root/autodl-tmp/taskb_env.sh`, but that absolute path is not required. On a
new machine, either activate your conda environment before running the script,
or point `TASKBONUS_ENV` to your own setup script:

```bash
# Option A: activate manually
conda activate taskb

# Option B: let the runner source your environment file
export TASKBONUS_ENV="$REPO/taskbonus_env.sh"
```

An environment setup file should activate Python and export any machine-specific
paths. For example:

```bash
source /path/to/miniconda3/etc/profile.d/conda.sh
conda activate taskb
export MUJOCO_GL=egl
export PYOPENGL_PLATFORM=egl
export PYTHONPATH="$REPO/TaskBonus/AlphaApollo:$REPO/TaskBonus/AlphaApollo/third_party/cap-x:${PYTHONPATH:-}"
```

`TaskBonus/run_task_bonus.sh` also works without `TASKBONUS_ENV` if the active
shell already has the right Python environment. For compatibility with the
original remote machine, it still auto-sources `/root/autodl-tmp/taskb_env.sh`
when that file exists.

Important runtime requirements:

```bash
export MUJOCO_GL=egl
export PYOPENGL_PLATFORM=egl
```

System packages needed for EGL rendering:

```bash
apt-get update
apt-get install -y libegl1 libgl1
```

PyRoKI is required because `goto_pose()` uses the IK server. The runner starts
the PyRoKI server automatically on `127.0.0.1:8116`. The environment should
contain:

```bash
pip install jax_dataclasses
pip install 'pyroki @ git+https://github.com/chungmin99/pyroki.git@95afccc22658c461ab1042a048ae4e9c24bc2a47'
```

The runner also needs the CaP-X code. This branch bundles the required CaP-X
backend under:

```text
$REPO/TaskBonus/AlphaApollo/third_party/cap-x
```

`run_task_bonus.sh` adds the bundled path to `PYTHONPATH` first, then falls
back to these locations for compatibility:

```text
TaskBonus/AlphaApollo/third_party/cap-x
../TaskA/cap-x
../cap-x
../../cap-x
/root/autodl-tmp/cap-x
```

## 3. API Configuration

The runner uses an OpenAI-compatible chat completions endpoint. It can read the
API key and server URL from `api.csv` automatically.

Search order:

```text
$REPO/api.csv
$REPO/TaskBonus/api.csv
/root/autodl-tmp/api.csv
```

Expected CSV keys:

```text
apiKey
openAiCompatible
```

Secrets are intentionally not committed. Put `api.csv` at the repository root
or under `TaskBonus/` before running:

```text
$REPO/api.csv
```

You can also configure the model manually:

```bash
export OPENAI_API_KEY=<your key>
export SERVER=<OpenAI-compatible /chat/completions URL>
export MODEL=qwen3-235b-a22b-instruct-2507
```

## 4. Run Commands

Run the full TaskBonus evaluation:

```bash
cd "$REPO/TaskBonus"
MAX_TURNS=25 TRIALS=30 BATCH_SIZE=1 bash run_task_bonus.sh
```

`run_task_bonus.sh` now calls the AlphaApollo demo-style API runner:

```text
TaskBonus/AlphaApollo/examples/demo/taskbonus_robosuite_api.py
```

with config:

```text
TaskBonus/AlphaApollo/examples/configs/demo_taskbonus_robosuite_api.yaml
```

Run only one task:

```bash
cd "$REPO/TaskBonus"
TASKS=cube_lift MAX_TURNS=25 TRIALS=30 BATCH_SIZE=1 bash run_task_bonus.sh
```

Run one successful demo episode with video recording:

```bash
cd "$REPO/TaskBonus"
OUT="$REPO/results/taskBonus/taskbonus_video_cube_lift_seed1" \
TASKS=cube_lift \
TRIALS=1 \
SEED_START=1 \
MAX_TURNS=25 \
BATCH_SIZE=1 \
RECORD_VIDEO=1 \
bash run_task_bonus.sh
```

Default settings in `run_task_bonus.sh`:

```text
MODEL=qwen3-235b-a22b-instruct-2507
TASKS="cube_lift cube_stack peg_insertion"
TRIALS=30
BATCH_SIZE=1
MAX_TURNS=12
PYROKI_PORT=8116
RECORD_VIDEO=0
```

For the submitted run, `MAX_TURNS` was set to 25.

## 5. Results

Full TaskBonus run:

```text
results/taskBonus/taskBonus_improved_turn25/summary.csv
```

| Task | Trials | Successes | Success rate | Average turns |
| --- | ---: | ---: | ---: | ---: |
| cube_lift | 30 | 30 | 100.00% | 8.50 |
| cube_stack | 30 | 11 | 36.67% | 21.87 |
| peg_insertion | 30 | 0 | 0.00% | 24.77 |

TaskB vs TaskBonus improved turn-25 comparison:

```text
results/taskBonus/taskB_vs_taskBonus_improved_turn25_comparison.csv
```

| Task | TaskB success | TaskBonus success | TaskBonus avg turns | Delta |
| --- | ---: | ---: | ---: | ---: |
| cube_lift | 30/30 = 100.00% | 30/30 = 100.00% | 8.50 | +0.0 pp |
| cube_stack | 30/30 = 100.00% | 11/30 = 36.67% | 21.87 | -63.3 pp |
| peg_insertion | 3/30 = 10.00% | 0/30 = 0.00% | 24.77 | -10.0 pp |

Both runs use the same three Robosuite tasks, the same `TRIALS=30`, and
`MAX_TURNS=25`. TaskB is the code-as-action baseline; TaskBonus is the
tool-call-as-action variant.

Successful tool-call demo video:

```text
results/taskBonus/taskbonus_video_cube_lift_seed1/cube_lift/videos/episode_000_success_1.mp4
```

Video episode summary:

```text
task,trials,successes,success_rate,avg_turns
cube_lift,1,1,1.0,16.0
```

## 6. Architecture and Data Flow

- `TaskBonus/run_task_bonus.sh` starts PyRoKI automatically if the server is
  not already running.

TaskBonus keeps AlphaApollo's multi-turn rollout structure, but changes the
model action from one `python_code` block to exactly one XML tool call per turn:

```text
model -> <tool_name>{json_args}</tool_name> -> EmbodiedToolGroup -> CaP-X S1 API
```

The execution path and data flow are:

```text
Shell env / api.csv / CLI vars
        |
        v
+---------------------------------+
| TaskBonus/run_task_bonus.sh     |
| - load API key + base URL       |
| - set model / trials / tasks    |
| - start PyRoKI if needed        |
+----------------+----------------+
                 |
                 | command-line args + environment
                 v
+----------------------------------------------------------------+
| AlphaApollo demo runner                                        |
| TaskBonus/AlphaApollo/examples/demo/taskbonus_robosuite_api.py |
|                                                                |
|  config YAML + task list + seeds                               |
|          |                                                     |
|          v                                                     |
|  +----------------------+    prompt/messages       +---------+ |
|  | make_envs/reset      | -----------------------> | LLM API | |
|  | Robosuite task envs  |                          | client  | |
|  +----------+-----------+ <----------------------- +---------+ |
|             |              one XML tool call per turn          |
|             v                                                  |
|  +----------------------+    tool call XML + JSON args         |
|  | EnvManager.step      | ----------------------------------+  |
|  | batch episode loop   |                                   |  |
|  +----------+-----------+                                   |  |
+-------------|-----------------------------------------------|--+
              |                                               |
              v                                               v
+-----------------------------+        +-----------------------------+
| EmbodiedRobosuiteEnv.step   |        | EmbodiedToolGroup           |
| - parse XML tool token      | -----> | registered S1 primitive     |
| - validate JSON arguments   | call   | one tool per model turn     |
+--------------+--------------+        +--------------+--------------+
               |                                      |
               | selected primitive + parameters      |
               v                                      v
+--------------------------------------------------------------+
| CaP-X + Robosuite backend                                    |
| TaskBonus/AlphaApollo/third_party/cap-x                      |
|                                                              |
| <get_object_pose> / <sample_grasp_pose> / <goto_pose> /      |
| <open_gripper> / <close_gripper> / reward + success check    |
+------------------------------+-------------------------------+
                               |
                               | <tool_response> + observation
                               v
+--------------------------------------------------------------+
| Next-turn prompt / result store                              |
| - tool response is appended to conversation history           |
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

demo_taskbonus_robosuite_api.yaml + TASKS/TRIALS/MAX_TURNS/SEED_START
  -> runner config
  -> make_envs()
  -> Robosuite episodes

task prompt + current observation + previous <tool_response> messages
  -> LLM messages
  -> model output containing one XML S1 tool call

XML tool call, for example <goto_pose>{...}</goto_pose>
  -> XML parser / minor close-tag normalization
  -> JSON argument validation
  -> EmbodiedToolGroup registered method
  -> CaP-X S1 primitive
  -> Robosuite state transition

primitive return value / observation / reward / success
  -> <tool_response>
  -> next model turn if unfinished
  -> episode JSON
  -> summary.csv / summary.json
```

- The tool-call runner normalizes minor XML formatting errors. For example,
  `<open_gripper>{}` is completed to `<open_gripper>{}</open_gripper>` when the
  body is valid JSON.
- Invalid JSON is not repaired and is left for the environment to reject.
- Runtime artifacts such as virtual environments, Git metadata, cache files,
  API keys, SSH passwords, and proxy key files are intentionally not committed.

## 7. Repository Layout

```text
TaskBonus/
TaskBonus/AlphaApollo/
TaskBonus/AlphaApollo/third_party/cap-x/
TaskBonus/AlphaApollo/examples/demo/taskbonus_robosuite_api.py
TaskBonus/AlphaApollo/examples/configs/demo_taskbonus_robosuite_api.yaml
TaskBonus/run_task_bonus.sh
results/taskBonus/taskBonus_improved_turn25/
results/taskBonus/taskbonus_video_cube_lift_seed1/
```
