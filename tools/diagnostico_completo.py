#!/usr/bin/env python3
"""Diagnostico estatico unificado do BlackOps1-Recomp.

Este script nao compila o projeto nem afirma que o jogo funciona.
Ele detecta arquivos ausentes, divergencias entre a ponte XISO e o CMake,
problemas de referencias aos fontes gerados e lacunas conhecidas no caminho
Android ARM64.

Uso:
  python3 tools/diagnostico_completo.py
  python3 tools/diagnostico_completo.py --strict
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return ""


def check_file(label: str, relative: str, required: bool = True) -> bool:
    path = ROOT / relative
    exists = path.is_file()
    status = "OK" if exists else ("FALTA" if required else "AVISO")
    print(f"[{status}] {label}: {relative}")
    return exists or not required


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="retorna erro se houver bloqueadores conhecidos",
    )
    args = parser.parse_args()

    print("=" * 72)
    print("DIAGNOSTICO COMPLETO — BlackOps1-Recomp")
    print("Escopo: verificacoes estaticas; nao substitui uma compilacao real.")
    print("=" * 72)

    required = [
        ("CMake principal", "CMakeLists.txt"),
        ("Manifesto ReXGlue", "blackops1_manifest.toml"),
        ("Ponto de entrada", "src/main.cpp"),
        ("Workflow Linux", ".github/workflows/build.yml"),
        ("Workflow Android", ".github/workflows/android.yml"),
        ("CMake nativo Android", "android/app/src/main/cpp/CMakeLists.txt"),
        ("Ponte XISO", "android/app/src/main/cpp/native-xiso-bridge.cpp"),
        ("Configuracao XISO", "android/app/src/main/cpp/xiso-integration.cmake"),
        ("Auditoria dos gerados", "scripts/auditar_gerados.py"),
        ("Preparacao SDK Android", "tools/android/preparar_sdk.py"),
        ("Auditoria Android", "tools/android/auditar_integracao.py"),
        ("Manifesto dos fontes gerados", "generated/sources.cmake"),
        ("CMake ReXGlue gerado", "generated/rexglue.cmake"),
    ]
    blockers: list[str] = []
    for label, relative in required:
        if not check_file(label, relative):
            blockers.append(f"Arquivo obrigatório ausente: {relative}")

    # O XEX é privado e pode não estar commitado; sua ausência é informativa
    # para o build, mas não deve impedir a auditoria do repositório.
    check_file("XEX privado para build", "game/default.xex", required=False)

    print("\n--- Integracao XISO ---")
    bridge_path = ROOT / "android/app/src/main/cpp/native-xiso-bridge.cpp"
    integration_path = ROOT / "android/app/src/main/cpp/xiso-integration.cmake"
    bridge = read_text(bridge_path)
    integration = read_text(integration_path)

    renamed = re.search(r"main\s*=\s*([A-Za-z_]\w*)", integration)
    declared = re.search(
        r'extern\s+"C"\s+int\s+([A-Za-z_]\w*)\s*\(\s*int\s+argc\s*,\s*char\s*\*\*\s*argv\s*\)',
        bridge,
    )
    called = re.search(r"\b([A-Za-z_]\w*)\s*\(\s*argc\s*,\s*argv\s*\)", bridge)
    if not renamed:
        blockers.append("CMake XISO nao define o nome alternativo de main()")
        print("[FALTA] Nome alternativo de main() nao encontrado no CMake.")
    elif not declared:
        blockers.append("Ponte XISO nao declara a funcao renomeada pelo CMake")
        print("[FALTA] Declaracao extern C da funcao XISO nao encontrada.")
    elif renamed.group(1) != declared.group(1):
        blockers.append(
            "Nome XISO divergente: CMake define "
            f"{renamed.group(1)}, ponte declara {declared.group(1)}"
        )
        print(
            f"[ERRO] CMake renomeia main para {renamed.group(1)}, "
            f"mas a ponte declara {declared.group(1)}."
        )
    elif not called or called.group(1) != renamed.group(1):
        blockers.append("Ponte XISO nao chama o simbolo definido pelo CMake")
        print("[ERRO] Chamada XISO nao corresponde ao simbolo configurado.")
    else:
        print(f"[OK] Simbolo XISO consistente: {renamed.group(1)}")

    print("\n--- Fontes gerados ---")
    generated = ROOT / "generated"
    source_manifest = generated / "sources.cmake"
    manifest_text = read_text(source_manifest)
    if not manifest_text:
        blockers.append("generated/sources.cmake vazio ou ilegível")
        print("[FALTA] Manifesto de fontes gerados vazio ou ilegivel.")
    else:
        listed = re.findall(r'["\']([^"\']+\.cpp)["\']', manifest_text)
        missing_sources: list[str] = []
        for entry in listed:
            # O manifesto usa variaveis CMake como ${CMAKE_CURRENT_LIST_DIR};
            # essas expressoes nao podem ser resolvidas por pathlib. Validamos
            # apenas caminhos literais e conferimos os globs abaixo.
            if "$" in entry:
                continue
            candidate = Path(entry)
            if not candidate.is_absolute():
                candidate = generated / candidate
            if not candidate.is_file():
                missing_sources.append(entry)
        print(f"[INFO] Referencias .cpp no manifesto: {len(listed)}")
        if "${CMAKE_CURRENT_LIST_DIR}" in manifest_text and "file(GLOB" in manifest_text:
            print("[INFO] Manifesto usa glob CMake; fontes numeradas sao verificadas no disco.")
        if missing_sources:
            blockers.append(
                f"{len(missing_sources)} fonte(s) referenciada(s) nao encontrada(s)"
            )
            for entry in missing_sources[:20]:
                print(f"[FALTA] Fonte referenciada: {entry}")
            if len(missing_sources) > 20:
                print(f"[INFO] Mais {len(missing_sources) - 20} ausentes nao listados.")
        else:
            print("[OK] Todas as referencias .cpp encontradas foram localizadas.")

    source_dir = generated / "sources"
    header_dir = generated / "headers"
    recomp_sources = sorted(source_dir.glob("blackops1_recomp.*.cpp"))
    recomp_headers = sorted(header_dir.glob("blackops1_funcs.*.h"))
    print(f"[INFO] Fontes recompilados em generated/sources/: {len(recomp_sources)}")
    print(f"[INFO] Headers numerados em generated/headers/: {len(recomp_headers)}")
    if not recomp_sources:
        print("[AVISO] Nenhuma fonte numerada encontrada em generated/sources/.")

    print("\n--- Lacunas conhecidas Android ARM64 ---")
    sdk_ui = ROOT / "rexglue-sdk/src/ui"
    android_surface_cpp = sdk_ui / "surface_android.cpp"
    android_surface_h = ROOT / "rexglue-sdk/include/rex/ui/surface_android.h"
    if android_surface_cpp.is_file() and android_surface_h.is_file():
        print("[OK] Arquivos de surface Android encontrados no checkout atual.")
    else:
        print(
            "[AVISO] Surface Android dedicada nao encontrada no checkout local. "
            "A existencia de SDL3 sozinha nao comprova que o runtime ReXGlue "
            "crie VkSurfaceKHR a partir de ANativeWindow."
        )

    native_cmake = read_text(ROOT / "android/app/src/main/cpp/CMakeLists.txt")
    for token in (
        "add_subdirectory(",
        "SDL3::SDL3",
        "rex::runtime",
        "rexgpu-xenos",
        "blackops1_recomp",
        'DEBUG_POSTFIX ""',
        "add_dependencies(blackops1_android rexgpu-xenos)",
        "libSDL3.so",
    ):
        if token in native_cmake:
            print(f"[OK] CMake Android menciona/configura {token}")
        else:
            print(f"[AVISO] CMake Android nao menciona/configura {token}")

    link_block = re.search(
        r"target_link_libraries\\(blackops1_android PRIVATE(.*?)\\)",
        native_cmake,
        re.DOTALL,
    )
    if link_block and re.search(
        r"\\brex::(?:ui|audio|input|gpu-xenos)\\b",
        link_block.group(1),
    ):
        blockers.append(
            "O alvo blackops1_android liga diretamente OBJECT libraries do SDK; "
            "isso pode duplicar o estado global do runtime ReXGlue"
        )
        print("[ERRO] OBJECT libraries do SDK estao ligadas diretamente ao app.")
    elif link_block:
        print("[OK] O app nao religa diretamente OBJECT libraries do ReXGlue.")
    else:
        print("[AVISO] Nao foi possivel localizar o bloco de link do app Android.")

    print("\n--- Resultado ---")
    if blockers:
        print(f"[ERRO] Bloqueadores estaticos encontrados: {len(blockers)}")
        for item in blockers:
            print(f" - {item}")
    else:
        print("[OK] Nenhum bloqueador estatico conhecido foi detectado.")
    print(
        "IMPORTANTE: mesmo sem bloqueadores, somente os workflows de compilacao "
        "podem confirmar se o codigo compila. Um APK compilado tambem nao prova "
        "que o jogo inicializa, renderiza ou executa corretamente."
    )
    return 1 if args.strict and blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
