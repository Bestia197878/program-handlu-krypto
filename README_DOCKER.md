# Docker development environment

This repository includes `Dockerfile.full` to create a reproducible environment
with Python 3.11 and the project's `requirements.txt` installed.

Build image:

```bash
./scripts/build_docker.sh
```

Run container:

```bash
./scripts/run_docker.sh
```

Notes:
- The Docker image uses `--prefer-binary` when installing `requirements.txt` to prefer wheels.
- For GPU support, use an appropriate PyTorch base image (e.g. `pytorch/pytorch:...`) and adjust the Dockerfile.
- If you prefer installing on host, `scripts/install_python311.sh` attempts to install Python 3.11 (requires sudo).
