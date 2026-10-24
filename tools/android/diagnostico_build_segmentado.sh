#!/usr/bin/env bash
# Diagnosticos segmentados do build Android. Informativos: nao alteram arquivos do SDK.
set -uo pipefail

section() {
  local number="$1"
  local title="$2"
  echo
  echo "========== COMEÇO ANÁLISE ${number} =========="
  echo "[${title}]"
}
end_section() {
  local number="$1"
  echo "========== FIM ANÁLISE ${number} =========="
}

ROOT="${GITHUB_WORKSPACE:-$(pwd)}"
cd "$ROOT"

section 1 "REVISÃO DO AMBIENTE ANDROID E COMPILADOR"
echo "Data UTC: $(date -u '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null || echo indisponível)"
echo "Runner: ${RUNNER_OS:-desconhecido} / ${RUNNER_ARCH:-desconhecida}"
echo "ANDROID_HOME=${ANDROID_HOME:-não definido}"
echo "ANDROID_NDK_HOME=${ANDROID_NDK_HOME:-não definido}"
echo "ANDROID_NDK_ROOT=${ANDROID_NDK_ROOT:-não definido}"
if command -v cmake >/dev/null 2>&1; then cmake --version | head -n 1; fi
if command -v gradle >/dev/null 2>&1; then gradle --version | grep -E 'Gradle [0-9]' | head -n 1; fi

NDK="${ANDROID_NDK_HOME:-${ANDROID_NDK_ROOT:-}}"
if [[ -z "$NDK" && -n "${ANDROID_HOME:-}" ]]; then
  NDK="$(find "$ANDROID_HOME/ndk" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | sort -V | tail -n 1)"
fi
if [[ -n "$NDK" && -d "$NDK" ]]; then
  echo "NDK selecionado: $NDK"
  find "$NDK/toolchains/llvm/prebuilt" -path '*/bin/clang++' -type f -print 2>/dev/null | head -n 4
  CLANGXX="$(find "$NDK/toolchains/llvm/prebuilt" -path '*/bin/clang++' -type f -print -quit 2>/dev/null)"
  if [[ -n "$CLANGXX" ]]; then "$CLANGXX" --version | head -n 2; fi
  SYSROOT="$(dirname "$(dirname "$CLANGXX")")/sysroot"
else
  echo "AVISO: não foi possível localizar o NDK nesta etapa."
fi
end_section 1

section 2 "SUPORTE C++20: jthread E stop_token"
if [[ -n "${CLANGXX:-}" && -x "$CLANGXX" ]]; then
  TMP_CPP="$(mktemp --suffix=.cpp)"
  TMP_ERR="$(mktemp)"
  cat > "$TMP_CPP" <<'CPP'
#include <thread>
#include <stop_token>
int main() {
  std::jthread worker([](std::stop_token token) { (void)token.stop_requested(); });
  worker.request_stop();
  return 0;
}
CPP
  if "$CLANGXX" --target=aarch64-linux-android29 --sysroot="$SYSROOT" -std=c++20 -fsyntax-only "$TMP_CPP" >"$TMP_ERR" 2>&1; then
    echo "[OK] O compilador aceita std::jthread e std::stop_token em C++20."
  else
    echo "[FALHA] Teste isolado de std::jthread/std::stop_token falhou:"
    sed -n '1,100p' "$TMP_ERR"
  fi
  rm -f "$TMP_CPP" "$TMP_ERR"
else
  echo "[INDETERMINADO] clang++ do NDK não localizado."
fi
end_section 2

section 3 "PLATAFORMA E MACROS DO REXGLUE"
for file in rexglue-sdk/include/rex/platform.h rexglue-sdk/CMakeLists.txt rexglue-sdk/src/core/timer_queue.cpp; do
  if [[ -f "$file" ]]; then echo "[PRESENTE] $file"; else echo "[AUSENTE] $file"; fi
done
if [[ -f rexglue-sdk/include/rex/platform.h ]]; then
  echo "--- Linhas de detecção de plataforma ---"
  grep -n -E 'REX_PLATFORM_(ANDROID|LINUX|MAC)|__ANDROID__|ANDROID' rexglue-sdk/include/rex/platform.h | head -n 80 || true
fi
echo "--- Macros Android/Linux no CMake e Gradle ---"
grep -R -n -E -- '-D(REX_PLATFORM_LINUX|REX_PLATFORM_ANDROID|ANDROID)(=|[[:space:]]|$)|REX_PLATFORM_LINUX|REX_PLATFORM_ANDROID' \
  android/app/src/main/cpp rexglue-sdk/CMakeLists.txt rexglue-sdk/src/core 2>/dev/null | head -n 120 || true
end_section 3

section 4 "DEPENDÊNCIAS DE timer_queue.cpp"
TIMER="rexglue-sdk/src/core/timer_queue.cpp"
if [[ -f "$TIMER" ]]; then
  echo "--- Includes e usos de threading ---"
  grep -n -E '^#include|std::jthread|std::stop_token|request_stop|stop_requested|dispatch_thread_' "$TIMER" | head -n 120 || true
  echo "--- Cabeçalhos que podem fornecer compatibilidade ---"
  grep -R -n -E '(^|[^[:alnum:]_])(jthread|stop_token)([^[:alnum:]_]|$)' rexglue-sdk/include rexglue-sdk/src 2>/dev/null | head -n 100 || true
else
  echo "[AVISO] timer_queue.cpp não encontrado no caminho esperado."
fi
end_section 4

section 5 "ESTADO DOS PATCHES DE COMPATIBILIDADE"
for file in rexglue-sdk/include/rex/string/numeric.h rexglue-sdk/include/rex/chrono/chrono.h rexglue-sdk/src/ui/CMakeLists.txt; do
  if [[ -f "$file" ]]; then
    echo "--- $file ---"
    case "$file" in
      *numeric.h) grep -n -E 'portable_float_from_chars|REX_PLATFORM_MAC.*ANDROID|defined\\(__ANDROID__\\)' "$file" | head -n 40 || true ;;
      *chrono.h) grep -n -E 'defined\\(__ANDROID__\\)|defined\\(ANDROID\\)|clock_time_conversion|clock_cast' "$file" | head -n 40 || true ;;
      *CMakeLists.txt) grep -n -E 'if\\(ANDROID\\)|PkgConfig|X11_XCB|WAYLAND' "$file" | head -n 40 || true ;;
    esac
  else
    echo "[AUSENTE] $file"
  fi
done
end_section 5

section 6 "RESUMO DO DIAGNÓSTICO"
echo "Este relatório é informativo e não substitui o erro original do compilador."
echo "Se a compilação falhar, consulte também a primeira ocorrência de 'error:' no log."
end_section 6
