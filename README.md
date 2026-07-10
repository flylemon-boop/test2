# AlphaApollo Embodied Robosuite MiniProject

This branch contains the Task B AlphaApollo code-as-action migration artifacts
for the Robosuite mini-project.

## 1. Core Changes

- Added the Task B AlphaApollo bridge under `TaskB/AlphaApollo/` and
  `code/AlphaApollo/`:
  - `alphaapollo/core/environments/embodied_robosuite/`
  - `alphaapollo/core/tools/embodied_robosuite.py`
  - `alphaapollo/core/environments/env_manager.py`
  - `scripts/run_taskB_robosuite_api.py`
  - `scripts/run_alphaapollo_taskB_generation.sh`
  - `scripts/start_taskB_pyroki_server.py`
- Task B keeps the required code-as-action protocol: the model emits one
  `<python_code>...</python_code>` block, and that Python program can call S1
  primitives such as `get_object_pose()`, `sample_grasp_pose()`, `goto_pose()`,
  `open_gripper()`, and `close_gripper()`.
- Added `TaskA/cap-x/` from the `taskA` branch because the Task B runner imports
  the CaP-X Robosuite environment and S1 API implementation at runtime.
- Added Task B aggregate results and per-episode JSON trajectories.

## 2. Run Tutorial

Clone the repository into any directory. The commands below use `$REPO` to mean
the repository root:

```bash
git clone -b taskB https://github.com/flylemon-boop/test2.git
cd test2
export REPO="$(pwd)"
```

Task B was run from AlphaApollo using a `taskb` conda environment. The exact
conda path is machine-specific. Either activate the environment manually before
running the script, or point `TASKB_ENV` to your own setup script:

```bash
# Option A: activate manually
conda activate taskb

# Option B: let the runner source your environment file
export TASKB_ENV="$REPO/taskb_env.sh"
```

An environment setup file should activate Python and export any machine-specific
paths. For example:

```bash
source /path/to/miniconda3/etc/profile.d/conda.sh
conda activate taskb
export MUJOCO_GL=egl
export PYOPENGL_PLATFORM=egl
export PYTHONPATH="$REPO/TaskB/AlphaApollo:$REPO/TaskA/cap-x:${PYTHONPATH:-}"
```

For compatibility with the submitted remote machine, `TaskB/run_taskB.sh` still
auto-sources `/root/autodl-tmp/taskb_env.sh` when that file exists, but this
absolute path is not required on a new machine.

Keep `TaskA/` and `TaskB/` as sibling directories. `TaskB/run_taskB.sh` adds
`../TaskA/cap-x` to `PYTHONPATH` automatically.

Run all Task B tasks:

```bash
cd "$REPO/TaskB"
TRIALS=30 MAX_TURNS=4 bash run_taskB.sh
```

The Task B script automatically:

- sources `TASKB_ENV` if provided;
- starts the PyRoKI IK server on `127.0.0.1:8116`;
- calls an OpenAI-compatible model server, either through the local proxy at
  `http://127.0.0.1:8110/chat/completions` or the configured remote API URL;
- evaluates `cube_lift`, `cube_stack`, and `peg_insertion`;
- saves full per-episode JSON trajectories.

It can read `api.csv` automatically from:

```text
$REPO/api.csv
$REPO/TaskB/api.csv
/root/autodl-tmp/api.csv
```

Secrets are intentionally not committed. You can also configure the API
manually:

```bash
export OPENAI_API_KEY=<your key>
export SERVER=<OpenAI-compatible /chat/completions URL>
export MODEL=qwen3-235b-a22b-instruct-2507
```

Default Task B settings:

- `MODEL=qwen3-235b-a22b-instruct-2507`
- `SERVER=<OpenAI-compatible chat completions URL>`
- `TRIALS=30`
- `MAX_TURNS=4`
- `PYROKI_PORT=8116`

## 3. Results Summary: Task A vs Task B

Task A used CaP-X S1 single-turn code generation. Task B used AlphaApollo with
the same code-as-action action granularity. Both use 30 trials per task.

| Task | Task A success | Task B success | Absolute delta | Status |
| --- | ---: | ---: | ---: | --- |
| Cube Lift | 30/30 (100.0%) | 30/30 (100.0%) | 0.0 pp | Aligned |
| Cube Stack | 29/30 (96.7%) | 30/30 (100.0%) | +3.3 pp | Aligned |
| Peg / Nut Assembly | 4/30 (13.3%) | 5/30 (16.7%) | +3.3 pp | Aligned |

Task B is aligned with the Task A reference under the project acceptance rule:
the per-task absolute success-rate difference is within 15 percentage points.

Full machine-readable Task B outputs:

- Task B aggregate: `results/taskB/taskB_qwen3-235b-a22b-instruct-2507_30/summary.json`
- Task B episode JSON:
  `results/taskB/taskB_qwen3-235b-a22b-instruct-2507_30/<task>/episode_*.json`
- Task B demo videos:
  `results/taskB/videos/cube_lift_seed0/episode_000_success_1.mp4` and
  `results/taskB/videos/cube_stack_seed0/episode_000_success_1.mp4`

### Task B Details

| Task B task | Trials | Successes | Success rate | Average final reward | Turns |
| --- | ---: | ---: | ---: | ---: | --- |
| Cube Lift | 30 | 30 | 100.0% | 1.000 | 1 |
| Cube Stack | 30 | 30 | 100.0% | 1.000 | 1 |
| Peg Insertion | 30 | 5 | 16.7% | 0.246 | 4 |

Peg Insertion remained the hardest Task B task. The new run improved it to
5/30 successes, which is within 3.3 percentage points of the corresponding
Task A Nut Assembly result (4/30). The remaining failures are likely caused by
the task's sensitivity to the handle-to-nut rigid transform, end-effector
orientation, and insertion depth.

## 4. Issues and Fixes

### EGL initialization

Initial Robosuite import failed with:

```text
AttributeError: 'NoneType' object has no attribute 'eglQueryString'
```

Fix:

```bash
apt-get update
apt-get install -y libegl1 libgl1
export MUJOCO_GL=egl
export PYOPENGL_PLATFORM=egl
```

### MuJoCo API compatibility

The bundled Robosuite controller called `mujoco.mj_fullM` with the older
argument order. Current MuJoCo expects:

```python
mujoco.mj_fullM(model, data, dst)
```

The CaP-X Robosuite snapshot was patched at:

```text
capx/third_party/robosuite/robosuite/controllers/parts/controller.py
```

to use:

```python
mujoco.mj_fullM(self.sim.model._model, self.sim.data._data, mass_matrix)
```

### CLI boolean value

`--record-video false` is invalid for the CaP-X launcher. The accepted value is:

```bash
--record-video False
```

### AlphaApollo Task B environment

The original AlphaApollo `python_code` tool launches a subprocess and is suited
for stateless math code. Task B needs one persistent Robosuite episode, so the
Task B bridge clones the code-as-action behavior but executes against the
in-process CaP-X `CodeExecutionEnvBase`.

### PyRoKI dependency

`goto_pose()` calls the PyRoKI IK server. The Task B runner starts it
automatically. The `taskb` conda environment needed:

```bash
pip install jax_dataclasses
pip install 'pyroki @ git+https://github.com/chungmin99/pyroki.git@95afccc22658c461ab1042a048ae4e9c24bc2a47'
```

### Video artifacts

Two successful Task B demo videos from different tasks are included under
`results/taskB/videos/`: one Cube Lift episode and one Cube Stack episode.
The Task B runner now supports `--record-video`, which exports the Robosuite
frame buffer to an episode mp4 and records the path in the episode JSON.

To generate a new video on another machine, run a small seeded evaluation with
recording enabled:

```bash
cd "$REPO/TaskB"
OUT="$REPO/results/taskB/videos/cube_lift_seed0" \
TASKS=cube_lift \
TRIALS=1 \
SEED_START=0 \
MAX_TURNS=4 \
RECORD_VIDEO=1 \
bash run_taskB.sh
```

## Repository Layout

```text
TaskA/
TaskA/cap-x/
TaskB/
TaskB/AlphaApollo/
code/cap-x/
code/AlphaApollo/
results/taskB/taskB_qwen3-235b-a22b-instruct-2507_30/
results/taskB/videos/
results/taskB_summary.csv
```

`TaskB/` contains the directly readable and runnable AlphaApollo Task B code
copied from the remote CUDA machine. `code/AlphaApollo/` is the submitted source
snapshot used for the Task B run.

Runtime artifacts are excluded where possible: virtual environments, Git
metadata, cache files, and local API key files are not committed.

Secrets such as API keys, SSH passwords, and proxy key files are intentionally
not committed.
