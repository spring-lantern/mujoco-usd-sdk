get_filename_component(_sdk "${CMAKE_CURRENT_LIST_DIR}/../../.." ABSOLUTE)
include(CMakeFindDependencyMacro)
find_dependency(Threads)
if(NOT TARGET mujoco::mujoco)
  add_library(mujoco::mujoco SHARED IMPORTED)
  set_target_properties(mujoco::mujoco PROPERTIES
    IMPORTED_LOCATION "${_sdk}/lib/libmujoco.so.4.0.1"
    INTERFACE_INCLUDE_DIRECTORIES "${_sdk}/include"
    INTERFACE_LINK_LIBRARIES "${_sdk}/lib/libstdc++.so.6")
  add_library(glfw STATIC IMPORTED)
  set_target_properties(glfw PROPERTIES
    IMPORTED_LOCATION "${_sdk}/lib/libglfw3.a"
    INTERFACE_INCLUDE_DIRECTORIES "${_sdk}/include"
    INTERFACE_LINK_LIBRARIES "Threads::Threads;${CMAKE_DL_LIBS};m")
  file(GLOB _sdk_filament_archives "${_sdk}/lib/filament/*.a")
  list(SORT _sdk_filament_archives)
  add_library(mujoco::filament INTERFACE IMPORTED)
  set_target_properties(mujoco::filament PROPERTIES
    INTERFACE_INCLUDE_DIRECTORIES "${_sdk}/include"
    INTERFACE_LINK_LIBRARIES "-Wl,--start-group;${_sdk_filament_archives};-Wl,--end-group;Threads::Threads;${CMAKE_DL_LIBS};m;X11")
  set(SWARM_MUJOCO_FILAMENT_ASSETS "${_sdk}/share/mujoco/filament")
  add_library(mujoco::libmujoco_simulate STATIC IMPORTED)
  set_target_properties(mujoco::libmujoco_simulate PROPERTIES
    IMPORTED_LOCATION "${_sdk}/lib/libsimulate.a"
    INTERFACE_INCLUDE_DIRECTORIES "${_sdk}/include/simulate"
    INTERFACE_LINK_LIBRARIES "mujoco::mujoco;glfw;Threads::Threads;mujoco::filament")
  add_library(usd_decoder_plugin SHARED IMPORTED)
  set_target_properties(usd_decoder_plugin PROPERTIES
    IMPORTED_LOCATION "${_sdk}/lib/libusd_decoder_plugin.so")
endif()
unset(_sdk_filament_archives)
unset(_sdk)
