#!/usr/bin/env python3
"""Preflight + minimal Android CMake adaptation for the bundled ReXGlue SDK.

This script deliberately validates every anchor before writing any file. It does
not claim to provide the missing SDL Android native-window/Vulkan host.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SDK = ROOT / "rexglue-sdk"

PATCHES = [
    (
        Path("CMakeLists.txt"),
        '''if(WIN32)\n    if(REX_TARGET_PROCESSOR MATCHES "AMD64|x86_64")''',
        '''if(ANDROID)\n    if(NOT REX_TARGET_PROCESSOR MATCHES "aarch64|ARM64|arm64")\n        message(FATAL_ERROR "Android ReXGlue target must be ARM64; got: ${REX_TARGET_PROCESSOR}")\n    endif()\n    set(REX_PLATFORM "android-arm64")\n    add_compile_definitions(REX_PLATFORM_ANDROID=1)\nelseif(WIN32)\n    if(REX_TARGET_PROCESSOR MATCHES "AMD64|x86_64")''',
        "Add Android ARM64 platform detection",
    ),
    (
        Path("src/core/CMakeLists.txt"),
        '''if(APPLE)\n    target_link_libraries(rexcore PRIVATE pthread)\nelseif(UNIX)\n    target_link_libraries(rexcore PRIVATE pthread rt dl)\nendif()''',
        '''if(ANDROID)\n    target_link_libraries(rexcore PRIVATE dl)\nelseif(APPLE)\n    target_link_libraries(rexcore PRIVATE pthread)\nelseif(UNIX)\n    target_link_libraries(rexcore PRIVATE pthread rt dl)\nendif()''',
        "Avoid linking librt on Android/Bionic",
    ),
    (
        Path("src/ui/CMakeLists.txt"),
        '''if(UNIX AND NOT APPLE)\n    find_package(PkgConfig REQUIRED)''',
        '''if(ANDROID)\n    # Android uses SDL's ANativeWindow and Android Vulkan surface path.\n    # Do not try to locate desktop X11/Wayland packages with PkgConfig.\nelseif(UNIX AND NOT APPLE)\n    find_package(PkgConfig REQUIRED)''',
        "Skip desktop X11/Wayland dependencies on Android",
    ),
]


def main() -> int:
    if not SDK.is_dir():
        print(f"ERRO: SDK não encontrado: {SDK}")
        return 1

    planned = []
    errors = []
    for rel, old, new, label in PATCHES:
        path = SDK / rel
        if not path.is_file():
            errors.append(f"Arquivo ausente: {rel.as_posix()}")
            continue
        text = path.read_text(encoding="utf-8")
        if new in text:
            print(f"JÁ APLICADO: {label}")
        elif old in text:
            planned.append((path, text, old, new, label))
        else:
            errors.append(f"Âncora não encontrada: {rel.as_posix()} ({label})")

    # Fail before modifying anything if any anchor is incompatible.
    if errors:
        print("PRÉ-VALIDAÇÃO FALHOU; nenhum arquivo foi alterado:")
        for error in errors:
            print(f" - {error}")
        return 2

    for path, text, old, new, label in planned:
        path.write_text(text.replace(old, new, 1), encoding="utf-8")
        print(f"APLICADO: {path.relative_to(ROOT).as_posix()} — {label}")

    print("\nPRÉ-PATCH CMake aplicado.")
    print("ATENÇÃO: isto ainda NÃO é uma integração Android completa.")
    print("Falta adicionar a superfície ANativeWindow ao WindowSDL, criar a")
    print("VkSurfaceKHR Android, integrar ciclo de vida/entrada/áudio e ligar")
    print("o runtime real e os fontes gerados ao target nativo do APK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
