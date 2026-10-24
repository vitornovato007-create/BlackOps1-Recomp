#!/usr/bin/env python3
"""Apply the Android ARM64 fiber backend to the temporary ReXGlue checkout."""
from pathlib import Path

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
if "fiber_switch.cpp" not in text:
    marker = "add_library(rex::core ALIAS rexcore)\n"
    if marker not in text:
        raise SystemExit("ERRO: marcador do rexcore nao encontrado no CMakeLists.txt.")
    text = text.replace(
        marker,
        marker + "\nif(ANDROID)\n    # Android Bionic nao fornece makecontext/swapcontext.\n"
        "    target_sources(rexcore PRIVATE fiber_switch.cpp)\nendif()\n",
        1,
    )
# Ensure Android does not also compile the POSIX backend through elseif(UNIX).
old = "elseif(UNIX)\n    # Linux and macOS/Darwin share the POSIX sources;"
new = "elseif(UNIX AND NOT ANDROID)\n    # Linux and macOS/Darwin share the POSIX sources;"
if old in text:
    text = text.replace(old, new, 1)
elif "elseif(UNIX AND NOT ANDROID)" not in text:
    raise SystemExit("ERRO: ramo UNIX esperado nao encontrado no CMakeLists.txt.")
cmake.write_text(text, encoding="utf-8")

text = posix.read_text(encoding="utf-8")
old_guard = "#if REX_PLATFORM_LINUX || REX_PLATFORM_MAC"
new_guard = "#if (REX_PLATFORM_LINUX && !REX_PLATFORM_ANDROID) || REX_PLATFORM_MAC"
if old_guard in text:
    text = text.replace(old_guard, new_guard, 1)
elif new_guard not in text:
    raise SystemExit("ERRO: guard de plataforma esperado nao encontrado em fiber_posix.cpp.")
posix.write_text(text, encoding="utf-8")

# Verify backend selection and guards before allowing the build to continue.
h = header_dst.read_text(encoding="utf-8")
c = cmake.read_text(encoding="utf-8")
p = posix.read_text(encoding="utf-8")
s = switch_dst.read_text(encoding="utf-8")
checks = {
    "header has Android ARM64 backend": "REX_PLATFORM_ANDROID && REX_ARCH_ARM64" in h,
    "switch implementation exists": "rex_fiber_swap" in s and "rex_fiber_trampoline" in s,
    "CMake includes switch backend": "target_sources(rexcore PRIVATE fiber_switch.cpp)" in c,
    "CMake excludes Android from UNIX backend": "elseif(UNIX AND NOT ANDROID)" in c,
    "POSIX source excludes Android": new_guard in p,
}
for label, ok in checks.items():
    print(("[OK] " if ok else "[ERRO] ") + label)
if not all(checks.values()):
    raise SystemExit("ERRO: verificacao do backend de fibers Android falhou.")
print("Backend de fibers Android ARM64 aplicado.")
