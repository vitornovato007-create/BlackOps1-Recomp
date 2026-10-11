#!/usr/bin/env bash
set -e

echo "Aplicando patches de compatibilidade C++23 no rexglue-sdk..."

# 1. Patch no map_parser.h
HEADER_FILE="rexglue-sdk/include/rex/system/map_parser.h"
if [ -f "$HEADER_FILE" ] && ! grep -q "#include <expected>" "$HEADER_FILE"; then
    sed -i '/#include <vector>/a #include <expected>' "$HEADER_FILE"
    echo "Injetado #include <expected> em map_parser.h"
fi

# 2. Patch no map_parser.cpp
CPP_FILE="rexglue-sdk/src/system/map_parser.cpp"
if [ -f "$CPP_FILE" ] && ! grep -q "#include <expected>" "$CPP_FILE"; then
    sed -i '1i #include <expected>' "$CPP_FILE"
    echo "Injetado #include <expected> em map_parser.cpp"
fi

# 3. Garante no Precompiled Header (PCH) do SDK
PCH_FILE=$(find rexglue-sdk -name "cmake_pch.hxx" | head -n 1)
if [ -n "$PCH_FILE" ] && [ -f "$PCH_FILE" ] && ! grep -q "#include <expected>" "$PCH_FILE"; then
    echo "#include <expected>" >> "$PCH_FILE"
    echo "Injetado #include <expected> no PCH do projeto"
fi

echo "Patches aplicados com sucesso!"
