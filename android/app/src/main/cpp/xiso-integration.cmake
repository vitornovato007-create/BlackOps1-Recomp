```cmake
# Integracao do extract-xiso no alvo Android existente.
# Este arquivo deve ser incluido pelo CMakeLists.txt principal
# depois de add_library(blackops1_android ...) e antes de
# target_link_libraries(...).

set(EXTRACT_XISO_SOURCE
    "${BLACKOPS1_ROOT}/thirdparty/extract-xiso/extract-xiso.c"
)

set(XISO_BRIDGE_SOURCE
    "${CMAKE_CURRENT_LIST_DIR}/native-xiso-bridge.cpp"
)

if(NOT EXISTS "${EXTRACT_XISO_SOURCE}")
    message(FATAL_ERROR
        "Fonte extract-xiso nao encontrado: ${EXTRACT_XISO_SOURCE}"
    )
endif()

if(NOT EXISTS "${XISO_BRIDGE_SOURCE}")
    message(FATAL_ERROR
        "Ponte JNI nao encontrada: ${XISO_BRIDGE_SOURCE}"
    )
endif()

# Renomeia main() do utilitario para evitar conflito com o aplicativo.
set_source_files_properties(
    "${EXTRACT_XISO_SOURCE}"
    PROPERTIES
    COMPILE_DEFINITIONS "main=extract_xiso_cli_main;__LINUX__"
)

target_sources(blackops1_android PRIVATE
    "${EXTRACT_XISO_SOURCE}"
    "${XISO_BRIDGE_SOURCE}"
)
