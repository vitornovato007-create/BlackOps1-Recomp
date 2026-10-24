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

# Prefer the exact NDK version declared by the Android Gradle module. The
# runner's ANDROID_NDK_HOME can point at an older preinstalled NDK.
NDK_VERSION=""
if [[ -f android/app/build.gradle ]]; then
  NDK_VERSION="$(sed -nE "s/^[[:space:]]*ndkVersion[[:space:]]+['\\\"]([^'\\\"]+)['\\\"].*/\\1/p" android/app/build.gradle | head -n 1)"
fi
NDK=""
if [[ -n "$NDK_VERSION" && -n "${ANDROID_HOME:-}" && -d "$ANDROID_HOME/ndk/$NDK_VERSION" ]]; then
  NDK="$ANDROID_HOME/ndk/$NDK_VERSION"
elif [[ -n "${ANDROID_HOME:-}" && -d "$ANDROID_HOME/ndk" ]]; then
  NDK="$(find "$ANDROID_HOME/ndk" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | sort -V | tail -n 1)"
elif [[ -n "${ANDROID_NDK_HOME:-}" && -d "$ANDROID_NDK_HOME" ]]; then
  NDK="$ANDROID_NDK_HOME"
elif [[ -n "${ANDROID_NDK_ROOT:-}" && -d "$ANDROID_NDK_ROOT" ]]; then
  NDK="$ANDROID_NDK_ROOT"
fi
echo "NDK exigido pelo Gradle: ${NDK_VERSION:-não detectado}"
if [[ -n "$NDK" && -d "$NDK" ]]; then
  echo "NDK selecionado: $NDK"
  find "$NDK/toolchains/llvm/prebuilt" -path '*/bin/clang++' \( -type f -o -type l \) -print 2>/dev/null | head -n 4
  CLANGXX="$(find "$NDK/toolchains/llvm/prebuilt" -path '*/bin/clang++' \( -type f -o -type l \) -print -quit 2>/dev/null)"
  if [[ -n "$CLANGXX" ]]; then "$CLANGXX" --version | head -n 2; fi
  SYSROOT="$(dirname "$(dirname "$CLANGXX")")/sysroot"
else
  echo "AVISO: não foi possível localizar o NDK nesta etapa."
fi
end_section 1

section 2 "SUPORTE C++20/C++23: jthread E stop_token"
if [[ -n "${CLANGXX:-}" && -x "${CLANGXX}" && -n "${SYSROOT:-}" && -d "${SYSROOT}" ]]; then
  echo "--- Identidade do compilador e alvo Android ---"
  "${CLANGXX}" --target=aarch64-linux-android29 --sysroot="${SYSROOT}" -stdlib=libc++ -dM -E -x c++ /dev/null 2>/dev/null | grep -E '^#define (__ANDROID__|__cplusplus|_LIBCPP_VERSION|_LIBCPP_HAS_NO_THREADS|__cpp_lib_jthread)' || true
  echo "--- Cabeçalho thread selecionado ---"
  printf '#include <thread>\n' | "${CLANGXX}" --target=aarch64-linux-android29 --sysroot="${SYSROOT}" -stdlib=libc++ -std=c++23 -pthread -E -H -x c++ - >/dev/null 2>&1 || true
  for STANDARD in c++20 c++23; do
    TMP_CPP="$(mktemp --suffix=.cpp)"
    TMP_ERR="$(mktemp)"
    cat > "$TMP_CPP" <<'CPP'
#include <version>
#include <thread>
#include <stop_token>
#ifndef __cpp_lib_jthread
#error "__cpp_lib_jthread nao definido pela biblioteca padrao"
#endif
int main() {
  std::jthread worker([](std::stop_token token) { (void)token.stop_requested(); });
  worker.request_stop();
  return 0;
}
CPP
    echo "--- Teste com -std=${STANDARD} ---"
    if "${CLANGXX}" --target=aarch64-linux-android29 --sysroot="${SYSROOT}" -stdlib=libc++ "-std=${STANDARD}" -pthread -fsyntax-only "$TMP_CPP" >"$TMP_ERR" 2>&1; then
      echo "[OK] ${STANDARD}: std::jthread e std::stop_token disponíveis."
    else
      echo "[FALHA] ${STANDARD}: teste isolado falhou:"
      sed -n '1,100p' "$TMP_ERR"
    fi
    rm -f "$TMP_CPP" "$TMP_ERR"
  done
else
  echo "[INDETERMINADO] clang++ do NDK ou sysroot não localizado."
fi


section 3 "PLATAFORMA E MACROS DO REXGLUE"
for file in rexglue-sdk/include/rex/platform.h rexglue-sdk/CMakeLists.txt rexglue-sdk/src/core/timer_queue.cpp; do
  if [[ -f "$file" ]]; then echo "[PRESENTE] $file"; else echo "[AUSENTE] $file"; fi
done
if [[ -f rexglue-sdk/include/rex/platform.h ]]; then
  echo "--- Linhas de detecção de plataforma ---"
  grep -n -E 'REX_PLATFORM_(ANDROID|LINUX|MAC)|__ANDROID__|ANDROID' rexglue-sdk/include/rex/platform.h | head -n 80 || true
  echo "--- Seleção de plataforma no CMake ---"
  grep -n -A 24 -B 3 '^# Platform detection' rexglue-sdk/CMakeLists.txt || true
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
