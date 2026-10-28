#!/usr/bin/env bash
set -euo pipefail

FILE="rexglue-sdk/src/ui/CMakeLists.txt"

if [ ! -f "$FILE" ]; then
  echo "::error file=$FILE::CMakeLists.txt do rexui nao encontrado."
  exit 1
fi

python - "$FILE" <<'PYTHON'
import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
content = path.read_text(encoding="utf-8")

pattern = re.compile(
    r"(?m)^# Platform-specific dependencies[^\n]*\n"
    r".*?"
    r"(?=^if\(WIN32\)\s*$)",
    re.DOTALL,
)

replacement = """# Platform-specific dependencies.
# Android must not require Linux desktop X11/Wayland packages.
if(ANDROID)
    # SDL3 provides Android platform integration.
    target_link_libraries(rexui PUBLIC android)
elseif(UNIX AND NOT APPLE)
    find_package(PkgConfig REQUIRED)

    pkg_check_modules(X11_XCB REQUIRED x11-xcb)
    pkg_check_modules(WAYLAND REQUIRED wayland-client)

    target_include_directories(rexui PUBLIC
        ${X11_XCB_INCLUDE_DIRS}
        ${WAYLAND_INCLUDE_DIRS}
    )

    target_link_libraries(rexui PUBLIC
        ${X11_XCB_LIBRARIES}
        ${WAYLAND_LIBRARIES}
    )
elseif(APPLE)
    target_link_libraries(rexui PRIVATE "-framework CoreFoundation")
endif()

"""

updated, count = pattern.subn(
    lambda _: replacement,
    content,
    count=1,
)

if count != 1:
    raise SystemExit(
        "ERRO: nao foi possivel localizar a secao de "
        "dependencias de plataforma esperada em "
        "rexglue-sdk/src/ui/CMakeLists.txt. "
        "O arquivo nao foi alterado."
    )

path.write_text(updated, encoding="utf-8")

result = path.read_text(encoding="utf-8")

if "if(ANDROID)" not in result:
    raise SystemExit(
        "ERRO: o bloco de dependencias Android nao foi aplicado."
    )

print("Correcao Android aplicada ao ReXGlue.")
print("Verificando bloco de dependencias:")
print(
    result[
        result.find("# Platform-specific dependencies"):
        result.find("if(WIN32)", result.find(
            "# Platform-specific dependencies"
        ))
    ]
)
PYTHON
