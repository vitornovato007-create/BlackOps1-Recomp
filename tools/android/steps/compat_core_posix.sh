#!/usr/bin/env bash
set -euo pipefail

FILE="rexglue-sdk/src/core/CMakeLists.txt"
if [ ! -f "$FILE" ]; then
  echo "::error file=$FILE::CMakeLists.txt do rexcore nao encontrado."
  exit 1
fi

python - "$FILE" <<'PYTHON'
import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
content = path.read_text(encoding="utf-8")

# O patch Android do SDK pode alterar o ramo UNIX antes deste passo.
# Localizamos o bloco de link POSIX pelo alvo rexcore e pelo proximo
# bloco de dependencias PUBLIC, em vez de depender de texto identico.
next_block = content.find("target_link_libraries(rexcore")
candidates = []
cursor = 0
while True:
    found = content.find("if(APPLE)", cursor)
    if found < 0 or (next_block >= 0 and found >= next_block):
        break
    candidates.append(found)
    cursor = found + 1

public_marker = re.search(
    r"(?m)^target_link_libraries\(rexcore\s*\n\s*PUBLIC\s*$",
    content,
)
if not public_marker:
    raise SystemExit(
        "ERRO: bloco PUBLIC do rexcore nao encontrado; "
        "nao e seguro alterar as dependencias POSIX."
    )

start = content.rfind("if(APPLE)", 0, public_marker.start())
if start < 0:
    raise SystemExit("ERRO: bloco de link POSIX do rexcore nao encontrado.")

existing_region = content[start:public_marker.start()]
android_link = re.search(
    r"(?m)^\s*target_link_libraries\(rexcore\s+PRIVATE\s+dl\s*\)",
    existing_region,
)
android_branch = re.search(r"(?m)^\s*elseif\(ANDROID\)\s*$", existing_region)

if not (android_link and android_branch):
    normalized = """if(APPLE)
    target_link_libraries(rexcore PRIVATE pthread)
elseif(ANDROID)
    # Bionic supplies pthread/realtime APIs; libdl remains explicit.
    target_link_libraries(rexcore PRIVATE dl)
elseif(UNIX)
    target_link_libraries(rexcore PRIVATE pthread rt dl)
endif()

"""
    content = content[:start] + normalized + content[public_marker.start():]
    path.write_text(content, encoding="utf-8")

final = path.read_text(encoding="utf-8")
final_public = re.search(
    r"(?m)^target_link_libraries\(rexcore\s*\n\s*PUBLIC\s*$",
    final,
)
final_start = final.rfind("if(APPLE)", 0, final_public.start()) if final_public else -1
final_region = final[final_start:final_public.start()] if final_start >= 0 and final_public else ""
if not re.search(r"(?m)^\s*elseif\(ANDROID\)\s*$", final_region):
    raise SystemExit("ERRO: ramo Android ausente nas dependencias POSIX do rexcore.")
if not re.search(
    r"(?m)^\s*target_link_libraries\(rexcore\s+PRIVATE\s+dl\s*\)",
    final_region,
):
    raise SystemExit("ERRO: libdl nao foi configurada para Android no rexcore.")
if not re.search(r"(?m)^\s*elseif\(UNIX\)\s*$", final_region):
    raise SystemExit("ERRO: dependencias POSIX de desktop foram perdidas.")
print("Dependencias de link Android/POSIX do rexcore corrigidas e verificadas.")
PYTHON

grep -n -A10 -B2 'target_link_libraries(rexcore PRIVATE' "$FILE"
