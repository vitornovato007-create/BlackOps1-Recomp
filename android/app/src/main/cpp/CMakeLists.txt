cmake_minimum_required(VERSION 3.25)

project(BlackOps1AndroidNative LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Biblioteca nativa utilizada pelo aplicativo Android.
add_library(
    blackops1_android
    SHARED
    native-lib.cpp
)

# Avisos de compilação.
target_compile_options(
    blackops1_android
    PRIVATE
    -Wall
    -Wextra
)

# Diretórios do projeto principal.
set(BLACKOPS1_ROOT
    "${CMAKE_CURRENT_SOURCE_DIR}/../../../../.."
)

set(BLACKOPS1_GENERATED_DIR
    "${BLACKOPS1_ROOT}/generated"
)

# Cabeçalhos gerados: adiciona o diretório somente
# quando ele existir.
if(EXISTS "${BLACKOPS1_GENERATED_DIR}")
    target_include_directories(
        blackops1_android
        PRIVATE
        "${BLACKOPS1_GENERATED_DIR}"
    )
endif()

# Bibliotecas Android.
find_library(
    android_log_lib
    log
)

find_library(
    android_lib
    android
)

target_link_libraries(
    blackops1_android
    PRIVATE
    ${android_log_lib}
    ${android_lib}
)
