#!/usr/bin/env bash
set -euo pipefail

RUNTIME_SOURCE="rexglue-sdk/src/core/android_runtime.cpp"
CMAKE_FILE="rexglue-sdk/src/core/CMakeLists.txt"
JAVA_ACTIVITY="android/app/src/main/java/com/blackops1/recomp/GameActivity.java"
LEGACY_SOURCE="rexglue-sdk/src/core/filesystem_android.cpp"

test -f "$RUNTIME_SOURCE"
test -f "$CMAKE_FILE"
test -f "$JAVA_ACTIVITY"

# O patch Android fixado do ReXGlue ja fornece as quatro funcoes
# rex::filesystem e encaminha a abertura de content:// pela ponte JNI.
# Nao compile uma segunda implementacao dessas mesmas funcoes.
python3 - "$RUNTIME_SOURCE" "$CMAKE_FILE" "$JAVA_ACTIVITY" <<'PYTHON'
import re
import sys
from pathlib import Path

runtime_path = Path(sys.argv[1])
cmake_path = Path(sys.argv[2])
java_path = Path(sys.argv[3])

runtime = runtime_path.read_text(encoding="utf-8")
required_runtime_symbols = (
    "AndroidInitialize()",
    "AndroidShutdown()",
    "IsAndroidContentUri(",
    "OpenAndroidContentFileDescriptor(",
    "OpenContentUriFdJavaBridge",
)
missing = [symbol for symbol in required_runtime_symbols if symbol not in runtime]
if missing:
    raise SystemExit(
        "ERRO: android_runtime.cpp nao contem a implementacao/ponte esperada: "
        + ", ".join(missing)
    )

java = java_path.read_text(encoding="utf-8")
if not re.search(r"static\s+ParcelFileDescriptor\s+openContentFd\s*\(", java):
    raise SystemExit(
        "ERRO: GameActivity.java nao declara o metodo estatico openContentFd "
        "esperado pela ponte Android."
    )

cmake = cmake_path.read_text(encoding="utf-8")

# Remove o bloco legado adicionado por esta etapa em execucoes anteriores.
# O bloco incluia filesystem_android.cpp (duplicava os simbolos) e a ligacao
# SDL3 que so era necessaria para essa implementacao alternativa.
cmake, removed = re.subn(
    r"(?m)^# Android ContentResolver bridge for content:// file descriptors\.\n"
    r"if\(ANDROID\)\n"
    r"(?:    target_sources\(rexcore PRIVATE filesystem_android\.cpp\)\n)?"
    r"(?:    target_link_libraries\(rexcore PRIVATE SDL3::SDL3\)\n)?"
    r"endif\(\)\n?",
    "",
    cmake,
)

# Fail closed if an older/malformed insertion remains instead of silently
# building both implementations again.
if "target_sources(rexcore PRIVATE filesystem_android.cpp)" in cmake:
    raise SystemExit(
        "ERRO: CMakeLists.txt ainda adiciona filesystem_android.cpp; "
        "remova a integracao customizada duplicada."
    )

cmake_path.write_text(cmake, encoding="utf-8")
print(
    "ContentResolver validado: android_runtime.cpp + GameActivity.openContentFd; "
    "implementacao C++ duplicada desativada."
)
PYTHON

# Remove somente a copia gerada por esta etapa; o arquivo-fonte versionado
# em patches/android/ e mantido para historico, mas nao entra no alvo rexcore.
rm -f "$LEGACY_SOURCE"

if grep -q 'filesystem_android.cpp' "$CMAKE_FILE"; then
    echo "ERRO: filesystem_android.cpp ainda aparece no CMakeLists.txt." >&2
    exit 1
fi

grep -n -E 'AndroidInitialize|IsAndroidContentUri|OpenAndroidContentFileDescriptor|OpenContentUriFdJavaBridge' "$RUNTIME_SOURCE"
grep -n -A2 -B2 'openContentFd' "$JAVA_ACTIVITY"
