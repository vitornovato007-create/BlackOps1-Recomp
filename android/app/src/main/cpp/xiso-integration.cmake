# Integração mínima do extract-xiso no alvo Android existente.
# Inserir este bloco DEPOIS de add_library(blackops1_android ...)
# e ANTES de target_link_libraries(...).
#
# O fonte upstream deve estar em:
# ${BLACKOPS1_ROOT}/third_party/extract-xiso/extract-xiso.c

set(EXTRACT_XISO_SOURCE
    "${BLACKOPS1_ROOT}/third_party/extract-xiso/extract-xiso.c")
if(NOT EXISTS "${EXTRACT_XISO_SOURCE}")
  message(FATAL_ERROR
    "Falta ${EXTRACT_XISO_SOURCE}. Adicione o fonte oficial XboxDev/extract-xiso.")
endif()

# Renomeia main() do utilitário para que possa ser chamado pelo bridge JNI.
set_source_files_properties("${EXTRACT_XISO_SOURCE}" PROPERTIES
  COMPILE_DEFINITIONS "main=extract_xiso_cli_main;__LINUX__")

target_sources(blackops1_android PRIVATE
  "${EXTRACT_XISO_SOURCE}"
  "${CMAKE_CURRENT_LIST_DIR}/native-xiso-bridge.cpp")
