# MuJoCo USD SDK 构建仓库

本仓库只负责构建和打包 SDK。它不是仿真应用，也不是官方二进制发布包。
官方源码由子模块固定：MuJoCo 3.15.0、OpenUSD v25.11。

## 构建与打包

Ubuntu 构建机准备 C/C++ 编译器、CMake（至少 3.18）、Python 3、Git、make、
patchelf，以及 libx11-dev、libxrandr-dev、libxinerama-dev、libxcursor-dev、
libxi-dev、libgl-dev。SDK 制作阶段可能下载官方第三方依赖；应用编译不下载。

```bash
git submodule update --init --recursive
cmake -S . -B build
cmake --build build -j4
python3 scripts/package_sdk.py
```

制品输出到 dist/：版本化 SDK 目录、同名 tar.gz、压缩包 SHA-256 校验文件。
SDK 目录包含头文件、动态库、simulate/GLFW 静态库、USD 插件资源、许可证、
VERSION.json 和逐文件 SHA256SUMS。为避免无意替换，打包工具拒绝覆盖已有目录。
如需重新打包，可指定新的 `--output dist/rebuild`。

已有相同配置的 OpenUSD 25.11 安装目录时，可配置
`-DSWARM_USD_ROOT=/absolute/path/to/openusd` 复用它；要求 Release、shared、
无 Python 和 imaging。默认会在 build/deps/usd 构建。首次制品复用了本机已经编译的
同版本 OpenUSD，MuJoCo 和界面库在本仓库重新构建。

## 应用交付

将完整 SDK 目录复制到 swarm-mujoco-cpp/third_party/ 并用该应用仓库的 Git
管理。应用通过 SDK 自带 CMake 包导入库，不引用本仓库，也不要求本仓库存在。
应用仓库不重复保存 tar.gz；压缩包用于独立分发。

SDK 内动态库使用 $ORIGIN 查找同目录依赖。无需 LD_LIBRARY_PATH。
不要拆散 lib/usd 和 lib/mujoco-usd-resources；USD 需要这些插件资源。
静态库禁用 LTO，避免绑定特定 GCC 的 LTO 字节码版本。

首个 SDK 的构建平台为 Ubuntu 24.04 x86_64、GCC 13、glibc 2.39，CPU 需要 AVX。
路径中出现 ubuntu20.04 不代表宿主系统是 20.04。
不承诺兼容 Ubuntu 20.04/22.04、ARM 或 Windows；这些平台需分别制作制品。
显卡驱动、系统 C/C++ 运行库不打包。制品升级使用新版本目录和新的 Git 提交。
普通 Git 保存二进制会累积历史体积，当前先遵循直接纳入仓库的方式，不依赖 LFS 服务。
