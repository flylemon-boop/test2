# Task B Code

This directory contains the runnable Task B AlphaApollo code copied from the
remote CUDA machine.

Main entry points:

```text
run_taskB.sh
run_taskB_generation.sh
AlphaApollo/alphaapollo/core/environments/embodied_robosuite/
AlphaApollo/alphaapollo/core/tools/embodied_robosuite.py
AlphaApollo/scripts/run_taskB_robosuite_api.py
AlphaApollo/scripts/run_alphaapollo_taskB_generation.sh
AlphaApollo/scripts/run_taskB_robosuite_eval.py
AlphaApollo/scripts/run_taskB_robosuite_eval.sh
AlphaApollo/scripts/start_taskB_pyroki_server.py
AlphaApollo/examples/configs/taskB_robosuite.yaml
```

Typical run from a fresh clone:

```bash
git clone -b taskB https://github.com/flylemon-boop/test2.git
cd test2
export REPO="$(pwd)"

# Use the conda path for the current machine.
source /path/to/miniconda3/etc/profile.d/conda.sh
conda activate taskb

cd "$REPO/TaskB"
TRIALS=30 MAX_TURNS=4 bash run_taskB.sh
```

If the environment needs extra setup, put it in a local file and pass it to the
runner:

```bash
export TASKB_ENV="$REPO/taskb_env.sh"
cd "$REPO/TaskB"
TRIALS=30 MAX_TURNS=4 bash run_taskB.sh
```

Place `api.csv` at `$REPO/api.csv` or `$REPO/TaskB/api.csv`, or set
`OPENAI_API_KEY` and `SERVER` manually before running.

Runtime artifacts and secrets are not included: `.git`, `.venv`, `outputs`,
cache files, API key files, and proxy base URL files were excluded.
