#!/usr/bin/env bash
set -euo pipefail

# Build Docker image for full environment
IMAGE_NAME=program-handlu-krypto:full

docker build -f Dockerfile.full -t "$IMAGE_NAME" .
echo "Built image: $IMAGE_NAME"
