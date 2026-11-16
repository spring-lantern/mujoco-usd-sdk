#!/usr/bin/env bash
set -euo pipefail
sdk_root=$(cd -- "$(dirname -- "$0")/.." && pwd)
# 固定官方版本并仅应用当前SDK所需补丁；已应用时不重复修改源码。
test "$(git -C "$sdk_root/third_party/mujoco" rev-parse HEAD)" = 4ed093a9f06b170bd1564942fa37e1bb907d93e3
sdk_patch="$sdk_root/patches/mujoco-4.0.1.patch"
if ! git -C "$sdk_root/third_party/mujoco" apply --reverse --check "$sdk_patch" 2>/dev/null; then
  git -C "$sdk_root/third_party/mujoco" apply --check "$sdk_patch"
  git -C "$sdk_root/third_party/mujoco" apply "$sdk_patch"
fi
docker build --build-arg BASE_IMAGE="${SWARM_BUILD_BASE:-ubuntu:20.04}" -f "$sdk_root/docker/Dockerfile.ubuntu20.04" -t swarm-mujoco-filament-builder:ubuntu20.04 "$sdk_root"
docker run --rm --user "$(id -u):$(id -g)" -e HOME=/tmp \
  -v "$sdk_root:/workspace/sdk" -w /workspace/sdk \
  swarm-mujoco-filament-builder:ubuntu20.04 bash -lc '
    set -euo pipefail
    cmake -S . -B build-ubuntu20.04-4.0.1
    cmake --build build-ubuntu20.04-4.0.1 -j4
    python3 scripts/package_sdk.py --build build-ubuntu20.04-4.0.1 --output "dist/baseline-$(date +%Y%m%d-%H%M%S)"
  '
