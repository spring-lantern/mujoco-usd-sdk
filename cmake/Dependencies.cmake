include(ExternalProject)
find_package(Python3 REQUIRED COMPONENTS Interpreter)
foreach(dependency mujoco openusd)
  if(NOT EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/third_party/${dependency}/CMakeLists.txt")
    message(FATAL_ERROR "Missing ${dependency} source. Run git submodule update --init --recursive")
  endif()
endforeach()
set(SWARM_USD_ROOT "${CMAKE_BINARY_DIR}/deps/usd" CACHE PATH "OpenUSD installation")
if(NOT EXISTS "${SWARM_USD_ROOT}/pxrConfig.cmake")
# OpenUSD 自带的构建工具只在编译期间运行；应用不依赖 Python。
ExternalProject_Add(swarm_openusd
  SOURCE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/third_party/openusd"
  DOWNLOAD_COMMAND "" UPDATE_COMMAND "" CONFIGURE_COMMAND "" INSTALL_COMMAND ""
  BUILD_COMMAND "${Python3_EXECUTABLE}"
    "${CMAKE_CURRENT_SOURCE_DIR}/third_party/openusd/build_scripts/build_usd.py"
    --jobs 4 --build-shared --no-examples --no-tools --no-ptex --no-prman
    --no-openimageio --no-opencolorio --no-alembic --no-draco --no-materialx
    --no-tutorials --no-tests --no-docs --no-imaging --no-python --no-usdValidation
    "${SWARM_USD_ROOT}"
  BUILD_ALWAYS TRUE
  BUILD_BYPRODUCTS "${SWARM_USD_ROOT}/pxrConfig.cmake")
else()
  add_custom_target(swarm_openusd)
endif()
ExternalProject_Add(swarm_engine
  DEPENDS swarm_openusd
  SOURCE_DIR "${CMAKE_CURRENT_SOURCE_DIR}"
  BINARY_DIR "${CMAKE_BINARY_DIR}/engine"
  DOWNLOAD_COMMAND "" UPDATE_COMMAND "" INSTALL_COMMAND ""
  CMAKE_ARGS -DSWARM_ENGINE_BUILD=ON -DSWARM_BUILD_ROOT=${CMAKE_BINARY_DIR}
    -Dpxr_DIR=${SWARM_USD_ROOT} -DCMAKE_BUILD_TYPE=Release
    -DMUJOCO_CMAKE_DEP_CACHE=${CMAKE_BINARY_DIR}/source-archives
    -DCMAKE_C_COMPILER=${CMAKE_C_COMPILER} -DCMAKE_CXX_COMPILER=${CMAKE_CXX_COMPILER}
  BUILD_COMMAND "${CMAKE_COMMAND}" --build <BINARY_DIR> --target sdk_libraries --parallel 4
  BUILD_ALWAYS TRUE
)
