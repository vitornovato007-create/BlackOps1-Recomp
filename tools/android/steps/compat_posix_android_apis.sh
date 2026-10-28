#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PYTHON'
from pathlib import Path
import re

root = Path("rexglue-sdk")
memory = root / "src/core/memory_posix.cpp"
threading = root / "src/core/threading_posix.cpp"
header = root / "include/rex/main_android.h"

for path in (memory, threading):
    if not path.is_file():
        raise SystemExit(f"::error file={path}::Arquivo ReXGlue necessario ausente.")

# Android's NDK exposes the device API level directly.
text = memory.read_text(encoding="utf-8")
if "#include <android/api-level.h>" not in text:
    text, count = re.subn(
        r"(?m)^#if REX_PLATFORM_ANDROID\s*$",
        "#if REX_PLATFORM_ANDROID\n#include <android/api-level.h>",
        text,
        count=1,
    )
    if count != 1:
        raise SystemExit("ERRO: bloco Android nao encontrado em memory_posix.cpp.")
text = text.replace("rex::GetAndroidApiLevel()", "android_get_device_api_level()")
if "android_get_device_api_level()" not in text or "#include <android/api-level.h>" not in text:
    raise SystemExit("ERRO: API level Android nao foi corrigida em memory_posix.cpp.")
memory.write_text(text, encoding="utf-8")

text = threading.read_text(encoding="utf-8")
old_assert = 'static_assert(REX_PLATFORM_LINUX || REX_PLATFORM_MAC, "This file is POSIX-only");'
new_assert = 'static_assert(REX_PLATFORM_LINUX || REX_PLATFORM_MAC || REX_PLATFORM_ANDROID, "This file is POSIX-only");'
if old_assert in text:
    text = text.replace(old_assert, new_assert, 1)
elif new_assert not in text:
    raise SystemExit("ERRO: static_assert esperado nao encontrado em threading_posix.cpp.")
if "#include <rex/main_android.h>" not in text:
    raise SystemExit("ERRO: include esperado rex/main_android.h nao encontrado em threading_posix.cpp.")

# Linux-only extensions and robust-mutex recovery must not be
# compiled for Android's Bionic libc. Do not count source blocks:
# the pinned community patch may rearrange/nest preprocessor guards.
# Normalize every top-level Linux guard in this POSIX file instead.
android_safe_guard = "#if REX_PLATFORM_LINUX && !defined(__ANDROID__)"
text = re.sub(
    r"(?m)^#if REX_PLATFORM_LINUX\s*$",
    android_safe_guard,
    text,
)

# Idempotent verification: no unguarded exact Linux guard may remain.
if re.search(r"(?m)^#if REX_PLATFORM_LINUX\s*$", text):
    raise SystemExit(
        "ERRO: ainda existe um guard Linux que nao exclui Android."
    )
if android_safe_guard not in text:
    raise SystemExit(
        "ERRO: nenhum guard Linux Android-safe foi aplicado em threading_posix.cpp."
    )
if not all(marker in text for marker in (
    "PTHREAD_MUTEX_ROBUST",
    "pthread_mutexattr_setrobust",
    "EOWNERDEAD",
)):
    raise SystemExit(
        "ERRO: a fonte mudou e os marcadores de mutex robusto nao foram encontrados."
    )
print(
    "Guards Linux normalizados para excluir Android; "
    "sem contagem fragil de blocos."
)
threading.write_text(text, encoding="utf-8")

# O patch Android fixado ja fornece main_android.h com as declaracoes
# de GetAndroidNativeLibraryDir, SetAndroidApplicationContext e
# GetAndroidApiLevel. Nao sobrescreva esse header: filesystem_posix.cpp
# depende de GetAndroidNativeLibraryDir durante a compilacao.
if not header.is_file():
    raise SystemExit("ERRO: main_android.h do patch Android esta ausente.")
header_text = header.read_text(encoding="utf-8")
required_android_api = (
    "GetAndroidNativeLibraryDir",
    "SetAndroidApplicationContext",
    "GetAndroidApiLevel",
)
missing_api = [name for name in required_android_api if name not in header_text]
if missing_api:
    raise SystemExit(
        "ERRO: main_android.h perdeu declaracoes do patch Android: "
        + ", ".join(missing_api)
    )

if new_assert not in threading.read_text(encoding="utf-8"):
    raise SystemExit("ERRO: threading_posix.cpp nao habilitou a compilacao Android.")
print("APIs Android corrigidas; declaracoes originais do patch preservadas.")
print(f"Cabecalho Android validado: {header}")
PYTHON
