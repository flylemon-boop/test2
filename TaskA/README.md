# Task A Code Bundle

This directory contains the Task A code bundle exported from the remote CUDA
machine.

The full CaP-X snapshot is stored as split archive parts because large ordinary
Git pushes are unreliable for this repository:

```text
archive/TaskA_capx_code.tar.gz.part_*
```

To reconstruct the readable code tree:

```bash
mkdir -p cap-x
cat archive/TaskA_capx_code.tar.gz.part_* > TaskA_capx_code.tar.gz
tar -xzf TaskA_capx_code.tar.gz -C cap-x
```

The convenience runner is also included:

```text
run_taskA_s1.sh
```

The archive excludes runtime artifacts and secrets such as `.git`, `.venv`,
`outputs`, cache files, API key files, and proxy base URL files.
