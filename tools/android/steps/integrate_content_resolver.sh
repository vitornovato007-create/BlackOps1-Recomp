#!/usr/bin/env bash
set -euo pipefail

SOURCE="patches/android/filesystem_android.cpp"
TARGET="rexglue-sdk/src/core/filesystem_android.cpp"
CMAKE_FILE="rexglue-sdk/src/core/CMakeLists.txt"

test -f "$SOURCE"
test -f "$CMAKE_FILE"
cp "$SOURCE" "$TARGET"

python3 - "$CMAKE_FILE" <<'PYTHON'
import sys
from pathlib import Path

path = Path(sys.argv[1])
content = path.read_text(encoding="utf-8")
marker = """# Xenos data-format layer (stateless; headers under include/rex/graphics/)."""
block = """# Android ContentResolver bridge for content:// file descriptors.
if(ANDROID)
    target_sources(rexcore PRIVATE filesystem_android.cpp)
endif()

"""
if "target_sources(rexcore PRIVATE filesystem_android.cpp)" not in content:
    if marker not in content:
        raise SystemExit("ERRO: ponto de insercao no CMakeLists.txt do rexcore nao encontrado.")
    content = content.replace(marker, block + marker, 1)
if "target_link_libraries(rexcore PRIVATE SDL3::SDL3)" not in content:
    content = content.replace(
        "target_sources(rexcore PRIVATE filesystem_android.cpp)",
        "target_sources(rexcore PRIVATE filesystem_android.cpp)\n    target_link_libraries(rexcore PRIVATE SDL3::SDL3)",
        1,
    )
path.write_text(content, encoding="utf-8")

verify = path.read_text(encoding="utf-8")
if "target_sources(rexcore PRIVATE filesystem_android.cpp)" not in verify:
    raise SystemExit("ERRO: a integracao Android nao foi adicionada ao alvo rexcore.")
if "target_link_libraries(rexcore PRIVATE SDL3::SDL3)" not in verify:
    raise SystemExit("ERRO: dependencias de cabecalho SDL3 nao foram adicionadas ao rexcore.")
print("Filesystem Android integrado ao alvo rexcore com SDL3.")
PYTHON

grep -n -A4 -B2 'filesystem_android.cpp' "$CMAKE_FILE"
grep -n -E 'AndroidInitialize|IsAndroidContentUri|OpenAndroidContentFileDescriptor' "$TARGET"
