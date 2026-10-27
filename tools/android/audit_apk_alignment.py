#!/usr/bin/env python3
"""Verify key native libraries in the APK support Android 16 KiB page sizes."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

REQUIRED_LIBRARIES = (
    "lib/arm64-v8a/libblackops1_android.so",
    "lib/arm64-v8a/libblackops1_xiso.so",
    "lib/arm64-v8a/libSDL3.so",
)
MIN_ALIGNMENT = 0x4000


def find_readelf() -> Path:
    candidates: list[Path] = []
    for key in ("ANDROID_NDK_HOME", "ANDROID_NDK_ROOT"):
        value = os.environ.get(key)
        if value:
            candidates.append(Path(value))
    for key in ("ANDROID_HOME", "ANDROID_SDK_ROOT"):
        value = os.environ.get(key)
        if value:
            candidates.extend(sorted((Path(value) / "ndk").glob("*"), reverse=True))
    for ndk in candidates:
        tool = ndk / "toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-readelf"
        if tool.is_file():
            return tool
    on_path = shutil.which("llvm-readelf")
    if on_path:
        return Path(on_path)
    raise RuntimeError("llvm-readelf nao encontrado no NDK do runner.")


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Uso: {Path(sys.argv[0]).name} caminho/do.apk", file=sys.stderr)
        return 2

    apk = Path(sys.argv[1])
    if not apk.is_file():
        print(f"::error file={apk}::APK nao encontrado.", file=sys.stderr)
        return 2

    readelf = find_readelf()
    failures: list[str] = []
    with zipfile.ZipFile(apk) as archive, tempfile.TemporaryDirectory() as temp:
        names = set(archive.namelist())
        for member in REQUIRED_LIBRARIES:
            if member not in names:
                failures.append(f"{member}: biblioteca ausente do APK")
                continue
            extracted = Path(temp) / Path(member).name
            extracted.write_bytes(archive.read(member))
            result = subprocess.run(
                [str(readelf), "-l", str(extracted)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            if result.returncode:
                failures.append(f"{member}: llvm-readelf falhou: {result.stdout[-1000:]}")
                continue
            aligns: list[int] = []
            for line in result.stdout.splitlines():
                if re.match(r"\s*LOAD\s", line):
                    match = re.search(r"\b0x([0-9a-fA-F]+)\s*$", line)
                    if match:
                        aligns.append(int(match.group(1), 16))
            if not aligns:
                failures.append(f"{member}: nenhum segmento LOAD foi analisado")
                continue
            smallest = min(aligns)
            print(f"[ELF] {member}: LOAD alignment(s)={[hex(x) for x in aligns]}")
            if smallest < MIN_ALIGNMENT:
                failures.append(
                    f"{member}: alinhamento minimo {hex(smallest)}; esperado >= 0x4000"
                )

    if failures:
        for failure in failures:
            print(f"::error::{failure}", file=sys.stderr)
        return 1
    print("OK: bibliotecas nativas criticas alinhadas para paginas de 16 KiB.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, zipfile.BadZipFile) as error:
        print(f"::error::{error}", file=sys.stderr)
        raise SystemExit(1)
