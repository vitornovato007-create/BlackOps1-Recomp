#!/usr/bin/env python3
"""Apply Android native-window support to the temporary ReXGlue checkout."""
from pathlib import Path

root = Path("rexglue-sdk")
patches = Path("patches/android")
header_src = patches / "surface_android.h"
source_src = patches / "surface_android.cpp"
header_dst = root / "include/rex/ui/surface_android.h"
source_dst = root / "src/ui/surface_android.cpp"
cmake_path = root / "src/ui/CMakeLists.txt"
window_path = root / "src/ui/window_sdl.cpp"

for path in (header_src, source_src, cmake_path, window_path):
    if not path.is_file():
        raise SystemExit(f"::error file={path}::Arquivo necessario ausente.")

header_dst.write_text(header_src.read_text(encoding="utf-8"), encoding="utf-8")
source_dst.write_text(source_src.read_text(encoding="utf-8"), encoding="utf-8")

cmake = cmake_path.read_text(encoding="utf-8")
old_platform_sources = """if(WIN32)
    set(REXUI_PLATFORM_SOURCES
        surface_win.cpp
    )
elseif(APPLE)
    set(REXUI_PLATFORM_SOURCES
        surface_mac.cpp
    )
else()
    # Keep the existing Linux surface source.
    # Its compatibility with Android must be verified separately.
    set(REXUI_PLATFORM_SOURCES
        surface_gnulinux.cpp
    )
endif()"""
old_platform_sources_upstream = """if(WIN32)
    set(REXUI_PLATFORM_SOURCES
        surface_win.cpp
    )
elseif(APPLE)
    set(REXUI_PLATFORM_SOURCES
        surface_mac.cpp
    )
else()
    set(REXUI_PLATFORM_SOURCES
        surface_gnulinux.cpp
    )
endif()"""
new_platform_sources = """if(WIN32)
    set(REXUI_PLATFORM_SOURCES
        surface_win.cpp
    )
elseif(ANDROID)
    set(REXUI_PLATFORM_SOURCES
        surface_android.cpp
    )
elseif(APPLE)
    set(REXUI_PLATFORM_SOURCES
        surface_mac.cpp
    )
else()
    set(REXUI_PLATFORM_SOURCES
        surface_gnulinux.cpp
    )
endif()"""
if "surface_android.cpp" not in cmake:
    if old_platform_sources not in cmake:
        raise SystemExit("ERRO: selecao de fontes de plataforma do rexui mudou; patch interrompido.")
    cmake = cmake.replace(old_platform_sources, new_platform_sources, 1)

if "target_link_libraries(rexui PUBLIC android)" not in cmake:
    marker = "if(ANDROID)\n"
    dependency_pos = cmake.find("# Platform-specific dependencies")
    if dependency_pos < 0:
        raise SystemExit("ERRO: secao de dependencias de plataforma nao encontrada.")
    branch_pos = cmake.find(marker, dependency_pos)
    if branch_pos >= 0:
        insert_pos = branch_pos + len(marker)
        cmake = cmake[:insert_pos] + "    target_link_libraries(rexui PUBLIC android)\n" + cmake[insert_pos:]
    else:
        raise SystemExit("ERRO: ramo Android de dependencias nao encontrado.")
cmake_path.write_text(cmake, encoding="utf-8")

window = window_path.read_text(encoding="utf-8")
old_includes = """#elif REX_PLATFORM_MAC
#include <CoreFoundation/CoreFoundation.h>
#include <SDL3/SDL_metal.h>

#include <rex/ui/surface_mac.h>
#else
#include <X11/Xlib-xcb.h>
#include <rex/ui/surface_gnulinux.h>
#endif"""
new_includes = """#elif REX_PLATFORM_MAC
#include <CoreFoundation/CoreFoundation.h>
#include <SDL3/SDL_metal.h>

#include <rex/ui/surface_mac.h>
#elif REX_PLATFORM_ANDROID
#include <rex/ui/surface_android.h>
#else
#include <X11/Xlib-xcb.h>
#include <rex/ui/surface_gnulinux.h>
#endif"""
if "rex/ui/surface_android.h" not in window:
    if old_includes not in window:
        raise SystemExit("ERRO: bloco de includes de window_sdl.cpp mudou; patch interrompido.")
    window = window.replace(old_includes, new_includes, 1)

old_size = """#if REX_PLATFORM_MAC
  int initial_width = int(GetDesiredLogicalWidth());
  int initial_height = int(GetDesiredLogicalHeight());
#else"""
new_size = """#if REX_PLATFORM_MAC || REX_PLATFORM_ANDROID
  int initial_width = int(GetDesiredLogicalWidth());
  int initial_height = int(GetDesiredLogicalHeight());
#else"""
if "REX_PLATFORM_MAC || REX_PLATFORM_ANDROID" not in window:
    if old_size not in window:
        raise SystemExit("ERRO: bloco de tamanho inicial da janela nao encontrado.")
    window = window.replace(old_size, new_size, 1)

old_surface = """#elif REX_PLATFORM_MAC
  if (allowed_types & Surface::kTypeFlag_CAMetalLayer) {"""
new_surface = """#elif REX_PLATFORM_ANDROID
  SDL_PropertiesID props = SDL_GetWindowProperties(sdl_window_);
  if (allowed_types & Surface::kTypeFlag_AndroidNativeWindow) {
    auto* window = static_cast<ANativeWindow*>(
        SDL_GetPointerProperty(props, SDL_PROP_WINDOW_ANDROID_WINDOW_POINTER, nullptr));
    if (window) {
      return std::make_unique<AndroidNativeWindowSurface>(window, sdl_window_);
    }
  }
#elif REX_PLATFORM_MAC
  if (allowed_types & Surface::kTypeFlag_CAMetalLayer) {"""
if "SDL_PROP_WINDOW_ANDROID_WINDOW_POINTER" not in window:
    if old_surface not in window:
        raise SystemExit("ERRO: ponto de insercao CreateSurfaceImpl nao encontrado.")
    window = window.replace(old_surface, new_surface, 1)
window_path.write_text(window, encoding="utf-8")

checks = {
    "Android surface source selected in CMake": "surface_android.cpp" in cmake,
    "Android native window included": "rex/ui/surface_android.h" in window,
    "Android SDL surface property used": "SDL_PROP_WINDOW_ANDROID_WINDOW_POINTER" in window,
    "Android surface declared and implemented": header_dst.is_file() and source_dst.is_file(),
}
for name, ok in checks.items():
    print(("[OK] " if ok else "[ERRO] ") + name)
if not all(checks.values()):
    raise SystemExit("ERRO: aplicacao do backend de UI Android incompleta.")
print("Backend de UI Android aplicado ao checkout ReXGlue.")
