#!/usr/bin/env bash
set -euo pipefail

# Run the full Docker image with sensible defaults
IMAGE_NAME=program-handlu-krypto:full
CONTAINER_NAME=program-handlu-krypto-run

docker run --rm -it \
  --name "$CONTAINER_NAME" \
  -p 8050:8050 \
  -e BINANCE_API_KEY \
  -e BINANCE_SECRET \
  -e NEWSAPI_KEY \
  -e TWITTER_BEARER_TOKEN \
  -e REDDIT_CLIENT_ID \
  -e REDDIT_CLIENT_SECRET \
  -e REDDIT_USER_AGENT \
  "$IMAGE_NAME"
