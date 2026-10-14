# Generated-source discovery for BlackOps1-Recomp.
# Prefer the organized generated/sources tree; fall back to legacy root files.
set(GENERATED_SOURCES)
foreach(_name blackops1_init.cpp blackops1_register.cpp)
  if(EXISTS "${CMAKE_CURRENT_LIST_DIR}/${_name}")
    list(APPEND GENERATED_SOURCES "${CMAKE_CURRENT_LIST_DIR}/${_name}")
  endif()
endforeach()

file(GLOB_RECURSE _organized_recomp CONFIGURE_DEPENDS
  "${CMAKE_CURRENT_LIST_DIR}/sources/blackops1_recomp.*.cpp")
if(_organized_recomp)
  list(APPEND GENERATED_SOURCES ${_organized_recomp})
else()
  file(GLOB _legacy_recomp CONFIGURE_DEPENDS
    "${CMAKE_CURRENT_LIST_DIR}/blackops1_recomp.*.cpp")
  list(APPEND GENERATED_SOURCES ${_legacy_recomp})
endif()
list(REMOVE_DUPLICATES GENERATED_SOURCES)
list(SORT GENERATED_SOURCES)
message(STATUS "BlackOps1: ${GENERATED_SOURCES} fontes geradas")
