#!/usr/bin/env python3
"""Apply Android native-window support to the temporary ReXGlue checkout."""
from pathlib import Path
import re

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

# Upstream ReXGlue v0.10.0 uses a platform-source block with either no
# comments or a descriptive comment. Replace the block by its boundaries,
# rather than relying on one exact comment/whitespace version.
cmake = cmake_path.read_text(encoding="utf-8")
if "surface_android.cpp" not in cmake:
    start_marker = "# Platform-specific sources"
    start = cmake.find(start_marker)
    if start < 0:
        start_marker = "# Platform-specific sources (windowing itself is SDL3, platform-independent)"
        start = cmake.find(start_marker)
    if start < 0:
        raise SystemExit("ERRO: secao de fontes de plataforma nao encontrada no CMakeLists.txt.")
    end_match = re.search(r"(?m)^endif\(\)\s*$", cmake[start:])
    if not end_match:
        raise SystemExit("ERRO: fim da selecao de fontes de plataforma nao encontrado.")
    end = start + end_match.end()
    replacement = """# Platform-specific sources; Android uses SDL3's native window.
if(WIN32)
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
    cmake = cmake[:start] + replacement + cmake[end:]
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

# A previous Android patch may already have inserted the SDL property while
# leaving the old one-argument constructor call behind. Do not use the
# property's presence alone as proof that the constructor integration is done.
# Normalize that stale call to the two-argument API implemented by
# AndroidNativeWindowSurface(window, sdl_window).
window, stale_calls = re.subn(
    r"std::make_unique<AndroidNativeWindowSurface>\(\s*([A-Za-z_]\w*)\s*\)",
    r"std::make_unique<AndroidNativeWindowSurface>(\1, sdl_window_)",
    window,
)
surface_constructor_ok = bool(re.search(
    r"std::make_unique<AndroidNativeWindowSurface>\(\s*[A-Za-z_]\w*\s*,\s*sdl_window_\s*\)",
    window,
))
if not surface_constructor_ok:
    raise SystemExit(
        "ERRO: chamada AndroidNativeWindowSurface nao corresponde ao construtor "
        "(ANativeWindow*, SDL_Window*) esperado."
    )

window_path.write_text(window, encoding="utf-8")

checks = {
    "Android surface source selected in CMake": "surface_android.cpp" in cmake,
    "Android native window included": "rex/ui/surface_android.h" in window,
    "Android SDL surface property used": "SDL_PROP_WINDOW_ANDROID_WINDOW_POINTER" in window,
    "Android surface constructor receives SDL_Window": surface_constructor_ok,
    "Android surface declared and implemented": header_dst.is_file() and source_dst.is_file(),
}
for name, ok in checks.items():
    print(("[OK] " if ok else "[ERRO] ") + name)
if not all(checks.values()):
    raise SystemExit("ERRO: aplicacao do backend de UI Android incompleta.")
print("Backend de UI Android aplicado ao checkout ReXGlue.")
