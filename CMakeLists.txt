cmake_minimum_required(VERSION 3.25)

project(BlackOps1Recomp LANGUAGES C CXX)

# ReXGlue exige C++23.

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Desativa recursos opcionais de profiling.

set(REXGLUE_ENABLE_TRACY OFF CACHE BOOL "" FORCE)
set(REXGLUE_ENABLE_PERF_COUNTERS OFF CACHE BOOL "" FORCE)

# Caminhos do projeto.

set(REXGLUE_SOURCE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/rexglue-sdk")
set(BLACKOPS1_MANIFEST "${CMAKE_CURRENT_SOURCE_DIR}/blackops1_manifest.toml")
set(BLACKOPS1_XEX "${CMAKE_CURRENT_SOURCE_DIR}/game/default.xex")
set(BLACKOPS1_GENERATED_DIR "${CMAKE_CURRENT_SOURCE_DIR}/generated")

# Confere se os arquivos necessários existem.

if(NOT EXISTS "${REXGLUE_SOURCE_DIR}/CMakeLists.txt")
message(FATAL_ERROR
"ReXGlue SDK não encontrado em: ${REXGLUE_SOURCE_DIR}")
endif()

if(NOT EXISTS "${BLACKOPS1_MANIFEST}")
message(FATAL_ERROR
"Manifesto não encontrado: ${BLACKOPS1_MANIFEST}")
endif()

if(NOT EXISTS "${BLACKOPS1_XEX}")
message(FATAL_ERROR
"Arquivo default.xex não encontrado: ${BLACKOPS1_XEX}")
endif()

# Compila o SDK e disponibiliza o executável rexglue.

add_subdirectory(rexglue-sdk)

if(NOT TARGET rexglue)
message(FATAL_ERROR
"O SDK foi carregado, mas o alvo executável 'rexglue' não existe.")
endif()

# Gera o código C++ recompilado a partir do manifesto.

# Execute com:

# cmake --build build --target blackops1_codegen

add_custom_target(blackops1_codegen
COMMAND
"$<TARGET_FILE:rexglue>"
codegen
"${BLACKOPS1_MANIFEST}"
WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}"
DEPENDS rexglue
COMMENT "Gerando código C++ do Black Ops 1 com ReXGlue..."
VERBATIM
)

message(STATUS "Projeto BlackOps1Recomp configurado.")
message(STATUS "Manifesto: ${BLACKOPS1_MANIFEST}")
message(STATUS "XEX: ${BLACKOPS1_XEX}")
message(STATUS "Saída esperada: ${BLACKOPS1_GENERATED_DIR}")
message(STATUS "Alvo de geração: blackops1_codegen")
