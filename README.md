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
- API rollout runner:
  - `TaskBonus/AlphaApollo/scripts/run_taskbonus_robosuite_api.py`
- One-command runner:
  - `TaskBonus/run_task_bonus.sh`
- Full TaskBonus evaluation results:
  - `results/taskBonus/taskbonus_autofix_turn25/`
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
export PYTHONPATH="$REPO/TaskBonus/AlphaApollo:$REPO/TaskA/cap-x:${PYTHONPATH:-}"
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

The runner also needs the CaP-X code. It searches these locations and adds the
first valid one to `PYTHONPATH`:

```text
../TaskA/cap-x
../cap-x
../../cap-x
/root/autodl-tmp/cap-x
```

In this repository, the expected relative layout is:

```text
$REPO/TaskA/cap-x
$REPO/TaskBonus
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
results/taskBonus/taskbonus_autofix_turn25/summary.csv
```

| Task | Trials | Successes | Success rate | Average turns |
| --- | ---: | ---: | ---: | ---: |
| cube_lift | 30 | 26 | 86.67% | 9.77 |
| cube_stack | 30 | 0 | 0.00% | 24.60 |
| peg_insertion | 30 | 0 | 0.00% | 24.20 |

Successful tool-call demo video:

```text
results/taskBonus/taskbonus_video_cube_lift_seed1/cube_lift/videos/episode_000_success_1.mp4
```

Video episode summary:

```text
task,trials,successes,success_rate,avg_turns
cube_lift,1,1,1.0,16.0
```

## 6. Notes

- `TaskBonus/run_task_bonus.sh` starts PyRoKI automatically if the server is
  not already running.
- The tool-call runner normalizes minor XML formatting errors. For example,
  `<open_gripper>{}` is completed to `<open_gripper>{}</open_gripper>` when the
  body is valid JSON.
- Invalid JSON is not repaired and is left for the environment to reject.
- Runtime artifacts such as virtual environments, Git metadata, cache files,
  API keys, SSH passwords, and proxy key files are intentionally not committed.

## 7. Repository Layout

```text
TaskA/
TaskBonus/
TaskBonus/AlphaApollo/
TaskBonus/run_task_bonus.sh
code/cap-x/
results/taskBonus/taskbonus_autofix_turn25/
results/taskBonus/taskbonus_video_cube_lift_seed1/
```
