#!/usr/bin/env python3
"""Initialize the ReXGlue SDK submodules for ZIP-based project checkouts.

The repository ZIP does not carry gitlink commit IDs, so when .git metadata is
unavailable this script shallow-clones the URLs/branches listed in .gitmodules.
For reproducible upstream versions, use a real recursive Git checkout instead.
"""
from __future__ import annotations
import configparser
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SDK = ROOT / "rexglue-sdk"
MODULES = SDK / ".gitmodules"

def run(args: list[str], cwd: Path | None = None) -> None:
    print("+", " ".join(args), flush=True)
    subprocess.run(args, cwd=cwd, check=True)

def main() -> int:
    if not (SDK / "CMakeLists.txt").is_file() or not MODULES.is_file():
        print("ERRO: rexglue-sdk/.gitmodules ou CMakeLists.txt ausente", file=sys.stderr)
        return 2
    if (ROOT / ".git").exists() and (SDK / ".git").exists():
        run(["git", "submodule", "update", "--init", "--recursive"], cwd=SDK)
        return 0
    parser = configparser.ConfigParser()
    parser.read(MODULES, encoding="utf-8")
    thirdparty = SDK / "thirdparty"
    failures = []
    for section in parser.sections():
        rel = parser.get(section, "path", fallback="").strip()
        url = parser.get(section, "url", fallback="").strip()
        branch = parser.get(section, "branch", fallback="").strip()
        if not rel or not url:
            continue
        dest = SDK / rel
        # A real populated checkout is left intact.
        if (dest / ".git").exists() and any(dest.iterdir()):
            continue
        if dest.exists():
            shutil.rmtree(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        cmd = ["git", "clone", "--depth", "1"]
        if branch:
            cmd += ["--branch", branch]
        cmd += [url, str(dest)]
        try:
            run(cmd)
        except subprocess.CalledProcessError as exc:
            failures.append((rel, exc.returncode))
    if failures:
        print("Falha ao obter submódulos:", file=sys.stderr)
        for rel, code in failures:
            print(f" - {rel} (exit {code})", file=sys.stderr)
        return 1
    print("Submódulos baixados. Atenção: ZIPs não preservam os commits exatos dos gitlinks.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
