#!/usr/bin/env python3
"""Apply the pinned Android compatibility patch to the temporary ReXGlue SDK.

The third-party patch is downloaded at build time rather than redistributed in
this repository because its upstream repository does not declare a license.
"""
from pathlib import Path
import subprocess
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
SDK = ROOT / "rexglue-sdk"
PATCH_DIR = SDK / ".blackops1-android-patch"
PATCH_FILE = PATCH_DIR / "rexglue-sdk-v0.10.0-android.patch"
MARKER = PATCH_DIR / "applied"
PATCH_URL = (
    "https://raw.githubusercontent.com/deivid22srk/"
    "hells-gate-recomp-android/"
    "0a79f938ab839c187d25bd7bf48e51e30a6150be/"
    "patches/sdk/rexglue-sdk-v0.10.0-android.patch"
)


def fail(message: str) -> "None":
    print(f"::error::{message}", file=sys.stderr)
    raise SystemExit(1)


def is_applied() -> bool:
    header = SDK / "include/rex/main_android.h"
    source = SDK / "src/core/android_runtime.cpp"
    cmake = SDK / "src/core/CMakeLists.txt"
    if not (header.is_file() and source.is_file() and cmake.is_file()):
        return False
    return (
        "SetAndroidApplicationContext" in header.read_text(encoding="utf-8")
        and "android_runtime.cpp" in cmake.read_text(encoding="utf-8")
        and "InitializeAndroidSystemForApplicationContext" in source.read_text(encoding="utf-8")
    )


if not SDK.is_dir():
    fail(f"Checkout ReXGlue nao encontrado: {SDK}")

if MARKER.is_file() and is_applied():
    print("Patch de compatibilidade Android do ReXGlue ja aplicado.")
    raise SystemExit(0)

if is_applied():
    PATCH_DIR.mkdir(parents=True, exist_ok=True)
    MARKER.write_text("upstream pinned patch already present\n", encoding="utf-8")
    print("Patch de compatibilidade Android ja presente no SDK.")
    raise SystemExit(0)

PATCH_DIR.mkdir(parents=True, exist_ok=True)
if not PATCH_FILE.is_file():
    print(f"Baixando patch Android fixado: {PATCH_URL}")
    try:
        with urllib.request.urlopen(PATCH_URL, timeout=60) as response:
            PATCH_FILE.write_bytes(response.read())
    except Exception as error:
        fail(f"Nao foi possivel baixar o patch Android do ReXGlue: {error}")

# Validate before writing any SDK files. The patch is pinned to the ReXGlue
# v0.10.0 tree; a changed upstream layout must fail visibly, not build a
# partially patched runtime.
check = subprocess.run(
    ["patch", "--dry-run", "--batch", "--forward", "-p1", "-d", str(SDK), "-i", str(PATCH_FILE)],
    text=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
)
if check.returncode != 0:
    fail(
        "O patch Android nao corresponde ao checkout atual do ReXGlue. "
        "Nenhuma alteracao foi aplicada pelo script. Saida:\n" + check.stdout
    )

apply = subprocess.run(
    ["patch", "--batch", "--forward", "-p1", "-d", str(SDK), "-i", str(PATCH_FILE)],
    text=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
)
if apply.returncode != 0:
    fail("Falha ao aplicar o patch Android do ReXGlue:\n" + apply.stdout)

if not is_applied():
    fail("Patch aplicado, mas a API de contexto Android nao foi encontrada na validacao.")

MARKER.write_text("0a79f938ab839c187d25bd7bf48e51e30a6150be\n", encoding="utf-8")
print("Patch Android aplicado e validado: main_android.h, android_runtime.cpp e CMake.")
