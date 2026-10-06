#!/usr/bin/env bash
set -euo pipefail
sdk_root=$(cd -- "$(dirname -- "$0")/.." && pwd)
docker build --build-arg BASE_IMAGE="${SWARM_BUILD_BASE:-ubuntu:20.04}" -f "$sdk_root/docker/Dockerfile.ubuntu20.04" -t swarm-mujoco-builder:ubuntu20.04 "$sdk_root"
docker run --rm --user "$(id -u):$(id -g)" -e HOME=/tmp \
  -v "$sdk_root:/workspace/sdk" -w /workspace/sdk \
  swarm-mujoco-builder:ubuntu20.04 bash -lc '
    set -euo pipefail
    cmake -S . -B build-ubuntu20.04
    cmake --build build-ubuntu20.04 -j4
    python3 scripts/package_sdk.py --build build-ubuntu20.04 --output "dist/baseline-$(date +%Y%m%d-%H%M%S)"
  '
