#!/usr/bin/env bash
set -euo pipefail

# Attempt to install Python 3.11 on Debian/Ubuntu using deadsnakes PPA.
# Requires sudo privileges.

if ! command -v sudo >/dev/null 2>&1; then
  echo "sudo not found. Please run this script on a machine with sudo and apt."
  exit 1
fi

sudo apt-get update
sudo apt-get install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv python3.11-dev

echo "Python 3.11 installed. You can create a venv with: python3.11 -m venv .venv311"
