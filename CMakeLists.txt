cmake_minimum_required(VERSION 3.22)
project(BlackOps1Recomp CXX)

# Força rigorosamente o C++23 globalmente para evitar incompatibilidades
set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Opcional: Desativa subprojetos pesados do SDK que não usamos agora para acelerar o build
set(REXGLUE_ENABLE_TRACY OFF CACHE BOOL "" FORCE)
set(REXGLUE_ENABLE_PERF_COUNTERS OFF CACHE BOOL "" FORCE)

# Adiciona o SDK do ReXGlue que está na pasta rexglue-sdk/
add_subdirectory(rexglue-sdk)

# Integrando o projeto do Call of Duty: Black Ops 1 através do manifesto na raiz
if(COMMAND rexglue_add_project)
    rexglue_add_project(blackops1
        MANIFEST "${CMAKE_CURRENT_SOURCE_DIR}/blackops1_manifest.toml"
    )
else()
    message(STATUS "ReXGlue SDK carregado. Aguardando registro do projeto...")
endif()
