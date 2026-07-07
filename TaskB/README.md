# Task B Code

This directory contains the runnable Task B AlphaApollo code copied from the
remote CUDA machine.

Main entry points:

```text
AlphaApollo/alphaapollo/core/environments/embodied_robosuite/
AlphaApollo/alphaapollo/core/tools/embodied_robosuite.py
AlphaApollo/scripts/run_taskB_robosuite_eval.py
AlphaApollo/scripts/run_taskB_robosuite_eval.sh
AlphaApollo/scripts/start_taskB_pyroki_server.py
AlphaApollo/examples/configs/taskB_robosuite.yaml
```

Typical remote run:

```bash
cd TaskB/AlphaApollo
TRIALS=30 MAX_TURNS=4 bash scripts/run_taskB_robosuite_eval.sh
```

Runtime artifacts and secrets are not included: `.git`, `.venv`, `outputs`,
cache files, API key files, and proxy base URL files were excluded.
