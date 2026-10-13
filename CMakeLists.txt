cmake_minimum_required(VERSION 3.25)

project(BlackOps1Recomp LANGUAGES C CXX)

# ============================================================
# CONFIGURAÇÃO DO C++
# ============================================================

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# ============================================================
# OPÇÕES DO RE XGLUE
# ============================================================

set(REXGLUE_ENABLE_TRACY OFF CACHE BOOL "" FORCE)
set(REXGLUE_ENABLE_PERF_COUNTERS OFF CACHE BOOL "" FORCE)

# ============================================================
# CAMINHOS DO PROJETO
# ============================================================

set(REXGLUE_SOURCE_DIR
    "${CMAKE_CURRENT_SOURCE_DIR}/rexglue-sdk"
)

set(BLACKOPS1_MANIFEST
    "${CMAKE_CURRENT_SOURCE_DIR}/blackops1_manifest.toml"
)

set(BLACKOPS1_XEX
    "${CMAKE_CURRENT_SOURCE_DIR}/game/default.xex"
)

set(BLACKOPS1_GENERATED_DIR
    "${CMAKE_CURRENT_SOURCE_DIR}/generated"
)

set(IMGUI_INCLUDE_DIR
    "${REXGLUE_SOURCE_DIR}/thirdparty/imgui"
)

# ============================================================
# VERIFICAÇÃO DOS ARQUIVOS NECESSÁRIOS
# ============================================================

if(NOT EXISTS "${REXGLUE_SOURCE_DIR}/CMakeLists.txt")
    message(FATAL_ERROR
        "ReXGlue SDK nao encontrado: ${REXGLUE_SOURCE_DIR}"
    )
endif()

if(NOT EXISTS "${BLACKOPS1_MANIFEST}")
    message(FATAL_ERROR
        "Manifesto nao encontrado: ${BLACKOPS1_MANIFEST}"
    )
endif()

if(NOT EXISTS "${BLACKOPS1_XEX}")
    message(FATAL_ERROR
        "Arquivo default.xex nao encontrado: ${BLACKOPS1_XEX}"
    )
endif()

if(NOT EXISTS "${BLACKOPS1_GENERATED_DIR}/rexglue.cmake")
    message(FATAL_ERROR
        "Arquivo generated/rexglue.cmake nao encontrado."
    )
endif()

if(NOT EXISTS "${IMGUI_INCLUDE_DIR}/imgui.h")
    message(FATAL_ERROR
        "imgui.h nao encontrado em: ${IMGUI_INCLUDE_DIR}"
    )
endif()

# ============================================================
# CORREÇÃO: INFORMAR ONDE ESTÁ O SDK
#
# IMPORTANTE:
# Não usamos add_subdirectory(rexglue-sdk) aqui.
# O arquivo generated/rexglue.cmake já carrega o SDK.
# Isso evita adicionar o mesmo SDK duas vezes.
# ============================================================

set(REXSDK_DIR
    "${REXGLUE_SOURCE_DIR}"
    CACHE PATH "Caminho do codigo-fonte do ReXGlue SDK"
    FORCE
)

# ============================================================
# INTEGRAÇÃO GERADA PELO RE XGLUE
# ============================================================

include(
    "${BLACKOPS1_GENERATED_DIR}/rexglue.cmake"
)

# ============================================================
# VERIFICAR SE O SDK FOI CARREGADO
# ============================================================

if(NOT TARGET rexglue)
    message(FATAL_ERROR
        "O SDK foi carregado, mas o alvo rexglue nao existe."
    )
endif()

# ============================================================
# EXECUTÁVEL DO PROJETO
# ============================================================

add_executable(blackops1
    src/main.cpp
)

# ============================================================
# DIRETÓRIOS DE INCLUSÃO
# ============================================================

target_include_directories(blackops1 PRIVATE
    "${CMAKE_CURRENT_SOURCE_DIR}"
    "${CMAKE_CURRENT_SOURCE_DIR}/src"
    "${BLACKOPS1_GENERATED_DIR}"
    "${IMGUI_INCLUDE_DIR}"
)

# ============================================================
# CONFIGURAÇÃO DO ALVO PELO RE XGLUE
# ============================================================

rexglue_setup_target(blackops1)

# ============================================================
# INFORMAÇÕES DE DIAGNÓSTICO
# ============================================================

message(STATUS "======================================")
message(STATUS "Projeto BlackOps1Recomp configurado")
message(STATUS "SDK: ${REXGLUE_SOURCE_DIR}")
message(STATUS "Manifesto: ${BLACKOPS1_MANIFEST}")
message(STATUS "XEX: ${BLACKOPS1_XEX}")
message(STATUS "ImGui: ${IMGUI_INCLUDE_DIR}")
message(STATUS "Gerados: ${BLACKOPS1_GENERATED_DIR}")
message(STATUS "======================================")
