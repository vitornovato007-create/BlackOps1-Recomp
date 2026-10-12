cmake_minimum_required(VERSION 3.25)

project(blackops1 LANGUAGES C CXX)

# Requisitos do projeto.
set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Desativar recursos opcionais de profiling.
set(REXGLUE_ENABLE_TRACY OFF CACHE BOOL "" FORCE)
set(REXGLUE_ENABLE_PERF_COUNTERS OFF CACHE BOOL "" FORCE)

# Caminhos do projeto.
set(BLACKOPS1_MANIFEST
    "${CMAKE_CURRENT_SOURCE_DIR}/blackops1_manifest.toml")

set(BLACKOPS1_XEX
    "${CMAKE_CURRENT_SOURCE_DIR}/game/default.xex")

set(BLACKOPS1_GENERATED_DIR
    "${CMAKE_CURRENT_SOURCE_DIR}/generated")

set(REXSDK_DIR
    "${CMAKE_CURRENT_SOURCE_DIR}/rexglue-sdk"
    CACHE PATH "Caminho local do SDK ReXGlue")

# Verificar arquivos e pastas necessários.
if(NOT EXISTS "${REXSDK_DIR}/CMakeLists.txt")
    message(FATAL_ERROR
        "ReXGlue SDK nao encontrado: ${REXSDK_DIR}")
endif()

if(NOT EXISTS "${BLACKOPS1_MANIFEST}")
    message(FATAL_ERROR
        "Manifesto nao encontrado: ${BLACKOPS1_MANIFEST}")
endif()

if(NOT EXISTS "${BLACKOPS1_XEX}")
    message(FATAL_ERROR
        "default.xex nao encontrado: ${BLACKOPS1_XEX}")
endif()

if(NOT EXISTS "${BLACKOPS1_GENERATED_DIR}/blackops1_init.h")
    message(STATUS
        "Cabecalhos gerados ainda nao encontrados; "
        "o ReXGlue tentara executar o codegen durante o build.")
endif()

# Carregar a configuração oficial gerada pelo ReXGlue.
# Ela carrega o SDK, configura o codegen e disponibiliza
# rexglue_setup_target() e rexglue_apply_recomp_settings().
include("${BLACKOPS1_GENERATED_DIR}/rexglue.cmake")

# Criar o executável principal.
# IMPORTANTE: src/main.cpp precisa definir a entrada da aplicação
# ReXGlue usando REX_DEFINE_APP.
add_executable(blackops1
    src/main.cpp
)

# Integrar o executável ao runtime e ao código recompilado.
# Esta função também configura as dependências de codegen.
rexglue_setup_target(blackops1)

message(STATUS "Projeto: blackops1")
message(STATUS "Manifesto: ${BLACKOPS1_MANIFEST}")
message(STATUS "XEX: ${BLACKOPS1_XEX}")
message(STATUS "Codigo gerado: ${BLACKOPS1_GENERATED_DIR}")
message(STATUS "Alvo executavel: blackops1")
