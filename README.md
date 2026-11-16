# MuJoCo USD 与 Filament SDK

本仓库构建 Ubuntu 20.04 / x86_64 的原生 C++ SDK，固定 MuJoCo 4.0.1、OpenUSD 25.11 和 MuJoCo 指定的 Filament 源码版本。制品不需要 Python 运行时。

现行入口：[架构说明](docs/架构说明.md)。

## 构建

```bash
git submodule update --init --recursive
./scripts/build_baseline.sh
```

需要 Docker 和首次下载依赖的网络。脚本先核对 MuJoCo 官方提交并应用本仓库补丁，然后在独立 Ubuntu 20.04 容器中使用 Clang 18、GCC 11 的 libstdc++ 构建。原来的 `build-ubuntu20.04/` 与已发布 SDK 不会被覆盖；本版本使用 `build-ubuntu20.04-4.0.1/`。

输出位于 `dist/baseline-时间戳/`，包括 SDK 目录、压缩包和 SHA-256。应用通过 `find_package(SwarmMuJoCoSDK CONFIG REQUIRED)` 接入，原生 USD 开发也可通过 `find_package(pxr CONFIG REQUIRED)` 接入。

可以复用本机已存在的 Ubuntu 20.04 镜像作为构建底座：

```bash
SWARM_BUILD_BASE=osrf/ros:noetic-desktop-full ./scripts/build_baseline.sh
```

这是自行构建、带明确补丁的 SDK，不是官方二进制发布包。实际编译器、源码提交、补丁哈希、GLIBC 要求和许可证随制品保存。发布前仍须在仿真应用中验证窗口、场景、多机物理与控制链路。
