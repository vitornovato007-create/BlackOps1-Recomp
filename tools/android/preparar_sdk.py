#!/usr/bin/env python3
"""Apply/verify the BlackOps1 Android ARM64 adaptation in the bundled ReXGlue SDK."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SDK = ROOT / "rexglue-sdk"


def edit(rel: str, old: str, new: str) -> None:
    path = SDK / rel
    text = path.read_text(encoding="utf-8")
    if new in text:
        print(f"OK (já aplicado): {rel}")
        return
    if old not in text:
        raise RuntimeError(f"Âncora não encontrada em {rel}; SDK diferente do esperado. Não alterado.")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"APLICADO: {rel}")


def main() -> int:
    if not (SDK / "CMakeLists.txt").is_file():
        print("SDK ausente", file=sys.stderr)
        return 2

    edit(
        "CMakeLists.txt",
        'elseif(UNIX AND NOT APPLE)\n    if(REX_TARGET_PROCESSOR MATCHES "AMD64|x86_64")',
        'elseif(ANDROID)\n    if(REX_TARGET_PROCESSOR MATCHES "aarch64|ARM64|arm64")\n'
        '        set(REX_PLATFORM "android-arm64")\n    else()\n'
        '        message(FATAL_ERROR "ReXGlue Android port currently requires ARM64; got ${REX_TARGET_PROCESSOR}")\n'
        '    endif()\n    add_compile_definitions(REX_PLATFORM_ANDROID=1 REX_PLATFORM_LINUX=1)\n'
        'elseif(UNIX AND NOT APPLE)\n    if(REX_TARGET_PROCESSOR MATCHES "AMD64|x86_64")',
    )
    edit(
        "src/core/CMakeLists.txt",
        'elseif(UNIX)\n    target_link_libraries(rexcore PRIVATE pthread rt dl)\nendif()',
        'elseif(ANDROID)\n    target_link_libraries(rexcore PRIVATE pthread dl)\n'
        'elseif(UNIX)\n    target_link_libraries(rexcore PRIVATE pthread rt dl)\nendif()',
    )
    edit(
        "src/ui/CMakeLists.txt",
        'elseif(WIN32)\n    set(REXUI_PLATFORM_SOURCES',
        'if(ANDROID)\n    set(REXUI_PLATFORM_SOURCES\n        surface_android.cpp\n    )\n'
        'elseif(WIN32)\n    set(REXUI_PLATFORM_SOURCES',
    )
    edit(
        "src/ui/CMakeLists.txt",
        'if(UNIX AND NOT APPLE)\n    find_package(PkgConfig REQUIRED)',
        'if(UNIX AND NOT APPLE AND NOT ANDROID)\n    find_package(PkgConfig REQUIRED)',
    )

    required = [
        SDK / "include/rex/ui/surface_android.h",
        SDK / "src/ui/surface_android.cpp",
        SDK / "src/ui/window_sdl.cpp",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError("Arquivos de superfície Android ausentes: " + ", ".join(missing))
    ui_source = (SDK / "src/ui/window_sdl.cpp").read_text(encoding="utf-8")
    if "SDL_PROP_WINDOW_ANDROID_WINDOW_POINTER" not in ui_source:
        raise RuntimeError("window_sdl.cpp não implementa a superfície ANativeWindow")

    sdk_cmake = (SDK / "CMakeLists.txt").read_text(encoding="utf-8")
    if 'if(NOT ANDROID)\n    set(CMAKE_RUNTIME_OUTPUT_DIRECTORY' not in sdk_cmake:
        print("AVISO: confirme que as bibliotecas Android não são redirecionadas para rexglue-sdk/out/.")
    print("Adaptação Android ARM64 aplicada/verificada. Isso não substitui o teste de compilação e execução.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        raise SystemExit(1)
