#!/usr/bin/env python3
"""Apply and verify the Android-safe ReXGlue logging path after checkout."""

from pathlib import Path
import re
import sys

SOURCE = Path("rexglue-sdk/src/ui/rex_app.cpp")
MARKER = "ANDROID_SAFE_LOG_DIR_PATCH"
OLD_ASSIGNMENT = 'log_config.log_dir = (exe_dir / "logs").string();'


def fail(message: str) -> "None":
    print(f"::error::{message}", file=sys.stderr)
    raise SystemExit(1)


if not SOURCE.is_file():
    fail(f"Arquivo ReXGlue nao encontrado: {SOURCE}")

content = SOURCE.read_text(encoding="utf-8")

if MARKER in content:
    if OLD_ASSIGNMENT in content:
        fail("Patch Android marcado, mas o caminho antigo /system/bin/logs ainda existe.")
    print(f"Patch de logs Android ja aplicado e verificado em {SOURCE}.")
    raise SystemExit(0)

pattern = re.compile(
    r'^(?P<indent>[ \\t]*)log_config\\.log_dir\\s*=\\s*'
    r'\\(\\s*exe_dir\\s*/\\s*"logs"\\s*\\)\\.string\\(\\);[ \\t]*$',
    re.MULTILINE,
)
matches = list(pattern.finditer(content))

replacement_lines_template = [
    "// ANDROID_SAFE_LOG_DIR_PATCH: Android nao pode gravar em /system/bin.",
    "const auto& effective_user_dir = path_config.user_data_root;",
    "if (!effective_user_dir.empty()) {",
    '  log_config.log_dir = (effective_user_dir / "logs").string();',
    '} else if (!path_config.cache_root.empty()) {',
    '  log_config.log_dir = (path_config.cache_root / "logs").string();',
    '} else if (!path_config.config_path.empty() &&',
    '           !path_config.config_path.parent_path().empty()) {',
    '  log_config.log_dir =',
    '      (path_config.config_path.parent_path() / "logs").string();',
    '} else {',
    '  // Evita fallback para current_path()/logs em /system/bin.',
    '  log_config.app_name.clear();',
    '}',
]

if len(matches) == 1:
    indent = matches[0].group("indent")
    replacement = "\\n".join(indent + line for line in replacement_lines_template)
    content = pattern.sub(lambda _match: replacement, content, count=1)
elif len(matches) == 0:
    # O checkout pode conter a correção anterior do próprio repositório.
    # Nesse caso, marque-a somente se o caminho seguro já estiver presente.
    safe_assignment = "const auto& effective_user_dir = path_config.user_data_root;"
    if safe_assignment not in content:
        fail(
            "Nao foi encontrada a atribuicao antiga nem a correcao segura conhecida. "
            "Build interrompido para evitar APK sem correcao."
        )
    content = content.replace(
        safe_assignment,
        "// " + MARKER + ": caminho privado Android ja configurado.\\n" + safe_assignment,
        1,
    )
else:
    fail(
        'Foi encontrada mais de uma atribuicao log_config.log_dir = (exe_dir / "logs").string(); '
        f"em {SOURCE}: {len(matches)} ocorrencias."
    )

if MARKER not in content:
    fail("Validacao interna falhou: marcador do patch nao encontrado.")
if OLD_ASSIGNMENT in content:
    fail("Validacao falhou: atribuicao antiga continua no arquivo.")
if "path_config.user_data_root" not in content:
    fail("Validacao falhou: destino privado de logs nao foi configurado.")

SOURCE.write_text(content, encoding="utf-8")
print(f"Patch de logs Android aplicado e verificado em {SOURCE}.")
print("Diretorio de logs: user_data_root/logs, cache_root/logs ou config_path.parent/logs.")
