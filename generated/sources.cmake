# Gerado/atualizado pelo projeto: aceita fontes na raiz generated/
# e também em generated/sources/. Arquivos ausentes não são inventados.
set(GENERATED_SOURCES)

# Arquivos de bootstrap que normalmente ficam na raiz.
foreach(_name blackops1_init.cpp blackops1_register.cpp)
    if(EXISTS "${CMAKE_CURRENT_LIST_DIR}/${_name}")
        list(APPEND GENERATED_SOURCES "${CMAKE_CURRENT_LIST_DIR}/${_name}")
    endif()
endforeach()

# Compatibilidade com a estrutura antiga: blackops1_recomp.N.cpp na raiz.
file(GLOB _legacy_recomp CONFIGURE_DEPENDS
    "${CMAKE_CURRENT_LIST_DIR}/blackops1_recomp.*.cpp"
)
list(APPEND GENERATED_SOURCES ${_legacy_recomp})

# Nova estrutura organizada: todas as fontes .cpp em generated/sources/
file(GLOB_RECURSE _organized_sources CONFIGURE_DEPENDS
    "${CMAKE_CURRENT_LIST_DIR}/sources/*.cpp"
)
list(APPEND GENERATED_SOURCES ${_organized_sources})

list(REMOVE_DUPLICATES GENERATED_SOURCES)
list(SORT GENERATED_SOURCES)

message(STATUS "BlackOps1: ${GENERATED_SOURCES} fontes C++ geradas encontradas")
