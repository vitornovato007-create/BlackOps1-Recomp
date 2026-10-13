cmake_minimum_required(VERSION 3.25)

project(BlackOps1Recomp LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

set(REXGLUE_ENABLE_TRACY OFF CACHE BOOL "" FORCE)
set(REXGLUE_ENABLE_PERF_COUNTERS OFF CACHE BOOL "" FORCE)

set(REXGLUE_SOURCE_DIR
    "${CMAKE_CURRENT_SOURCE_DIR}/rexglue-sdk")

set(BLACKOPS1_MANIFEST
    "${CMAKE_CURRENT_SOURCE_DIR}/blackops1_manifest.toml")

set(BLACKOPS1_XEX
    "${CMAKE_CURRENT_SOURCE_DIR}/game/default.xex")

set(BLACKOPS1_GENERATED_DIR
    "${CMAKE_CURRENT_SOURCE_DIR}/generated")

# Verificar arquivos necessários.
if(NOT EXISTS "${REXGLUE_SOURCE_DIR}/CMakeLists.txt")
    message(FATAL_ERROR
        "ReXGlue SDK não encontrado: ${REXGLUE_SOURCE_DIR}")
endif()

if(NOT EXISTS "${BLACKOPS1_MANIFEST}")
    message(FATAL_ERROR
        "Manifesto não encontrado: ${BLACKOPS1_MANIFEST}")
endif()

if(NOT EXISTS "${BLACKOPS1_XEX}")
    message(FATAL_ERROR
        "Arquivo default.xex não encontrado: ${BLACKOPS1_XEX}")
endif()

# Verificar o cabeçalho do ImGui.
set(IMGUI_INCLUDE_DIR
    "${REXGLUE_SOURCE_DIR}/thirdparty/imgui")

if(NOT EXISTS "${IMGUI_INCLUDE_DIR}/imgui.h")
    message(FATAL_ERROR
        "imgui.h não encontrado em: ${IMGUI_INCLUDE_DIR}")
endif()

# Carregar o SDK.
add_subdirectory(rexglue-sdk)

if(NOT TARGET rexglue)
    message(FATAL_ERROR
        "O SDK foi carregado, mas o alvo rexglue não existe.")
endif()

# Disponibilizar o ImGui para o alvo principal.
# O diretório é aplicado depois da criação do alvo blackops1.
# A integração do alvo é feita mais abaixo.

# Integrar as regras geradas pelo ReXGlue.
include(
    "${BLACKOPS1_GENERATED_DIR}/rexglue.cmake"
)

# Executável principal.
add_executable(blackops1
    src/main.cpp
)

target_include_directories(blackops1 PRIVATE
    "${CMAKE_CURRENT_SOURCE_DIR}"
    "${CMAKE_CURRENT_SOURCE_DIR}/src"
    "${BLACKOPS1_GENERATED_DIR}"
    "${IMGUI_INCLUDE_DIR}"
)

# Integrar runtime, fontes recompiladas e configurações do ReXGlue.
rexglue_setup_target(blackops1)

message(STATUS "Projeto BlackOps1Recomp configurado.")
message(STATUS "Manifesto: ${BLACKOPS1_MANIFEST}")
message(STATUS "XEX: ${BLACKOPS1_XEX}")
message(STATUS "ImGui: ${IMGUI_INCLUDE_DIR}")
message(STATUS "Saída gerada: ${BLACKOPS1_GENERATED_DIR}")
