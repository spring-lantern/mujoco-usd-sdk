cmake_minimum_required(VERSION 3.18)
project(mujoco_usd_sdk LANGUAGES C CXX)
if(NOT SWARM_ENGINE_BUILD)
  include(cmake/Dependencies.cmake)
  return()
endif()
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type" FORCE)
endif()
set(MUJOCO_WITH_USD ON CACHE BOOL "USD is required by this project" FORCE)
set(MUJOCO_BUILD_TESTS OFF CACHE BOOL "" FORCE)
set(MUJOCO_TEST_PYTHON_UTIL OFF CACHE BOOL "" FORCE)
set(MUJOCO_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
set(MUJOCO_BUILD_SIMULATE ON CACHE BOOL "" FORCE)
set(MUJOCO_BUILD_STUDIO OFF CACHE BOOL "" FORCE)
set(SIMULATE_BUILD_EXECUTABLE OFF CACHE BOOL "" FORCE)
set(GLFW_BUILD_WAYLAND OFF CACHE BOOL "" FORCE)
set(GLFW_BUILD_X11 ON CACHE BOOL "" FORCE)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
# SDK static libraries must contain ordinary objects, not compiler-specific LTO bytecode.
set(MUJOCO_ENABLE_LTO OFF CACHE BOOL "" FORCE)
set(CMAKE_INTERPROCEDURAL_OPTIMIZATION OFF)
add_subdirectory(third_party/mujoco EXCLUDE_FROM_ALL)
# 3.15.0 的 USD 源码使用 third_party/mujoco/... 形式的包含路径，
# 且上游插件 CMake 遗漏 newton_tokens.cc；在集成层补齐，不修改子模块。
target_include_directories(usd_decoder_plugin PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}")
target_sources(usd_decoder_plugin PRIVATE
  "${CMAKE_CURRENT_SOURCE_DIR}/third_party/mujoco/plugin/usd_decoder/newton_tokens.cc")
# 官方仅在 install 阶段复制这个 schema；本项目从 build 目录直接运行。
configure_file(
  "${CMAKE_CURRENT_SOURCE_DIR}/third_party/mujoco/src/experimental/usd/mjcPhysics/generatedSchema.usda"
  "${CMAKE_BINARY_DIR}/${CMAKE_INSTALL_LIBDIR}/mujoco-usd-resources/mjcPhysics/generatedSchema.usda"
  COPYONLY)

add_custom_target(sdk_libraries ALL DEPENDS mujoco libmujoco_simulate glfw usd_decoder_plugin usdMjcf)
