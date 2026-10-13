cmake_minimum_required(VERSION 3.25)

project(BlackOps1AndroidNative LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_library(
blackops1_android
SHARED
native-lib.cpp
)

target_compile_options(
blackops1_android
PRIVATE
-Wall
-Wextra
)

find_library(
android_log_lib
log
)

target_link_libraries(
blackops1_android
PRIVATE
${android_log_lib}
)
