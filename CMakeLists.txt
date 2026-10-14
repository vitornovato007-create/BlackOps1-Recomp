cmake_minimum_required(VERSION 3.25)

project(BlackOps1Recomp LANGUAGES C CXX)

# ============================================================
# CONFIGURACAO GERAL
# ============================================================

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

set(REXGLUE_ENABLE_TRACY OFF CACHE BOOL "" FORCE)
set(REXGLUE_ENABLE_PERF_COUNTERS OFF CACHE BOOL "" FORCE)

# ============================================================
# CAMINHOS DO PROJETO
# ============================================================

set(BLACKOPS1_ROOT
    "${CMAKE_CURRENT_SOURCE_DIR}"
)

set(REXGLUE_SOURCE_DIR
    "${BLACKOPS1_ROOT}/rexglue-sdk"
)

set(BLACKOPS1_MANIFEST
    "${BLACKOPS1_ROOT}/blackops1_manifest.toml"
)

set(BLACKOPS1_XEX
    "${BLACKOPS1_ROOT}/game/default.xex"
)

set(BLACKOPS1_GENERATED_DIR
    "${BLACKOPS1_ROOT}/generated"
)

set(BLACKOPS1_SOURCE
    "${BLACKOPS1_ROOT}/src/main.cpp"
)

set(IMGUI_INCLUDE_DIR
    "${REXGLUE_SOURCE_DIR}/thirdparty/imgui"
)

# ============================================================
# VALIDACAO DOS ARQUIVOS NECESSARIOS
# ============================================================

if(NOT EXISTS "${BLACKOPS1_MANIFEST}")
    message(FATAL_ERROR
        "Manifesto nao encontrado: ${BLACKOPS1_MANIFEST}"
    )
endif()

if(NOT EXISTS "${BLACKOPS1_XEX}")
    message(FATAL_ERROR
        "default.xex nao encontrado: ${BLACKOPS1_XEX}"
    )
endif()

if(NOT EXISTS "${BLACKOPS1_SOURCE}")
    message(FATAL_ERROR
        "Arquivo principal nao encontrado: ${BLACKOPS1_SOURCE}"
    )
endif()

if(NOT EXISTS "${REXGLUE_SOURCE_DIR}/CMakeLists.txt")
    message(FATAL_ERROR
        "SDK ReXGlue nao encontrado em: ${REXGLUE_SOURCE_DIR}"
    )
endif()

if(NOT EXISTS "${BLACKOPS1_GENERATED_DIR}/rexglue.cmake")
    message(FATAL_ERROR
        "Arquivo generated/rexglue.cmake nao encontrado."
    )
endif()

# ============================================================
# CONFIGURACAO DO SDK RE XGLUE
# ============================================================

set(REXSDK_DIR
    "${REXGLUE_SOURCE_DIR}"
    CACHE PATH "Diretorio do SDK ReXGlue"
    FORCE
)

# O arquivo gerado configura o SDK, as regras de codegen
# e as funcoes de integracao do projeto.
include(
    "${BLACKOPS1_GENERATED_DIR}/rexglue.cmake"
)

# ============================================================
# EXECUTAVEL PRINCIPAL
# ============================================================

add_executable(blackops1
    "${BLACKOPS1_SOURCE}"
)

target_include_directories(blackops1 PRIVATE
    "${BLACKOPS1_ROOT}"
    "${BLACKOPS1_ROOT}/src"
    "${BLACKOPS1_GENERATED_DIR}"
    "${BLACKOPS1_GENERATED_DIR}/headers"
    "${IMGUI_INCLUDE_DIR}"
)

# ============================================================
# INTEGRACAO COM O RE XGLUE
# ============================================================

# Esta funcao e definida por generated/rexglue.cmake.
# Ela conecta o executavel ao runtime e ao codigo recompilado,
# alem de associar a etapa automatica de geracao.
rexglue_setup_target(blackops1)

# ============================================================
# INFORMACOES DE CONFIGURACAO
# ============================================================

message(STATUS "==========================================")
message(STATUS " BlackOps1-Recomp")
message(STATUS "==========================================")
message(STATUS "Raiz:       ${BLACKOPS1_ROOT}")
message(STATUS "Manifesto:  ${BLACKOPS1_MANIFEST}")
message(STATUS "XEX:        ${BLACKOPS1_XEX}")
message(STATUS "Gerados:    ${BLACKOPS1_GENERATED_DIR}")
message(STATUS "SDK:        ${REXGLUE_SOURCE_DIR}")
message(STATUS "C++:        ${CMAKE_CXX_STANDARD}")
message(STATUS "==========================================")
