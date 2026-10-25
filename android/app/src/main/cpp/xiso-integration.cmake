# Integra o extract-xiso em uma biblioteca JNI isolada.
# A extração da ISO não deve carregar SDL3/ReXGlue nem inicializar o runtime do jogo.

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

add_library(blackops1_xiso SHARED
    "${EXTRACT_XISO_SOURCE}"
    "${XISO_BRIDGE_SOURCE}"
)

target_compile_options(blackops1_xiso PRIVATE
    -Wall
    -Wextra
    -fno-strict-aliasing
)

target_link_libraries(blackops1_xiso PRIVATE
    ${android_log_lib}
)

set_target_properties(blackops1_xiso PROPERTIES
    OUTPUT_NAME "blackops1_xiso"
    C_VISIBILITY_PRESET default
    CXX_VISIBILITY_PRESET default
    VISIBILITY_INLINES_HIDDEN OFF
)
