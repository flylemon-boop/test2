# Task A Run Environment

- Method: CaP-X S1 baseline, single-turn code generation.
- Model: `qwen3-235b-a22b-instruct-2507`.
- Server: local OpenAI-compatible proxy at `http://127.0.0.1:8110/chat/completions`.
- Trials: 30 per task.
- Workers: 1.
- Rendering: `MUJOCO_GL=egl`, `PYOPENGL_PLATFORM=egl`.
- Remote runtime: Ubuntu 22.04, RTX 4090, Python 3.10, conda env `capx`, project venv `.venv`.
- Commit of the CaP-X working tree at evaluation time: `53e9966`, dirty because of a local MuJoCo compatibility patch.

The run used the privileged Robosuite configs listed in `results/taskA_s1_summary.csv`.
