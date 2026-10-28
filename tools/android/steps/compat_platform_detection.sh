#!/usr/bin/env bash
set -euo pipefail

python3 - <<'PYTHON'
from pathlib import Path
import re

path = Path("rexglue-sdk/CMakeLists.txt")
content = path.read_text(encoding="utf-8")
marker = "# Platform detection (supports AMD64 and ARM64)"
start = content.find(marker)
if start < 0:
    raise SystemExit("ERRO: bloco de deteccao de plataforma nao encontrado.")
end = content.find("# Build config as compile definition", start)
if end < 0:
    raise SystemExit("ERRO: fim do bloco de plataforma nao encontrado.")
block = content[start:end]

if "elseif(ANDROID)" in block:
    # O patch comunitario pode criar o ramo Android sem definir a
    # macro usada pelos fontes do SDK. Garanta ambos os requisitos.
    if "add_compile_definitions(REX_PLATFORM_ANDROID=1)" not in block:
        block = block.replace(
            "elseif(ANDROID)",
            "elseif(ANDROID)\n    add_compile_definitions(REX_PLATFORM_ANDROID=1)",
            1,
        )
        content = content[:start] + block + content[end:]
        path.write_text(content, encoding="utf-8")
        print("Macro REX_PLATFORM_ANDROID adicionada ao ramo Android existente.")
    else:
        print("Ramo Android e macro ja existem; nenhuma alteracao necessaria.")
else:
    old = "elseif(UNIX AND NOT APPLE)"
    if old not in block:
        raise SystemExit("ERRO: ramo Unix esperado nao encontrado no bloco de plataforma.")
    block = block.replace(
        old,
        """elseif(ANDROID)
    if(REX_TARGET_PROCESSOR MATCHES "aarch64|ARM64|arm64")
        set(REX_PLATFORM "android-arm64")
    else()
        message(FATAL_ERROR "ReXGlue Android requer ARM64; arquitetura: ${REX_TARGET_PROCESSOR}")
    endif()
    add_compile_definitions(REX_PLATFORM_ANDROID=1)
elseif(UNIX AND NOT APPLE)""",
        1,
    )
    content = content[:start] + block + content[end:]
    path.write_text(content, encoding="utf-8")

verify = path.read_text(encoding="utf-8")
start = verify.find(marker)
end = verify.find("# Build config as compile definition", start)
block = verify[start:end]
if "elseif(ANDROID)" not in block or 'set(REX_PLATFORM "android-arm64")' not in block:
    raise SystemExit("ERRO: selecao de plataforma Android nao foi aplicada.")
if "add_compile_definitions(REX_PLATFORM_ANDROID=1)" not in block:
    raise SystemExit("ERRO: macro REX_PLATFORM_ANDROID nao foi adicionada.")
print("Selecao de plataforma Android ARM64 aplicada e verificada.")
print(block)
PYTHON
