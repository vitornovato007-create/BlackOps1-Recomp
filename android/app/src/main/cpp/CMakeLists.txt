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
set(BLACKOPS1_JNILIBS_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../jniLibs/arm64-v8a")

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

# Configuracao do ReXGlue para Android ARM64.
set(REXGLUE_USE_D3D12 OFF CACHE BOOL "" FORCE)
set(REXGLUE_USE_VULKAN ON CACHE BOOL "" FORCE)
set(REXGLUE_BUILD_TESTS OFF CACHE BOOL "" FORCE)
set(REXGLUE_ENABLE_TRACY OFF CACHE BOOL "" FORCE)
set(REXGLUE_ENABLE_PERF_COUNTERS OFF CACHE BOOL "" FORCE)
set(REXGLUE_ENABLE_SANITIZERS OFF CACHE BOOL "" FORCE)

# SDL3 deve ser compartilhado porque SDLActivity carrega libSDL3.so por nome.
# O SDK define o sufixo 'd' nas bibliotecas Debug; SDL3 e uma excecao porque o
# Java procura sempre libSDL3.so. O nome SONAME e o arquivo empacotado precisam
# coincidir, ou System.loadLibrary("SDL3")/dlopen falha ao abrir o runtime.
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

# O ReXGlue compila rexcore/rexui/rexaudio/rexinput como OBJECT libraries e
# incorpora seus objetos no librexruntime.so. NAO os vincule de novo ao app:
# isso duplica registros globais (cvars, janelas, input e audio) entre DSO.
# A app so precisa das cabecalhos e das dependencias de cabecalho do renderizador.
add_library(blackops1_headers INTERFACE)
target_include_directories(blackops1_headers INTERFACE
  $<TARGET_PROPERTY:imgui,INTERFACE_INCLUDE_DIRECTORIES>
  "${REXGLUE_SOURCE_DIR}/src"
  "${REXGLUE_SOURCE_DIR}/thirdparty"
)
target_link_libraries(blackops1_headers INTERFACE
  renderdoc
  Vulkan::Headers
  GPUOpen::VulkanMemoryAllocator
  spirv-tools-headers
)

# O SDK configura SDL3 como alvo compartilhado. Remover apenas o postfix de
# SDL3, nao o postfix das outras bibliotecas do ReXGlue: o loader de GPU usa o
# postfix de configuracao para encontrar librexgpu-xenosd.so em Debug.
if(TARGET SDL3-shared)
  set(SDL3_LINK_TARGET SDL3-shared)
else()
  get_target_property(SDL3_LINK_TARGET SDL3::SDL3 ALIASED_TARGET)
  if(NOT SDL3_LINK_TARGET)
    set(SDL3_LINK_TARGET SDL3::SDL3)
  endif()
endif()

if(NOT TARGET SDL3::SDL3)
  message(FATAL_ERROR
    "O alvo SDL3::SDL3 nao existe. Verifique a configuracao do SDL3.")
endif()

get_target_property(SDL3_LINK_TYPE "${SDL3_LINK_TARGET}" TYPE)
if(NOT SDL3_LINK_TYPE STREQUAL "SHARED_LIBRARY")
  message(FATAL_ERROR
    "SDL3::SDL3 nao e uma biblioteca compartilhada (tipo: ${SDL3_LINK_TYPE}). "
    "SDLActivity precisa de libSDL3.so.")
endif()

set_target_properties("${SDL3_LINK_TARGET}" PROPERTIES
  DEBUG_POSTFIX ""
  RELWITHDEBINFO_POSTFIX ""
)

if(TARGET rexgpu-xenos)
  # O plugin e carregado pelo nome calculado em gpu_plugin_loader.cpp; nao
  # deve ser linkado ao app. Compilar e copiar para nativeLibraryDir e suficiente.
  set_property(TARGET rexgpu-xenos PROPERTY POSITION_INDEPENDENT_CODE ON)
endif()

# A app gerada e uma biblioteca separada. Assim os simbolos do jogo ficam
# ligados ao mesmo librexruntime.so que fornece cvars, UI, audio e input.
include("${BLACKOPS1_GENERATED_DIR}/sources.cmake")

if(NOT GENERATED_SOURCES)
  message(FATAL_ERROR
    "generated/sources.cmake nao definiu GENERATED_SOURCES; "
    "nao e possivel ligar o codigo do jogo.")
endif()

add_library(blackops1_recomp STATIC ${GENERATED_SOURCES})
target_include_directories(blackops1_recomp PRIVATE
  "${BLACKOPS1_ROOT}"
  "${BLACKOPS1_ROOT}/src"
  "${BLACKOPS1_GENERATED_DIR}"
  "${BLACKOPS1_GENERATED_DIR}/headers"
  "${REXGLUE_SOURCE_DIR}/include"
)
target_link_libraries(blackops1_recomp PUBLIC
  rex::runtime
  blackops1_headers
)

if(COMMAND rexglue_apply_target_settings)
  rexglue_apply_target_settings(blackops1_recomp)
endif()

target_precompile_headers(blackops1_recomp PRIVATE
  "${BLACKOPS1_GENERATED_DIR}/headers/blackops1_pch.h"
)
target_compile_options(blackops1_recomp PRIVATE
  -gline-tables-only
  -Wno-unused-variable
)

# Entrada nativa SDL3. Segue o padrao Android do NFSMW-Recompiled-Mobile:
# SDL_main prepara o contexto Android, cria SDLWindowedAppContext e chama o
# criador registado por REX_DEFINE_APP. Nao se linkam object libraries do SDK.
add_library(blackops1_android SHARED
  native-lib.cpp
  "${BLACKOPS1_ROOT}/src/main.cpp"
  android_main.cpp
  "${REXGLUE_SOURCE_DIR}/src/ui/rex_app.cpp"
)

target_include_directories(blackops1_android PRIVATE
  "${BLACKOPS1_ROOT}"
  "${BLACKOPS1_ROOT}/src"
  "${BLACKOPS1_GENERATED_DIR}"
  "${BLACKOPS1_GENERATED_DIR}/headers"
  "${REXGLUE_SOURCE_DIR}/include"
  "${REXGLUE_SOURCE_DIR}/src"
  "${REXGLUE_SOURCE_DIR}/src/ui"
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
  XE_UI_WINDOWED_APPS_IN_LIBRARY=1
)

target_link_libraries(blackops1_android PRIVATE
  rex::runtime
  blackops1_headers
  blackops1_recomp
  ${android_log_lib}
  ${android_lib}
  ${dl_lib}
  ${vulkan_lib}
)

# ReX_DEFINE_APP / runtime plugins resolve exported game symbols from this DSO.
target_link_options(blackops1_android PRIVATE
  "-Wl,--export-dynamic"
  "-Wl,-z,max-page-size=16384"
)

set_target_properties(blackops1_android PROPERTIES
  OUTPUT_NAME "blackops1_android"
  CXX_VISIBILITY_PRESET default
  VISIBILITY_INLINES_HIDDEN OFF
)

# SDLActivity chama System.loadLibrary("SDL3") e o loader nativo usa o SONAME
# do mesmo alvo. O arquivo copiado precisa ser libSDL3.so em Debug e Release.
target_link_options("${SDL3_LINK_TARGET}" PRIVATE "-Wl,-z,max-page-size=16384")
add_custom_command(TARGET blackops1_android POST_BUILD
  COMMAND "${CMAKE_COMMAND}" -E make_directory "${BLACKOPS1_JNILIBS_DIR}"
  COMMAND "${CMAKE_COMMAND}" -E copy_if_different
          "$<TARGET_FILE:SDL3::SDL3>"
          "${BLACKOPS1_JNILIBS_DIR}/libSDL3.so"
  COMMENT "Empacotando libSDL3.so com SONAME consistente para Android ARM64"
  VERBATIM
)

# O loader do ReXGlue procura o plugin em nativeLibraryDir e acrescenta o
# postfix de configuracao (por exemplo, librexgpu-xenosd.so em Debug). Nao
# linke o plugin ao app: copie-o com o nome original calculado pelo SDK.
if(TARGET rexgpu-xenos)
  add_dependencies(blackops1_android rexgpu-xenos)
  # O POST_BUILD do plugin cobre builds limpos; esta copia adicional no app
  # cobre rebuilds incrementais quando o app muda mas o plugin nao.
  add_custom_command(TARGET blackops1_android POST_BUILD
    COMMAND "${CMAKE_COMMAND}" -E make_directory "${BLACKOPS1_JNILIBS_DIR}"
    COMMAND "${CMAKE_COMMAND}" -E copy_if_different
            "$<TARGET_FILE:rexgpu-xenos>"
            "${BLACKOPS1_JNILIBS_DIR}/$<TARGET_FILE_NAME:rexgpu-xenos>"
    COMMENT "Confirmando plugin ReXGlue Xenos em nativeLibraryDir"
    VERBATIM
  )
  add_custom_command(TARGET rexgpu-xenos POST_BUILD
    COMMAND "${CMAKE_COMMAND}" -E make_directory "${BLACKOPS1_JNILIBS_DIR}"
    COMMAND "${CMAKE_COMMAND}" -E copy_if_different
            "$<TARGET_FILE:rexgpu-xenos>"
            "${BLACKOPS1_JNILIBS_DIR}/$<TARGET_FILE_NAME:rexgpu-xenos>"
    COMMENT "Empacotando plugin ReXGlue Xenos com postfix de configuracao correto"
    VERBATIM
  )
else()
  message(FATAL_ERROR
    "O alvo rexgpu-xenos nao existe; o runtime Black Ops 1 precisa do plugin Xenos.")
endif()
