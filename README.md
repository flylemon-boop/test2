# AlphaApollo Embodied Robosuite MiniProject

This repository contains the Task A CaP-X S1 reproduction and the Task B
AlphaApollo code-as-action migration artifacts for the Robosuite mini-project.

## 1. Core Changes

- Reproduced the CaP-X S1 baseline on the six required Robosuite tasks:
  `cube_lifting`, `cube_stack`, `spill_wipe`, `nut_assembly`,
  `two_arm_lift`, and `two_arm_handover`.
- Added a reproducible Task A runner at `scripts/run_taskA_s1.sh`.
- Added the Task B AlphaApollo bridge under `code/AlphaApollo/`:
  - `alphaapollo/core/environments/embodied_robosuite/`
  - `alphaapollo/core/tools/embodied_robosuite.py`
  - `alphaapollo/core/environments/env_manager.py`
  - `scripts/run_taskB_robosuite_eval.py`
  - `scripts/run_taskB_robosuite_eval.sh`
  - `scripts/start_taskB_pyroki_server.py`
- Task B keeps the required code-as-action protocol: the model emits one
  `<python_code>...</python_code>` block, and that Python program can call S1
  primitives such as `get_object_pose()`, `sample_grasp_pose()`, `goto_pose()`,
  `open_gripper()`, and `close_gripper()`.
- Added Task A and Task B aggregate results and per-episode JSON trajectories.

## 2. Run Tutorial

### Task A

Task A was run inside the prepared CaP-X environment on the CUDA machine.

```bash
cd /root/autodl-tmp/cap-x
source /root/miniconda3/etc/profile.d/conda.sh
conda activate capx
source .venv/bin/activate
```

Start the OpenAI-compatible proxy. The API key file and base URL file are not
committed.

```bash
nohup python capx/serving/openrouter_server.py \
  --key-file aliyun_key \
  --base-url "$(cat aliyun_base_url)" \
  --port 8110 \
  > outputs/aliyun_proxy.log 2>&1 &
```

Run all Task A S1 tasks:

```bash
bash scripts/run_taskA_s1.sh
```

### Task B

Task B was run from AlphaApollo using the separate `taskb` conda environment.

```bash
cd /root/autodl-tmp/AlphaApollo
TRIALS=30 MAX_TURNS=1 bash scripts/run_taskB_robosuite_eval.sh
```

The Task B script automatically:

- activates `/root/autodl-tmp/taskb_env.sh`;
- starts the PyRoKI IK server on `127.0.0.1:8116`;
- calls the OpenAI-compatible model server at `http://127.0.0.1:8110/chat/completions`;
- evaluates `cube_lift`, `cube_stack`, and `peg_insertion`;
- saves full per-episode JSON trajectories.

Default Task B settings:

- `MODEL=qwen3-235b-a22b-instruct-2507`
- `SERVER=http://127.0.0.1:8110/chat/completions`
- `TRIALS=30`
- `MAX_TURNS=1`
- `PYROKI_PORT=8116`

## 3. Results Summary: Task A vs Task B

Task A used CaP-X S1 single-turn code generation. Task B used AlphaApollo with
the same code-as-action action granularity. Both use 30 trials per task.

| Task | Task A success | Task B success | Absolute delta | Status |
| --- | ---: | ---: | ---: | --- |
| Cube Lift | 30/30 (100.0%) | 30/30 (100.0%) | 0.0 pp | Aligned |
| Cube Stack | 29/30 (96.7%) | 30/30 (100.0%) | +3.3 pp | Aligned |
| Peg / Nut Assembly | 4/30 (13.3%) | 0/30 (0.0%) | -13.3 pp | Aligned within 15 pp |

Task B is aligned with the Task A reference under the project acceptance rule:
the per-task absolute success-rate difference is within 15 percentage points.

Full machine-readable outputs:

- Task A aggregate: `results/taskA_s1_summary.csv`
- Task A Figure 17 comparison: `results/taskA_figure17_comparison.pdf`
- Task B aggregate: `results/taskB/taskB_qwen3-235b-a22b-instruct-2507_30/summary.json`
- Task B episode JSON:
  `results/taskB/taskB_qwen3-235b-a22b-instruct-2507_30/<task>/episode_*.json`

### Task B Details

| Task B task | Trials | Successes | Success rate | Average final reward | Turns |
| --- | ---: | ---: | ---: | ---: | --- |
| Cube Lift | 30 | 30 | 100.0% | 1.000 | 1 |
| Cube Stack | 30 | 30 | 100.0% | 1.000 | 1 |
| Peg Insertion | 30 | 0 | 0.0% | 0.142 | 1 |

Peg Insertion had no sandbox execution errors. The generated code executed
successfully, but the final state did not satisfy the Robosuite
`_check_success()` criterion. This is consistent with Task A also being low on
the corresponding Nut Assembly task (4/30). The remaining gap is within the
project tolerance and is likely caused by the task's sensitivity to the
handle-to-nut rigid transform, end-effector orientation, and insertion depth.

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

The committed Task B run was executed without video recording. The required
episode JSON trajectories and summaries are included. To produce demo videos,
rerun selected successful episodes with video capture enabled and save the
Robosuite frame buffer from the Task B wrapper.

## Repository Layout

```text
code/cap-x/
code/AlphaApollo/
scripts/run_taskA_s1.sh
results/taskA_s1_summary.csv
results/taskA_figure17_comparison.pdf
results/taskA_run_environment.md
results/taskB/taskB_qwen3-235b-a22b-instruct-2507_30/
logs/taskA/
experiments/taskA/taskA_qwen3-235b-a22b-instruct-2507_30/
```

Runtime artifacts are excluded where possible: virtual environments, Git
metadata, cache files, and local API key files are not committed.

Secrets such as API keys, SSH passwords, and proxy key files are intentionally
not committed.
