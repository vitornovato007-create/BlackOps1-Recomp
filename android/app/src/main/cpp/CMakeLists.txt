cmake_minimum_required(VERSION 3.25)
project(BlackOps1AndroidNative LANGUAGES C CXX)

if(NOT ANDROID OR NOT CMAKE_ANDROID_ARCH_ABI STREQUAL "arm64-v8a")
  message(FATAL_ERROR
    "BlackOps1-Recomp requer build Android ARM64 (arm64-v8a).")
endif()

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

get_filename_component(
  BLACKOPS1_ROOT
  "${CMAKE_CURRENT_SOURCE_DIR}/../../../../.."
  ABSOLUTE
)

set(REXGLUE_SOURCE_DIR "${BLACKOPS1_ROOT}/rexglue-sdk")
set(BLACKOPS1_GENERATED_DIR "${BLACKOPS1_ROOT}/generated")

foreach(_required
    "${REXGLUE_SOURCE_DIR}/CMakeLists.txt"
    "${REXGLUE_SOURCE_DIR}/thirdparty/sdl3/CMakeLists.txt"
    "${REXGLUE_SOURCE_DIR}/include/rex/rex_app.h"
    "${BLACKOPS1_ROOT}/src/main.cpp"
    "${BLACKOPS1_ROOT}/src/blackops1_app.h"
    "${BLACKOPS1_GENERATED_DIR}/sources.cmake"
    "${BLACKOPS1_GENERATED_DIR}/headers/blackops1_init.h"
    "${BLACKOPS1_GENERATED_DIR}/headers/blackops1_pch.h"
)
  if(NOT EXISTS "${_required}")
    message(FATAL_ERROR
      "Arquivo indispensavel ausente: ${_required}. "
      "Inicialize o SDK SDL3 e gere os fontes do jogo antes "
      "de compilar o runtime.")
  endif()
endforeach()

# Configuracao do ReXGlue para Android.
set(REXGLUE_USE_D3D12 OFF CACHE BOOL "" FORCE)
set(REXGLUE_USE_VULKAN ON CACHE BOOL "" FORCE)
set(REXGLUE_BUILD_TESTS OFF CACHE BOOL "" FORCE)
set(REXGLUE_ENABLE_TRACY OFF CACHE BOOL "" FORCE)
set(REXGLUE_ENABLE_PERF_COUNTERS OFF CACHE BOOL "" FORCE)
set(REXGLUE_ENABLE_SANITIZERS OFF CACHE BOOL "" FORCE)

# Configuracao do SDL3.
set(SDL_SHARED ON CACHE BOOL "" FORCE)
set(SDL_STATIC OFF CACHE BOOL "" FORCE)
set(SDL_TEST_LIBRARY OFF CACHE BOOL "" FORCE)

find_library(android_log_lib log REQUIRED)
find_library(android_lib android REQUIRED)
find_library(dl_lib dl REQUIRED)
find_library(vulkan_lib vulkan REQUIRED)

add_subdirectory(
  "${REXGLUE_SOURCE_DIR}"
  "${CMAKE_BINARY_DIR}/rexglue-sdk"
)

include("${BLACKOPS1_GENERATED_DIR}/sources.cmake")

if(NOT GENERATED_SOURCES)
  message(FATAL_ERROR
    "generated/sources.cmake nao definiu GENERATED_SOURCES; "
    "nao e possivel ligar o codigo do jogo.")
endif()

# Biblioteca principal do runtime. O extrator XISO fica em uma
# biblioteca separada para que o launcher não carregue SDL3/ReXGlue.
add_library(blackops1_android SHARED
  native-lib.cpp
  "${BLACKOPS1_ROOT}/src/main.cpp"
  "${REXGLUE_SOURCE_DIR}/src/ui/windowed_app_main_sdl.cpp"
  "${REXGLUE_SOURCE_DIR}/src/ui/rex_app.cpp"
  ${GENERATED_SOURCES}
)

# Integra o extrator XISO como blackops1_xiso, sem adicioná-lo ao runtime.
include("${CMAKE_CURRENT_LIST_DIR}/xiso-integration.cmake")

target_include_directories(blackops1_android PRIVATE
  "${BLACKOPS1_ROOT}"
  "${BLACKOPS1_ROOT}/src"
  "${BLACKOPS1_GENERATED_DIR}"
  "${BLACKOPS1_GENERATED_DIR}/headers"
  "${REXGLUE_SOURCE_DIR}/include"
  "${REXGLUE_SOURCE_DIR}/src"
  "${REXGLUE_SOURCE_DIR}/thirdparty"
)

target_compile_options(blackops1_android PRIVATE
  -Wall
  -Wextra
  -fno-strict-aliasing
  -fno-char8_t
)

target_compile_definitions(blackops1_android PRIVATE
  REXGLUE_BUILD_CONFIG="$<CONFIG>"
)

target_link_libraries(blackops1_android PRIVATE
  rex::runtime
  rex::ui
  rex::audio
  rex::input
  rex::gpu-xenos
  SDL3::SDL3
  ${android_log_lib}
  ${android_lib}
  ${dl_lib}
  ${vulkan_lib}
)

set_target_properties(blackops1_android PROPERTIES
  OUTPUT_NAME "blackops1_android"
  CXX_VISIBILITY_PRESET default
  VISIBILITY_INLINES_HIDDEN OFF
)

# SDLActivity carrega SDL3 como biblioteca dinamica. Use o mesmo alvo
# SDL3::SDL3 que o runtime ja vincula, sem presumir o nome interno do alvo
# (que varia entre versoes do SDL3).
if(NOT TARGET SDL3::SDL3)
  message(FATAL_ERROR
    "O alvo SDL3::SDL3 nao existe. Verifique a configuracao do SDL3.")
endif()

get_target_property(SDL3_LINK_TARGET SDL3::SDL3 ALIASED_TARGET)
if(NOT SDL3_LINK_TARGET)
  set(SDL3_LINK_TARGET SDL3::SDL3)
endif()

get_target_property(SDL3_LINK_TYPE "${SDL3_LINK_TARGET}" TYPE)
if(NOT SDL3_LINK_TYPE STREQUAL "SHARED_LIBRARY")
  message(FATAL_ERROR
    "SDL3::SDL3 nao e uma biblioteca compartilhada (tipo: ${SDL3_LINK_TYPE}). "
    "SDLActivity precisa de libSDL3.so.")
endif()

set(SDL3_ANDROID_JNILIBS_DIR
    "${CMAKE_CURRENT_SOURCE_DIR}/../jniLibs/arm64-v8a")

add_custom_command(TARGET blackops1_android POST_BUILD
  COMMAND "${CMAKE_COMMAND}" -E make_directory
          "${SDL3_ANDROID_JNILIBS_DIR}"
  COMMAND "${CMAKE_COMMAND}" -E copy_if_different
          "$<TARGET_FILE:SDL3::SDL3>"
          "${SDL3_ANDROID_JNILIBS_DIR}/libSDL3.so"
  COMMENT "Empacotando libSDL3.so para Android ARM64"
  VERBATIM
)
