bash
#!/usr/bin/env bash
set -euo pipefail

echo "=========================================="
echo " PATCH DE COMPATIBILIDADE DO RE XGLUE"
echo "=========================================="

SDK_DIR="rexglue-sdk"

if [ ! -d "$SDK_DIR" ]; then
    echo "ERRO: pasta rexglue-sdk não encontrada."
    exit 1
fi

# 1. Adiciona o cabeçalho expected quando necessário.
HEADER_FILE="$SDK_DIR/include/rex/system/map_parser.h"

if [ -f "$HEADER_FILE" ] && ! grep -q '#include <expected>' "$HEADER_FILE"; then
    sed -i '/#include <vector>/a #include <expected>' "$HEADER_FILE"
    echo "Patch aplicado: map_parser.h"
fi

CPP_FILE="$SDK_DIR/src/system/map_parser.cpp"

if [ -f "$CPP_FILE" ] && ! grep -q '#include <expected>' "$CPP_FILE"; then
    sed -i '1i #include <expected>' "$CPP_FILE"
    echo "Patch aplicado: map_parser.cpp"
fi

# 2. Adapta a opção de ponto flutuante do Clang para GCC.
# O GCC aceita -ffp-contract=off.
while IFS= read -r -d '' FILE; do
    if grep -q -- '-ffp-model=strict' "$FILE"; then
        sed -i 's/-ffp-model=strict/-ffp-contract=off/g' "$FILE"
        echo "Opção de compilação adaptada em: $FILE"
    fi
done < <(
    grep -rlZ --exclude-dir=.git -- '-ffp-model=strict' "$SDK_DIR" || true
)

# 3. Mostra se ainda restou a opção incompatível.
if grep -rl --exclude-dir=.git -- '-ffp-model=strict' "$SDK_DIR"; then
    echo "AVISO: ainda existem ocorrências da opção do Clang."
else
    echo "Verificação: opção do Clang não encontrada no SDK."
fi

echo "=========================================="
echo " PATCHES CONCLUÍDOS"
echo "=========================================="
