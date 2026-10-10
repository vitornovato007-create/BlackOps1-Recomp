cmake_minimum_required(VERSION 3.22)

project(BlackOps1Recomp
    VERSION 0.1.0
    LANGUAGES C CXX
)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_library(blackops1_stub STATIC
    src/main.cpp
)

target_include_directories(blackops1_stub
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/src
)

message(STATUS "BlackOps1-Recomp v0.1")
message(STATUS "This target is only a native scaffold.")
message(STATUS "ReXGlue generated sources are added after successful codegen.")
