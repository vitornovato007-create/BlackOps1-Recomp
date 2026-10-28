#!/usr/bin/env python3
"""Orquestra a preparacao reproduzivel do SDK ReXGlue para Android ARM64.

A rotina aplica os patches versionados em tools/android/steps e os scripts
existentes. Cada etapa continua separada, pode ser auditada isoladamente e
precisa validar o resultado antes de seguir.

Uso:
  python3 tools/android/preparar_sdk.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SDK = ROOT / "rexglue-sdk"

STEPS = [
    ("patch Android fixado do SDK", [sys.executable, "tools/android/apply_android_sdk_patch.py"]),
    ("diretorio de logs Android", [sys.executable, "tools/android/apply_logging_patch.py"]),
    ("backend de fibers ARM64", [sys.executable, "tools/android/apply_fiber_backend.py"]),
    ("backend de janela/surface", [sys.executable, "tools/android/apply_ui_backend.py"]),
    ("TimerQueue compatível com Android", ["bash", "tools/android/steps/apply_timer_queue.sh"]),
    ("compatibilidade C++/NDK", ["bash", "tools/android/steps/compat_cpp.sh"]),
    ("dependências UI sem X11/Wayland", ["bash", "tools/android/steps/compat_ui_dependencies.sh"]),
    ("dependências POSIX/Bionic", ["bash", "tools/android/steps/compat_core_posix.sh"]),
    ("detecção de plataforma ARM64", ["bash", "tools/android/steps/compat_platform_detection.sh"]),
    ("APIs POSIX Android", ["bash", "tools/android/steps/compat_posix_android_apis.sh"]),
    ("SDL3 compartilhado", ["bash", "tools/android/steps/verify_and_patch_sdl3.sh"]),
    ("filesystem ContentResolver", ["bash", "tools/android/steps/integrate_content_resolver.sh"]),
]


def main() -> int:
    if not (SDK / "CMakeLists.txt").is_file():
        print(f"ERRO: checkout ReXGlue ausente ou incompleto: {SDK}", file=sys.stderr)
        return 2

    required = [ROOT / relative for relative in (
        "tools/android/apply_android_sdk_patch.py",
        "tools/android/apply_logging_patch.py",
        "tools/android/apply_fiber_backend.py",
        "tools/android/apply_ui_backend.py",
        "tools/android/steps/apply_timer_queue.sh",
        "tools/android/steps/compat_cpp.sh",
        "tools/android/steps/compat_ui_dependencies.sh",
        "tools/android/steps/compat_core_posix.sh",
        "tools/android/steps/compat_platform_detection.sh",
        "tools/android/steps/compat_posix_android_apis.sh",
        "tools/android/steps/verify_and_patch_sdl3.sh",
        "tools/android/steps/integrate_content_resolver.sh",
    )]
    missing = [path.relative_to(ROOT).as_posix() for path in required if not path.is_file()]
    if missing:
        print("ERRO: faltam scripts de preparação:", file=sys.stderr)
        for path in missing:
            print(f" - {path}", file=sys.stderr)
        return 2

    print("=" * 72)
    print("PREPARAÇÃO DO SDK RE XGLUE — ANDROID ARM64")
    print("Base: checkout fixado do ReXGlue v0.10.0 + patch Android fixado.")
    print("As alterações específicas do projeto estão versionadas em tools/android/steps.")
    print("=" * 72)

    for label, command in STEPS:
        print(f"\n>>> {label}", flush=True)
        result = subprocess.run(command, cwd=ROOT, check=False)
        if result.returncode:
            print(
                f"ERRO: etapa '{label}' falhou com código {result.returncode}; "
                "as etapas seguintes não foram executadas.",
                file=sys.stderr,
            )
            return result.returncode

    print("\nOK: todas as etapas de preparação do SDK terminaram.")
    print("Isso não comprova que o APK compila nem que o jogo inicia no dispositivo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
