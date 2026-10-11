#!/usr/bin/env bash
set -euo pipefail

echo "===== PATCH DE COMPATIBILIDADE RE XGLUE ====="

SDK_DIR="rexglue-sdk"
HEADER_FILE="$SDK_DIR/include/rex/system/map_parser.h"
CPP_FILE="$SDK_DIR/src/system/map_parser.cpp"

if [ ! -d "$SDK_DIR" ]; then
    echo "ERRO: pasta rexglue-sdk não encontrada."
    exit 1
fi

# Garante o include no header.
if [ -f "$HEADER_FILE" ] &&
   ! grep -q '#include <expected>' "$HEADER_FILE"; then
    sed -i '1i #include <expected>' "$HEADER_FILE"
    echo "Include adicionado em map_parser.h"
fi

# Garante o include no arquivo .cpp.
if [ -f "$CPP_FILE" ] &&
   ! grep -q '#include <expected>' "$CPP_FILE"; then
    sed -i '1i #include <expected>' "$CPP_FILE"
    echo "Include adicionado em map_parser.cpp"
fi

# Adapta a opção específica do Clang, se estiver escrita nos arquivos.
grep -rlZ --exclude-dir=.git -- '-ffp-model=strict' "$SDK_DIR" |
while IFS= read -r -d '' FILE; do
    sed -i 's/-ffp-model=strict/-ffp-contract=off/g' "$FILE"
    echo "Opção de compilação adaptada: $FILE"
done

echo "===== TESTE DE expected E unexpected ====="

cat > /tmp/test_expected.cpp <<'EOF'
#include <expected>
#include <string>

std::expected<int, std::string> testar(bool sucesso) {
    if (sucesso) {
        return 42;
    }

    return std::unexpected(std::string("erro de teste"));
}

int main() {
    auto resultado = testar(true);
    return resultado.value() == 42 ? 0 : 1;
}
EOF

g++ -std=c++23 -fsyntax-only /tmp/test_expected.cpp

echo "OK: expected e unexpected reconhecidos pelo GCC."
echo "===== PATCH CONCLUÍDO ====="
