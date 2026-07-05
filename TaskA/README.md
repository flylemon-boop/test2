# Task A Code

This directory contains the runnable Task A CaP-X code copied from the remote
CUDA machine.

Main entry points:

```text
run_taskA_s1.sh
cap-x/capx/envs/launch.py
cap-x/env_configs/
```

Typical remote run:

```bash
cd TaskA/cap-x
source /root/miniconda3/etc/profile.d/conda.sh
conda activate capx
source .venv/bin/activate
bash ../run_taskA_s1.sh
```

Runtime artifacts and secrets are not included: `.git`, `.venv`, `outputs`,
cache files, API key files, and proxy base URL files were excluded.
