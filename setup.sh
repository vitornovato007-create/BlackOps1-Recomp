#!/usr/bin/env bash
set -euo pipefail

echo "BlackOps1-Recomp v0.1 setup"
echo
echo "This script does not download or contain game data."
echo
echo "Expected local file:"
echo "  game/default.xex"
echo

if [ ! -f "game/default.xex" ]; then
    echo "WARNING: game/default.xex was not found."
    echo "Place your own legally obtained Xbox 360 XEX there before codegen."
    exit 0
fi

echo "Found game/default.xex"
echo "Ready for the ReXGlue 0.10.0 codegen step."
