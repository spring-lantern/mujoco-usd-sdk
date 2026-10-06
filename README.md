# MuJoCo USD SDK 构建仓库

只负责构建和打包 SDK，仿真应用位于相邻的 swarm-mujoco-cpp 仓库。
这是自行构建的 SDK，不是官方二进制发布包。官方源码子模块固定为
MuJoCo 3.15.0 和 OpenUSD v25.11。

## Ubuntu 20.04 基线构建

```bash
git submodule update --init --recursive
./scripts/build_baseline.sh
```

需要 Docker。首次制作镜像和获取上游依赖需要联网；用户使用制品时无需下载这些依赖。
构建使用独立容器，不修改现有 container_msg。
镜像准备 GCC 11、CMake 3.28.4、Python 3、X11/OpenGL 开发库和 patchelf。
Dockerfile 默认从 ubuntu:20.04 开始，也可复用已有的 20.04 镜像：

```bash
SWARM_BUILD_BASE=osrf/ros:noetic-desktop-full ./scripts/build_baseline.sh
```

本次采用本机已有的上述 20.04 镜像作为底座，以减少网络下载。构建入口已清除
继承的 ROS 启动脚本，SDK 不链接 ROS。PPA 公钥指纹来自 Launchpad 官方接口，
已在 docker/toolchain.asc 固定；实际编译器与运行库版本记录在制品 VERSION.json 中。

制品输出到 dist/baseline-时间戳/：完整 SDK 目录、tar.gz 和压缩包 SHA-256。
SDK 目录包含头文件、MuJoCo/OpenUSD/TBB 动态库、simulate/GLFW 静态库、
USD 插件资源、CMake 导入包、许可证、VERSION.json 和逐文件 SHA256SUMS。
打包工具拒绝覆盖已有制品，重复执行会使用新的输出目录。

SDK 同时打包该基线系统的 libstdc++.so.6 和 libgcc_s.so.1。
不打包 glibc、图形驱动和 ROS。动态库以 $ORIGIN 查找同目录依赖；
打包时检查所有动态库的 GLIBC 符号要求不超过 2.31，并拒绝外部构建目录依赖。
静态库禁用 LTO，避免与特定编译器的 LTO 字节码绑定。
CPU 仍要求 Linux x86_64 + AVX。

## 应用交付与验证

将完整 SDK 目录放进 swarm-mujoco-cpp/third_party/ 并纳入该仓库的 Git。
应用的 scripts/build_release.sh 使用同一个构建镜像编译并生成可搬移运行包。
应用仓库保存解压 SDK，不重复提交 SDK 压缩包；应用运行包位于其 dist/。
不要混入之前在 Ubuntu 24.04 上编译的动态库。

scripts/check_runtime.py 可在目标系统检查一个运行包：

```bash
python3 scripts/check_runtime.py /path/to/release/bin/swarm_mujoco
```

该检查不需要 ROS，通过本地 TCP 验证树林加载、7 架飞机以及独立起飞。
当前验证范围按用户要求限定为 container_msg（20.04）和宿主机（24.04）。
Ubuntu 26.04 暂不验证、不宣称已兼容。具体结果见应用仓库 COMPATIBILITY.md：20.04 容器与 24.04 宿主机的树林、多机、TCP 单机起飞及官方窗口检查均已通过。

## 本机构建（维护用途）

```bash
cmake -S . -B build
cmake --build build -j4
python3 scripts/package_sdk.py
```

本机构建会使用当前系统的 glibc 基线，不能替代 20.04 容器制品。
可用 -DSWARM_USD_ROOT=/absolute/path 指定同环境、同版本、Release/shared、
无 Python/imaging 的 OpenUSD 安装；禁止将 24.04 安装目录拿到 20.04 构建中复用。

GCC 11 对上游碰撞代码的条件赋值会报告初始化警告。集成层保留该警告但不将其升级为编译错误；官方源码未修改，应用自身的警告策略不变。
