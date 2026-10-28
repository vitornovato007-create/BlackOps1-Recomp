# Auditoria e migração Android — BlackOps1-Recomp

## Objetivo

Separar o codegen do Black Ops 1 da integração do runtime Android. Um APK compilado não prova que o jogo inicia; a migração só estará validada após testes no dispositivo.

## Evidências verificadas

- `.github/workflows/build.yml` compila o ReXGlue host para Linux, executa `rexglue codegen blackops1_manifest.toml --force` e compila o executável Linux.
- `blackops1_manifest.toml` aponta para `game/default.xex` e para `generated`.
- A branch inspecionada contém fontes numerados `generated/sources/blackops1_recomp.0.cpp` a `.84.cpp`, cabeçalhos numerados e arquivos de inicialização/registro.
- `game/default.xex` não está versionado no checkout Git inspecionado. O workflow exige o arquivo no runner; sua ausência no Git não prova que ele não exista na cópia local do usuário.
- O workflow Android atual clona ReXGlue v0.10.0 e aplica o patch Android comunitário fixado, seguido de adaptações do projeto. Um erro recente foi causado por uma etapa nossa que sobrescrevia `include/rex/main_android.h` e removia declarações do patch; a correção já preserva o cabeçalho original.
- A referência [NFSMW-Recompiled-Mobile](https://github.com/victorgbd/NFSMW-Recompiled-Mobile) também prepara ReXGlue v0.10.0 por meio de um patch Android fixado e patches próprios versionados. Seu caminho Android Xenos não é simplesmente um SDK diferente que possa substituir o nosso sem adaptações.

## Decisão arquitetural inicial

**Manter o codegen do BO1 separado e preservar `build.yml`.** Não há evidência que justifique apagar ou reescrever esse workflow como parte da migração Android.

O diretório `nativo/sdk` da referência pertence a um caminho de motor nativo alternativo. Não deve ser trocado automaticamente pelo SDK Xenos do BO1: a seleção do motor altera fontes, backend gráfico e dependências.

A melhoria imediata é tornar a análise dos fontes gerados reproduzível e retirar gradualmente a lógica de patch inline do YAML para scripts versionados. O SDK e o patch comunitário precisam continuar com versões fixadas até que outra base seja comprovada. Não se deve copiar código de referência sem conferir a licença de cada parte; o repositório de referência declara GPL-3.0 no nível superior e o SDK contém um aviso BSD de três cláusulas.

## Auditoria de C++ gerado

`tools/auditar_codigo_gerado.py` verifica artefatos obrigatórios, sequência de fontes/cabeçalhos, arquivos vazios, bytes NUL, consistência entre `blackops1_register.cpp`, `blackops1_init.cpp` e funções `DEFINE_REX_FUNC`, includes locais e indícios heurísticos de APIs de plataforma.

```bash
python3 tools/auditar_codigo_gerado.py
python3 tools/auditar_codigo_gerado.py --json build-diagnostic/codigo-gerado.json --markdown build-diagnostic/codigo-gerado.md
python3 tools/auditar_codigo_gerado.py --strict
```

A auditoria estática não comprova a semântica das instruções recompiladas, a linkagem final nem a execução em Android. As heurísticas de APIs de plataforma são informativas, não falhas automáticas.

## Gates da migração

1. **Codegen:** manter `build.yml`; auditar os fontes antes/depois da geração e publicar relatórios. Não alterar o código gerado por tentativa.
2. **Preparação do SDK:** manter versão e patch fixados; mover alterações inline do `android.yml` para scripts em `tools/android/`. Cada script deve validar todas as âncoras antes de escrever, ser idempotente e verificar o resultado. Nunca sobrescrever cabeçalhos fornecidos pelo patch sem preservar as APIs originais.
3. **Ligação nativa:** manter código gerado em alvo próprio; ligar apenas uma instância do runtime. Não relincar OBJECT libraries já incorporadas ao runtime compartilhado. Validar SDL3, plugin Xenos e XISO de forma independente.
4. **APK:** verificar bibliotecas ARM64, SONAME/NEEDED, plugin, STL e alinhamento ELF/ZIP de 16 KiB.
5. **Dispositivo:** confirmar em sequência Activity/JNI, contexto Android, armazenamento privado, SDL3, superfície Vulkan, criação do app ReXGlue, `BlackOps1App::OnInitialize`, loop principal e primeira imagem.
6. **Conclusão:** somente declarar migração pronta depois que o BO1 iniciar no dispositivo. Nenhum workflow foi disparado durante esta auditoria.

## Limitações atuais

- O codegen completo não foi reexecutado nesta branch.
- O C++ gerado ainda precisa passar pela auditoria automática e pela compilação Android.
- O runtime Vulkan e a inicialização real do BO1 ainda não foram confirmados em dispositivo.
- O arquivo XEX não deve ser adicionado a commits públicos junto com assets ou artefatos privados sem autorização e revisão de licenças.

A branch de trabalho anterior é preservada; `BlackOps1-XenonRecomp` não faz parte desta migração.
