# AlphaApollo Embodied Robosuite MiniProject

This repository contains the Task A CaP-X S1 reproduction artifacts and the
submission scaffolding for the AlphaApollo / Robosuite mini-project.

## 1. Core Changes

- Reproduced the CaP-X S1 baseline on the six required Robosuite tasks:
  `cube_lifting`, `cube_stack`, `spill_wipe`, `nut_assembly`,
  `two_arm_lift`, and `two_arm_handover`.
- Added a reproducible Task A runner at `TaskA/run_taskA_s1.sh`.
- Added Task A aggregate results in `results/taskA_s1_summary.csv`.
- Added complete Task A episode records under `experiments/taskA/`.
  Each trial directory contains generated code, raw model response,
  prompt snapshot, `all_responses.json`, and `summary.txt`.
- Added raw command logs under `logs/taskA/`.

Task B has not been completed in this repository yet. The A vs B table below
keeps the Task B columns explicit as pending instead of inventing results.

## 2. Run Tutorial

Clone the repository into any directory. The commands below use `$REPO` to mean
the repository root:

```bash
git clone -b taskA https://github.com/flylemon-boop/test2.git
cd test2
export REPO="$(pwd)"
```

Activate the CaP-X environment. The exact conda path is machine-specific; the
following is only an example:

```bash
source /path/to/miniconda3/etc/profile.d/conda.sh
conda activate capx
cd "$REPO/TaskA/cap-x"
source .venv/bin/activate
```

Start the OpenAI-compatible proxy if you use a local proxy. The API key file
and base URL file are not committed to this repository. Put them wherever is
appropriate for the current machine and pass their paths explicitly:

```bash
nohup python capx/serving/openrouter_server.py \
  --key-file /path/to/aliyun_key \
  --base-url "$(cat /path/to/aliyun_base_url)" \
  --port 8110 \
  > outputs/aliyun_proxy.log 2>&1 &
```

If you already have an OpenAI-compatible chat completions endpoint, skip the
proxy and set `SERVER` directly when running the script.

Run all Task A S1 tasks with one command:

```bash
cd "$REPO/TaskA"
bash run_taskA_s1.sh
```

Default settings:

- `MODEL=qwen3-235b-a22b-instruct-2507`
- `SERVER=http://127.0.0.1:8110/chat/completions`
- `TRIALS=30`
- `WORKERS=1`
- `MUJOCO_GL=egl`
- `PYOPENGL_PLATFORM=egl`

The command can be overridden, for example:

```bash
cd "$REPO/TaskA"
TRIALS=5 WORKERS=1 MODEL=qwen3-235b-a22b-instruct-2507 bash run_taskA_s1.sh
```

## 3. Results Summary: Task A vs Task B

Task A used privileged Robosuite configs and single-turn code generation.
The run used 30 trials per task.

| Task | Task A success | Task A avg reward | Task A code gen success | Task B success | Notes |
| --- | ---: | ---: | ---: | ---: | --- |
| Cube Lift | 30/30 (100.0%) | 1.000 | 1.000 | Pending | S1 completed reliably. |
| Cube Stack | 29/30 (96.7%) | 0.967 | 1.000 | Pending | One trial failed final completion. |
| Spill Wipe | 12/30 (40.0%) | 0.848 | 1.000 | Pending | Generated wiping trajectories, but completion criterion was stricter than partial reward. |
| Nut Assembly | 4/30 (13.3%) | 0.254 | 0.767 | Pending | Many failures came from geometry/orientation sensitivity. |
| Two Arm Lift | 2/30 (6.7%) | 0.062 | 1.000 | Pending | Two-arm grasp/orientation failures dominated. |
| Two Arm Handover | 0/30 (0.0%) | 0.067 | 0.867 | Pending | Handover planning often produced long or unstable code. |

Machine-readable Task A results are in `results/taskA_s1_summary.csv`.

### Figure 17 Alignment

The selected model corresponds to the `Qwen-235b` row in CaP-X Figure 17.
The comparison below uses the S1 columns in the Task Success Rate panel.
The paper reports N=100 per cell, while this reproduction uses N=30 per task.

| Task | Figure 17 Qwen-235b S1 | Ours | Delta |
| --- | ---: | ---: | ---: |
| Cube Lift | 96.0% | 100.0% | +4.0 pp |
| Cube Stack | 95.0% | 96.7% | +1.7 pp |
| Spill Wipe | 39.0% | 40.0% | +1.0 pp |
| Peg / Nut Assembly | 11.0% | 13.3% | +2.3 pp |
| Two-Arm Lift | 3.0% | 6.7% | +3.7 pp |
| Two-Arm Handover | 3.0% | 0.0% | -3.0 pp |
| Macro average | 41.2% | 42.8% | +1.6 pp |

The reproduction is aligned with Figure 17: the macro-average success rate is
within 1.6 percentage points, and the task difficulty ordering is preserved
up to small sampling noise from using 30 instead of 100 trials.

The same success-rate comparison is also provided as a PDF table report:
`results/taskA_figure17_comparison.pdf`.

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

The remote CaP-X working tree was patched at:

```text
capx/third_party/robosuite/robosuite/controllers/parts/controller.py
```

from:

```python
mujoco.mj_fullM(self.sim.model._model, mass_matrix, self.sim.data.qM)
```

to:

```python
mujoco.mj_fullM(self.sim.model._model, self.sim.data._data, mass_matrix)
```

### CLI boolean value

`--record-video false` is invalid for this launcher. The accepted value is:

```bash
--record-video False
```

### Parallel workers

`WORKERS=4` caused stalled or zombie worker processes during early runs.
The submitted run uses `WORKERS=1` for reproducibility. After the single-worker
run is stable, `WORKERS=2` can be tested, but the baseline numbers here are from
single-worker execution.

### Optional dependency warnings

Warnings about `LIBERO`, `R1Pro`, `robosuite_models`, or GR1 whole-body IK were
not blockers for Task A Robosuite experiments.

## Repository Layout

```text
TaskA/
TaskA/cap-x/
TaskA/run_taskA_s1.sh
code/cap-x/
TaskA/run_taskA_s1.sh
results/taskA_s1_summary.csv
results/taskA_figure17_comparison.pdf
results/taskA_run_environment.md
logs/taskA/
experiments/taskA/taskA_qwen3-235b-a22b-instruct-2507_30/
```

`TaskA/` contains the directly readable and runnable Task A CaP-X code copied
from the remote CUDA machine. `code/cap-x/` is the submitted source snapshot
used for the Task A run. Both include the local Robosuite/MuJoCo compatibility
patch used during evaluation. Runtime artifacts are excluded: `.venv`,
`outputs`, Git metadata, cache files, and local API key files are not committed.
The bundled Robosuite documentation directory is omitted from `TaskA/` because
it is not required for running the Task A code.

Secrets such as API keys, SSH passwords, and proxy key files are intentionally
not committed.
