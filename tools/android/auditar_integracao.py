#!/usr/bin/env python3
"""Static checks for the experimental Android ARM64 integration (not a build test)."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
checks = {
    "SDK CMake": ROOT / "rexglue-sdk/CMakeLists.txt",
    "Android surface header": ROOT / "rexglue-sdk/include/rex/ui/surface_android.h",
    "Android surface implementation": ROOT / "rexglue-sdk/src/ui/surface_android.cpp",
    "SDL Android Activity": ROOT / "android/app/src/main/java/com/blackops1/recomp/MainActivity.java",
    "Android native CMake": ROOT / "android/app/src/main/cpp/CMakeLists.txt",
    "Generated source manifest": ROOT / "generated/sources.cmake",
    "XEX required for private APK": ROOT / "game/default.xex",
}
failed = False
for label, path in checks.items():
    ok = path.is_file()
    print(f"{'OK' if ok else 'FALTA'}: {label}: {path.relative_to(ROOT)}")
    failed |= not ok

cmake = (ROOT / "android/app/src/main/cpp/CMakeLists.txt").read_text(encoding="utf-8")
for token in ("add_subdirectory(\"${REXGLUE_SOURCE_DIR}\"", "rex::runtime", "rex::gpu-xenos", "${GENERATED_SOURCES}"):
    ok = token in cmake
    print(f"{'OK' if ok else 'FALTA'}: Android CMake contém {token}")
    failed |= not ok

src = ROOT / "generated/sources"
files = sorted(src.glob("blackops1_recomp.*.cpp")) if src.is_dir() else []
print(f"Fontes recompiladas organizadas: {len(files)}")
if not files:
    print("FALTA: nenhuma fonte em generated/sources/", file=sys.stderr)
    failed = True

print("ATENÇÃO: esta auditoria é estática; não prova compilação, carregamento do Vulkan ou boot do jogo.")
raise SystemExit(1 if failed else 0)
