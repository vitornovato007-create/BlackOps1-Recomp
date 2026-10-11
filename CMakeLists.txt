cmake_minimum_required(VERSION 3.22)
project(BlackOps1Recomp CXX)

# Força rigorosamente o C++23 globalmente
set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Adiciona o SDK do ReXGlue que baixamos
add_subdirectory(rexglue-sdk)

# Adiciona a pasta do aplicativo/jogo (onde ficarão os códigos do Black Ops 1)
add_subdirectory(app)
