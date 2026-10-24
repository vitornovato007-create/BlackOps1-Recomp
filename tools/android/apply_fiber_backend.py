#!/usr/bin/env python3
"""Apply the Android ARM64 fiber backend to the temporary ReXGlue checkout."""
from pathlib import Path
import re

root = Path("rexglue-sdk")
patch_root = Path("patches/android")
header_src = patch_root / "fiber.h"
switch_src = patch_root / "fiber_switch.cpp"
header_dst = root / "include/rex/thread/fiber.h"
switch_dst = root / "src/core/fiber_switch.cpp"
cmake = root / "src/core/CMakeLists.txt"
posix = root / "src/core/fiber_posix.cpp"

for path in (header_src, switch_src, header_dst, cmake, posix):
    if not path.is_file():
        raise SystemExit(f"::error file={path}::Arquivo necessario ausente.")

# Keep the complete, reviewed implementation as persistent repository patches.
header_dst.write_text(header_src.read_text(encoding="utf-8"), encoding="utf-8")
switch_dst.write_text(switch_src.read_text(encoding="utf-8"), encoding="utf-8")

text = cmake.read_text(encoding="utf-8")

# Android needs the normal POSIX sources (threads, filesystem, dynamic library,
# memory, etc.). Only fiber_posix.cpp is incompatible with Bionic, so keep it
# out of the shared UNIX list and add it separately for non-Android UNIX.
# Match the condition independently of upstream comments/formatting.
text, replacements = re.subn(
    r"(?m)^elseif\(UNIX AND NOT ANDROID\)\s*$",
    "elseif(UNIX)",
    text,
    count=1,
)
if replacements != 1:
    # Some ReXGlue revisions use a plain UNIX branch already. Accept that
    # state, but fail clearly if neither expected form is present.
    if not re.search(r"(?m)^elseif\(UNIX\)\s*$", text):
        raise SystemExit("ERRO: ramo UNIX de fontes POSIX nao encontrado no CMakeLists.txt.")

platform_marker = "# Platform-specific sources"
platform_start = text.find(platform_marker)
if platform_start < 0:
    raise SystemExit("ERRO: secao de fontes de plataforma nao encontrada no CMakeLists.txt.")

platform_end_match = re.search(r"(?m)^endif\(\)\s*$", text[platform_start:])
if not platform_end_match:
    raise SystemExit("ERRO: fim da selecao de fontes de plataforma nao encontrado.")
platform_end = platform_start + platform_end_match.end()
platform_block = text[platform_start:platform_end]

# Remove fiber_posix.cpp from the shared UNIX source list.
platform_block = re.sub(r"(?m)^\s*fiber_posix\.cpp\s*\n", "", platform_block)
text = text[:platform_start] + platform_block + text[platform_end:]

# Add the POSIX fiber source only on non-Android platforms, exactly once.
conditional = """\n# POSIX ucontext fibers are not available on Android Bionic.
if(UNIX AND NOT ANDROID)
    target_sources(rexcore PRIVATE fiber_posix.cpp)
endif()
"""
if "target_sources(rexcore PRIVATE fiber_posix.cpp)" not in text:
    # Recompute the end after removing the source-list entry, because that
    # replacement changes the file length.
    platform_start = text.find(platform_marker)
    platform_end_match = re.search(r"(?m)^endif\(\)\s*$", text[platform_start:])
    if not platform_end_match:
        raise SystemExit("ERRO: nao foi possivel recalcular o fim da selecao de fontes.")
    platform_end = platform_start + platform_end_match.end()
    text = text[:platform_end] + conditional + text[platform_end:]

# Android uses the custom AAPCS64 fiber switch backend.
if "target_sources(rexcore PRIVATE fiber_switch.cpp)" not in text:
    marker = "add_library(rex::core ALIAS rexcore)\n"
    if marker not in text:
        raise SystemExit("ERRO: marcador do rexcore nao encontrado no CMakeLists.txt.")
    text = text.replace(
        marker,
        marker + "\nif(ANDROID)\n"
        "    # Android Bionic nao fornece makecontext/swapcontext.\n"
        "    target_sources(rexcore PRIVATE fiber_switch.cpp)\n"
        "endif()\n",
        1,
    )

cmake.write_text(text, encoding="utf-8")

text = posix.read_text(encoding="utf-8")
old_guard = "#if REX_PLATFORM_LINUX || REX_PLATFORM_MAC"
new_guard = "#if (REX_PLATFORM_LINUX && !REX_PLATFORM_ANDROID) || REX_PLATFORM_MAC"
if old_guard in text:
    text = text.replace(old_guard, new_guard, 1)
elif new_guard not in text:
    raise SystemExit("ERRO: guard de plataforma esperado nao encontrado em fiber_posix.cpp.")
posix.write_text(text, encoding="utf-8")

# Verify the platform source list retains all POSIX files except fiber_posix.cpp.
h = header_dst.read_text(encoding="utf-8")
c = cmake.read_text(encoding="utf-8")
p = posix.read_text(encoding="utf-8")
s = switch_dst.read_text(encoding="utf-8")
checks = {
    "header has Android ARM64 backend": "REX_PLATFORM_ANDROID && REX_ARCH_ARM64" in h,
    "switch implementation exists": "rex_fiber_swap" in s and "rex_fiber_trampoline" in s,
    "CMake includes Android switch backend": "target_sources(rexcore PRIVATE fiber_switch.cpp)" in c,
    "shared POSIX source branch remains enabled for Android": bool(re.search(r"(?m)^elseif\(UNIX\)\s*$", c)),
    "POSIX fiber is limited to non-Android UNIX": "if(UNIX AND NOT ANDROID)\n    target_sources(rexcore PRIVATE fiber_posix.cpp)" in c,
    "Android custom backend excludes POSIX fiber implementation": new_guard in p,
}
for label, ok in checks.items():
    print(("[OK] " if ok else "[ERRO] ") + label)
if not all(checks.values()):
    raise SystemExit("ERRO: verificacao do backend de fibers Android falhou.")
print("Backend de fibers Android ARM64 aplicado sem excluir os demais arquivos POSIX.")
