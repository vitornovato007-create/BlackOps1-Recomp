#!/usr/bin/env python3
"""Apply and verify the Android-safe ReXGlue logging path after checkout."""

from pathlib import Path
import re
import sys

SOURCE = Path("rexglue-sdk/src/ui/rex_app.cpp")
MARKER = "ANDROID_SAFE_LOG_DIR_PATCH"

def fail(message: str) -> "None":
    print(f"::error::{message}", file=sys.stderr)
    raise SystemExit(1)

if not SOURCE.is_file():
    fail(f"Arquivo ReXGlue nao encontrado: {SOURCE}")

content = SOURCE.read_text(encoding="utf-8")

if MARKER in content:
    if 'log_config.log_dir = (exe_dir / "logs").string();' in content:
        fail("Patch Android marcado, mas o caminho antigo /system/bin/logs ainda existe.")
    print(f"Patch de logs Android ja aplicado e verificado em {SOURCE}.")
    raise SystemExit(0)

pattern = re.compile(
    r'^(?P<indent>[ \t]*)log_config\.log_dir\s*=\s*\(\s*exe_dir\s*/\s*"logs"\s*\)\.string\(\);[ \t]*$',
    re.MULTILINE,
)
matches = list(pattern.finditer(content))
if len(matches) != 1:
    fail(
        "Nao foi possivel identificar exatamente uma atribuicao "
        'log_config.log_dir = (exe_dir / "logs").string(); '
        f"em {SOURCE}; encontradas: {len(matches)}. Build interrompido para evitar APK sem correcao."
    )

indent = matches[0].group("indent")
replacement_lines = [
    f"{indent}// {MARKER}: Android nao pode gravar em /system/bin.",
    f"{indent}const auto& effective_user_dir = path_config.user_data_root;",
    f"{indent}if (!effective_user_dir.empty()) {{",
    f'{indent}  log_config.log_dir = (effective_user_dir / "logs").string();',
    f"{indent}}} else if (!path_config.cache_root.empty()) {{",
    f'{indent}  log_config.log_dir = (path_config.cache_root / "logs").string();',
    f"{indent}}} else if (!path_config.config_path.empty() &&",
    f"{indent}           !path_config.config_path.parent_path().empty()) {{",
    f"{indent}  log_config.log_dir =",
    f'{indent}      (path_config.config_path.parent_path() / "logs").string();',
    f"{indent}}} else {{",
    f"{indent}  // Evita que o logger tente usar current_path()/logs em /system/bin.",
    f"{indent}  log_config.app_name.clear();",
    f"{indent}}}",
]
content = pattern.sub("\\n".join(replacement_lines), content, count=1)

if MARKER not in content:
    fail("Validacao interna falhou: marcador do patch nao encontrado.")
if 'log_config.log_dir = (exe_dir / "logs").string();' in content:
    fail("Validacao falhou: atribuicao antiga continua no arquivo.")

SOURCE.write_text(content, encoding="utf-8")
print(f"Patch de logs Android aplicado e verificado em {SOURCE}.")
print("Diretorio de logs: user_data_root/logs, cache_root/logs ou config_path.parent/logs.")
