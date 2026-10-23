#!/usr/bin/env python3
"""Compatibilidade: encaminha a auditoria Android para o diagnostico unificado.

Uso:
  python3 tools/android/auditar_integracao.py
  python3 tools/android/auditar_integracao.py --strict

Sem --strict, os problemas conhecidos sao reportados sem interromper a
inspecao. Com --strict, o comando retorna codigo diferente de zero quando
encontrar bloqueadores estaticos. Nenhuma dessas opcoes substitui a compilacao.
"""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
DIAGNOSTIC = ROOT / "tools" / "diagnostico_completo.py"

if not DIAGNOSTIC.is_file():
    print(f"ERRO: diagnostico unificado nao encontrado: {DIAGNOSTIC}", file=sys.stderr)
    raise SystemExit(2)

result = subprocess.run(
    [sys.executable, str(DIAGNOSTIC), *sys.argv[1:]],
    cwd=ROOT,
    check=False,
)
raise SystemExit(result.returncode)
