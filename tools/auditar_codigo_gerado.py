#!/usr/bin/env python3
"""Auditoria estrutural do C++ gerado pelo ReXGlue para Black Ops 1.

Nao compila nem executa o jogo. Confere integridade dos artefatos, referencias
entre arquivos, consistencia dos enderecos registrados e sinais de risco para
a futura integracao Android.

Uso:
  python3 tools/auditar_codigo_gerado.py
  python3 tools/auditar_codigo_gerado.py --strict
  python3 tools/auditar_codigo_gerado.py --json build-diagnostic/codigo-gerado.json
  python3 tools/auditar_codigo_gerado.py --markdown build-diagnostic/codigo-gerado.md
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / "generated"
SOURCE_DIRS = (GEN / "sources", GEN)
HEADER_DIRS = (GEN / "headers", GEN)


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return ""


def numbered_files(directory: Path, pattern: str) -> dict[int, Path]:
    found: dict[int, Path] = {}
    if not directory.exists():
        return found
    for path in directory.glob(pattern):
        match = re.fullmatch(r"blackops1_recomp\.(\d+)\.(?:cpp|h)", path.name)
        if match:
            found[int(match.group(1))] = path
    return found


def unique_paths(paths: list[Path]) -> list[Path]:
    return sorted(set(p.resolve() for p in paths if p.is_file()))


def locate_include(name: str, source: Path) -> bool:
    candidates = [source.parent / name]
    candidates.extend(directory / name for directory in HEADER_DIRS)
    candidates.extend(directory / name for directory in SOURCE_DIRS)
    candidates.append(ROOT / name)
    return any(path.is_file() for path in candidates)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true",
                        help="retorna erro tambem para avisos e riscos heurísticos")
    parser.add_argument("--json", dest="json_path", type=Path,
                        help="grava relatorio JSON")
    parser.add_argument("--markdown", dest="markdown_path", type=Path,
                        help="grava relatorio Markdown")
    args = parser.parse_args()

    cpp = unique_paths(
        [p for directory in SOURCE_DIRS if directory.exists()
         for p in directory.rglob("*.cpp")]
    )
    headers = unique_paths(
        [p for directory in HEADER_DIRS if directory.exists()
         for pattern in ("*.h", "*.hpp")
         for p in directory.rglob(pattern)]
    )
    numbered_cpp: dict[int, Path] = {}
    numbered_headers: dict[int, Path] = {}
    for directory in SOURCE_DIRS:
        numbered_cpp.update(numbered_files(directory, "blackops1_recomp.*.cpp"))
    for directory in HEADER_DIRS:
        numbered_headers.update(numbered_files(directory, "blackops1_funcs.*.h"))

    issues: list[dict[str, str]] = []

    def issue(level: str, code: str, message: str) -> None:
        issues.append({"level": level, "code": code, "message": message})

    for required in (
        GEN / "blackops1_init.cpp",
        GEN / "blackops1_register.cpp",
        GEN / "sources.cmake",
        GEN / "rexglue.cmake",
        GEN / "headers" / "blackops1_init.h",
        GEN / "headers" / "blackops1_pch.h",
        GEN / "headers" / "blackops1_funcs.h",
    ):
        if not required.is_file():
            issue("ERROR", "REQUIRED_FILE_MISSING",
                  f"Arquivo obrigatório ausente: {required.relative_to(ROOT)}")

    if not cpp:
        issue("ERROR", "NO_GENERATED_CPP", "Nenhum arquivo C++ gerado foi encontrado.")
    if not numbered_cpp:
        issue("ERROR", "NO_NUMBERED_CPP",
              "Nenhum blackops1_recomp.N.cpp foi encontrado em generated/ ou generated/sources/.")

    cpp_indices = set(numbered_cpp)
    header_indices = set(numbered_headers)
    if cpp_indices != header_indices:
        issue("ERROR", "SOURCE_HEADER_INDEX_MISMATCH",
              "Índices C++/cabeçalhos divergentes; sem C++=" +
              ",".join(map(str, sorted(cpp_indices - header_indices))) +
              "; sem cabeçalho=" +
              ",".join(map(str, sorted(header_indices - cpp_indices))))

    if cpp_indices:
        expected = set(range(min(cpp_indices), max(cpp_indices) + 1))
        missing = sorted(expected - cpp_indices)
        if missing:
            issue("WARNING", "SOURCE_INDEX_GAPS",
                  "Lacunas na sequência de fontes: " + ", ".join(map(str, missing)))

    empty_files = [p for p in cpp + headers if p.stat().st_size == 0]
    if empty_files:
        issue("ERROR", "EMPTY_GENERATED_FILES",
              "Arquivos gerados vazios: " +
              ", ".join(p.relative_to(ROOT).as_posix() for p in empty_files[:20]))

    bad_encoding = []
    missing_newline = []
    for path in cpp + headers:
        data = path.read_bytes()
        if b"\x00" in data:
            bad_encoding.append(path)
        if data and not data.endswith(b"\n"):
            missing_newline.append(path)
    if bad_encoding:
        issue("ERROR", "BINARY_IN_SOURCE",
              "Arquivo C++/header contém byte NUL: " +
              ", ".join(p.relative_to(ROOT).as_posix() for p in bad_encoding[:20]))
    if missing_newline:
        issue("WARNING", "MISSING_FINAL_NEWLINE",
              f"{len(missing_newline)} arquivo(s) não terminam com newline.")

    # O registro e o mapa PPC precisam concordar nos endereços e nos símbolos.
    register_text = read(GEN / "blackops1_register.cpp")
    init_text = read(GEN / "blackops1_init.cpp")
    register_rows = re.findall(
        r"SetFunction\s*\(\s*(0x[0-9A-Fa-f]+)\s*,\s*([A-Za-z_]\w*)\s*\)",
        register_text,
    )
    mapping_rows = re.findall(
        r"\{\s*(0x[0-9A-Fa-f]+)\s*,\s*([A-Za-z_]\w*)\s*\}",
        init_text,
    )
    reg_addresses = [int(address, 16) for address, _ in register_rows]
    map_addresses = [int(address, 16) for address, _ in mapping_rows]
    duplicates = sorted(address for address, count in Counter(reg_addresses).items() if count > 1)
    if duplicates:
        issue("ERROR", "DUPLICATE_REGISTERED_ADDRESS",
              "Endereços duplicados no registro: " +
              ", ".join(f"0x{x:08X}" for x in duplicates[:30]))
    if not register_rows:
        issue("ERROR", "NO_FUNCTION_REGISTRATION",
              "Não foi possível extrair SetFunction() de blackops1_register.cpp.")
    if not mapping_rows:
        issue("ERROR", "NO_PPC_MAPPINGS",
              "Não foi possível extrair PPCFuncMappings de blackops1_init.cpp.")
    if set(reg_addresses) != set(map_addresses):
        only_register = sorted(set(reg_addresses) - set(map_addresses))
        only_map = sorted(set(map_addresses) - set(reg_addresses))
        issue("ERROR", "REGISTRATION_MAPPING_MISMATCH",
              "Endereços divergentes: somente registro=" +
              ", ".join(f"0x{x:08X}" for x in only_register[:20]) +
              "; somente mapa=" +
              ", ".join(f"0x{x:08X}" for x in only_map[:20]))

    function_definitions: set[str] = set()
    for path in cpp:
        text = read(path)
        function_definitions.update(re.findall(r"DEFINE_REX_FUNC\s*\(\s*([A-Za-z_]\w*)\s*\)", text))
    registered_functions = {name for _, name in register_rows}
    mapped_functions = {name for _, name in mapping_rows}
    if function_definitions and registered_functions - function_definitions:
        missing = sorted(registered_functions - function_definitions)
        issue("ERROR", "REGISTERED_FUNCTION_WITHOUT_DEFINITION",
              "Funções registradas sem DEFINE_REX_FUNC encontrado: " +
              ", ".join(missing[:30]))
    if function_definitions and mapped_functions - function_definitions:
        missing = sorted(mapped_functions - function_definitions)
        issue("ERROR", "MAPPED_FUNCTION_WITHOUT_DEFINITION",
              "Funções no mapa sem DEFINE_REX_FUNC encontrado: " +
              ", ".join(missing[:30]))
    if function_definitions and function_definitions - registered_functions:
        extra = sorted(function_definitions - registered_functions)
        issue("WARNING", "UNREGISTERED_GENERATED_FUNCTION",
              "Funções definidas não encontradas no registro: " +
              ", ".join(extra[:30]))

    # Verifica includes locais sem tratar includes de sistema como erros.
    missing_includes: list[str] = []
    include_re = re.compile(r'^\s*#\s*include\s*"([^"]+)"', re.MULTILINE)
    for path in cpp + headers:
        for include in include_re.findall(read(path)):
            if "/" in include or include.startswith("blackops1_"):
                if not locate_include(include, path):
                    missing_includes.append(
                        f"{path.relative_to(ROOT).as_posix()}: {include}"
                    )
    if missing_includes:
        issue("ERROR", "LOCAL_INCLUDE_MISSING",
              "Includes locais não encontrados: " + "; ".join(missing_includes[:30]))

    # Heurísticas para orientar a análise de portabilidade. Não são falhas por si.
    platform_patterns = {
        "Windows API": r"\b(?:CreateFileW|VirtualAlloc|VirtualProtect|GetModuleHandleW|__declspec)\b|#\s*include\s*[<\"]windows\.h[>\"]",
        "Linux/Unix APIs": r"#\s*include\s*[<\"](?:sys/mman\.h|unistd\.h|pthread\.h)[>\"]|\b(?:mmap|munmap|dlopen|pthread_create)\s*\(",
    }
    platform_hits = []
    for label, pattern in platform_patterns.items():
        hit_files = [p for p in cpp if re.search(pattern, read(p))]
        if hit_files:
            platform_hits.append(f"{label}: {len(hit_files)} fonte(s)")
    if platform_hits:
        issue("INFO", "PLATFORM_API_HEURISTIC",
              "APIs de plataforma detectadas (precisam de contexto, não são falhas automáticas): " +
              "; ".join(platform_hits))

    errors = sum(item["level"] == "ERROR" for item in issues)
    warnings = sum(item["level"] == "WARNING" for item in issues)
    summary = {
        "project": "BlackOps1-Recomp",
        "scope": "static generated-code audit; no compilation or runtime test",
        "generated_cpp_files": len(cpp),
        "numbered_recomp_sources": len(numbered_cpp),
        "generated_header_files": len(headers),
        "numbered_function_headers": len(numbered_headers),
        "registered_functions": len(register_rows),
        "ppc_function_mappings": len(mapping_rows),
        "unique_function_definitions": len(function_definitions),
        "errors": errors,
        "warnings": warnings,
        "issues": issues,
    }

    print("=" * 72)
    print("AUDITORIA DO CÓDIGO C++ GERADO — BlackOps1-Recomp")
    print("Escopo estático; não compila nem comprova execução do jogo.")
    print("=" * 72)
    for key in (
        "generated_cpp_files", "numbered_recomp_sources", "generated_header_files",
        "numbered_function_headers", "registered_functions", "ppc_function_mappings",
        "unique_function_definitions",
    ):
        print(f"{key}: {summary[key]}")
    for item in issues:
        print(f"[{item['level']}] {item['code']}: {item['message']}")
    if not issues:
        print("[OK] Nenhuma inconsistência estrutural detectada.")
    print(f"Resultado: {errors} erro(s), {warnings} aviso(s).")

    markdown = [
        "# Auditoria do código C++ gerado",
        "",
        "> Auditoria estática. Não compila nem comprova que o jogo inicia.",
        "",
        "## Resumo",
        "",
    ]
    markdown += [f"- **{key}**: {summary[key]}" for key in (
        "generated_cpp_files", "numbered_recomp_sources", "generated_header_files",
        "numbered_function_headers", "registered_functions", "ppc_function_mappings",
        "unique_function_definitions", "errors", "warnings",
    )]
    markdown += ["", "## Achados", ""]
    markdown += [
        f"- **{item['level']} / {item['code']}** — {item['message']}"
        for item in issues
    ] or ["- Nenhuma inconsistência estrutural detectada."]
    markdown += [
        "", "## Limites", "",
        "- Não valida a semântica das instruções PowerPC recompiladas.",
        "- Não resolve símbolos de runtime sem uma compilação/link real.",
        "- Detecções de APIs de plataforma são heurísticas e exigem revisão manual.",
        "- Não substitui teste em dispositivo Android ARM64.",
    ]
    if args.json_path:
        args.json_path.parent.mkdir(parents=True, exist_ok=True)
        args.json_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.markdown_path:
        args.markdown_path.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_path.write_text("\n".join(markdown) + "\n", encoding="utf-8")

    if errors or (args.strict and warnings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
