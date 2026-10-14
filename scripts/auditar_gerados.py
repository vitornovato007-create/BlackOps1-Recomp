#!/usr/bin/env python3
"""Audita e organiza os artefatos de código gerado do BlackOps1-Recomp.

Uso:
  python3 scripts/auditar_gerados.py
  python3 scripts/auditar_gerados.py --strict

O script não gera código recompilado do nada. Ele verifica os arquivos que
precisam vir do codegen/ReXGlue e informa o que está faltando.
"""
from pathlib import Path
import argparse
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / "generated"
SOURCES = GEN / "sources"
HEADERS = GEN / "headers"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true",
                        help="retorna código de erro se faltarem fontes esperadas")
    args = parser.parse_args()
    cpp = sorted(set(GEN.glob("*.cpp")) | set(SOURCES.rglob("*.cpp")))
    headers = sorted(set(GEN.glob("*.h")) | set(GEN.glob("*.hpp")) |
                     set(HEADERS.rglob("*.h")) | set(HEADERS.rglob("*.hpp")))
    recomp = []
    for f in cpp:
        m = re.match(r"blackops1_recomp\.(\d+)\.cpp$", f.name)
        if m:
            recomp.append(int(m.group(1)))
    missing = [i for i in range(85) if i not in recomp]
    print("=== Auditoria de artefatos BlackOps1-Recomp ===")
    print(f"Fontes C++ encontradas: {len(cpp)}")
    print(f"Fontes blackops1_recomp.N.cpp reconhecidas: {len(recomp)}")
    print(f"Cabeçalhos .h/.hpp encontrados: {len(headers)}")
    print(f"Pasta de fontes: {SOURCES}")
    print(f"Pasta de cabeçalhos: {HEADERS}")
    if missing:
        print("Índices blackops1_recomp ausentes na raiz (os arquivos podem estar em sources/):")
        print(", ".join(map(str, missing)))
        print("Nota: o script reconhece fontes numeradas na pasta sources/ também.")
    if not cpp:
        print("ERRO: nenhuma fonte C++ gerada encontrada.")
    if not headers:
        print("AVISO: nenhum cabeçalho gerado encontrado.")
    if args.strict and (not cpp or missing):
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
