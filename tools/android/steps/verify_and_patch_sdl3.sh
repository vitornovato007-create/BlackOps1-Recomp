#!/usr/bin/env bash
set -euo pipefail

SDL_DIR="rexglue-sdk/thirdparty/sdl3"

if [ ! -f "$SDL_DIR/CMakeLists.txt" ]; then
  echo "::error::SDL3 nao encontrado em $SDL_DIR"
  exit 1
fi

if [ ! -d "$SDL_DIR/include/SDL3" ]; then
  echo "::error::Cabecalhos SDL3 nao encontrados."
  exit 1
fi

# O ReXGlue força SDL_SHARED=OFF e SDL_STATIC=ON no arquivo
# thirdparty/CMakeLists.txt. Isso produz SDL3 estático, mas
# SDLActivity exige libSDL3.so. Ative SDL compartilhado somente
# no build Android e preserve a configuração original em desktop.
python3 - <<'PY'
from pathlib import Path

path = Path("rexglue-sdk/thirdparty/CMakeLists.txt")
content = path.read_text()

old = '''set(SDL_SHARED OFF CACHE BOOL "" FORCE)
set(SDL_STATIC ON CACHE BOOL "" FORCE)'''
new = '''if(ANDROID)
    set(SDL_SHARED ON CACHE BOOL "" FORCE)
    set(SDL_STATIC OFF CACHE BOOL "" FORCE)
else()
    set(SDL_SHARED OFF CACHE BOOL "" FORCE)
    set(SDL_STATIC ON CACHE BOOL "" FORCE)
endif()'''

if old not in content:
    if new in content:
        print("SDL3 ja configurado como compartilhado no Android.")
    else:
        raise SystemExit(
            "ERRO: nao encontrei as definicoes SDL_SHARED/SDL_STATIC "
            "esperadas em rexglue-sdk/thirdparty/CMakeLists.txt."
        )
else:
    path.write_text(content.replace(old, new, 1))
    print("SDL3 configurado como biblioteca compartilhada somente no Android.")

check = path.read_text()
if "if(ANDROID)" not in check or 'set(SDL_SHARED ON CACHE BOOL "" FORCE)' not in check:
    raise SystemExit("ERRO: a configuracao SDL3 compartilhada nao foi confirmada.")
PY

echo "SDL3 encontrado e configurado para gerar libSDL3.so no Android."
git -C "$SDL_DIR" log -1 --oneline || true
