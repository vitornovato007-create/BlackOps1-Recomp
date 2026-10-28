#!/usr/bin/env bash
set -euo pipefail

python3 - <<'PYTHON'
from pathlib import Path
import re

numeric = Path("rexglue-sdk/include/rex/string/numeric.h")
chrono = Path("rexglue-sdk/include/rex/chrono/chrono.h")

for path in (numeric, chrono):
    if not path.is_file():
        raise SystemExit(f"::error file={path}::Cabecalho ReXGlue ausente.")

# The upstream SDK is freshly cloned on every workflow run, so apply
# these compatibility changes here instead of relying on repo edits.
# O patch Android fixado do ReXGlue ja altera estes guards para
# REX_PLATFORM_ANDROID. Este passo tambem aceita o SDK original,
# tornando a verificacao idempotente em ambos os formatos.
text = numeric.read_text(encoding="utf-8")
text, _ = re.subn(
    r"(?m)^#if REX_PLATFORM_MAC\s*$",
    "#if REX_PLATFORM_MAC || REX_PLATFORM_ANDROID",
    text,
)
already_patched_count = text.count(
    "#if REX_PLATFORM_MAC || REX_PLATFORM_ANDROID"
)
guard_count = already_patched_count
if guard_count < 3:
    raise SystemExit(
        "ERRO: numeric.h nao contem os guards esperados para "
        "REX_PLATFORM_ANDROID/float from_chars."
    )
numeric.write_text(text, encoding="utf-8")

text = chrono.read_text(encoding="utf-8")
old_guard = "#ifdef __APPLE__"
new_guard = "#if defined(__APPLE__) || (defined(_LIBCPP_VERSION) && _LIBCPP_VERSION < 200000)"
if old_guard in text:
    text = text.replace(old_guard, new_guard, 1)
    chrono.write_text(text, encoding="utf-8")
elif new_guard not in text:
    raise SystemExit(
        "ERRO: chrono.h nao contem o fallback libc++ esperado "
        "para Android NDK."
    )

# Confirme os simbolos realmente usados pelo patch Android fixado.
numeric_text = numeric.read_text(encoding="utf-8")
chrono_text = chrono.read_text(encoding="utf-8")
if "portable_float_from_chars" not in numeric_text:
    raise SystemExit("ERRO: fallback de float nao encontrado em numeric.h.")
if "REX_PLATFORM_ANDROID" not in numeric_text:
    raise SystemExit("ERRO: guard REX_PLATFORM_ANDROID ausente em numeric.h.")
if "_LIBCPP_VERSION < 200000" not in chrono_text:
    raise SystemExit("ERRO: fallback libc++/chrono nao foi habilitado para Android.")
if "clock_time_conversion" not in chrono_text:
    raise SystemExit("ERRO: declaracao clock_time_conversion ausente em chrono.h.")

print("Compatibilidade Android aplicada e verificada:")
print(f"  {numeric}: {guard_count} guards Android reconhecidos")
print(f"  {chrono}: fallback libc++/chrono confirmado")
PYTHON

echo "Confirmando alteracoes aplicadas:"
grep -n -E 'portable_float_from_chars|REX_PLATFORM_MAC.*REX_PLATFORM_ANDROID' \
  rexglue-sdk/include/rex/string/numeric.h
grep -n -E '_LIBCPP_VERSION|clock_time_conversion' \
  rexglue-sdk/include/rex/chrono/chrono.h | head -20
