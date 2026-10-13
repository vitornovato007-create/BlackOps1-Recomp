# Estado da integração Android — BlackOps1-Recomp

Esta alteração corrige problemas reais de estrutura, mas não deve ser confundida com um port Android completo.

## Correções incluídas

1. `.github/workflows/build.yml`: corrigida a indentação YAML do workflow Linux para que os eventos, permissões, job e etapas fiquem sob os níveis corretos.
2. `android/app/src/main/cpp/CMakeLists.txt`: corrigido o cálculo da raiz do repositório. O caminho anterior subia um nível a mais, impedindo que `generated/` fosse encontrado corretamente.
3. `android/app/src/main/cpp/native-lib.cpp`: o nome exportado JNI agora corresponde ao método `getNativeStatus()` declarado em `MainActivity.java`.
4. Mantido o workflow Android separado para construir o APK de diagnóstico e anexar relatórios/logs.

## O que ainda falta para iniciar o jogo no Android

- Aplicar e validar os patches de Android ARM64 no SDK ReXGlue. A referência NFSMW-RECOMP usa um SDK preparado para Android, não apenas o SDK Linux genérico.
- Criar uma aplicação/host Android que inicialize o runtime e forneça a superfície de janela/swapchain Vulkan, ciclo de vida, entrada e áudio.
- Incorporar as fontes geradas do Black Ops 1 à biblioteca nativa, usando os targets e a API de inicialização reais da versão de ReXGlue utilizada.
- Resolver as chamadas externas e os requisitos específicos do título identificados pelo codegen.
- Testar no hardware de destino; o projeto de referência foi validado principalmente em Snapdragon/Adreno, enquanto este alvo é Exynos/Mali.

## Importante sobre dados do jogo

Não mantenha `game/default.xex`, ISOs, código C++ gerado a partir do executável ou APKs com código do jogo em um repositório público. Guarde o XEX localmente e forneça-o apenas em um ambiente de build privado e controlado. O workflow Linux atual depende de `game/default.xex` para executar o codegen; sem esse arquivo, a etapa de geração deve falhar claramente.

## Referência técnica

O fluxo Android descrito em `WINDROID-EMU/NFSMW-RECOMP/docs/android.md` separa a preparação/patch do SDK, a geração do código e a compilação Gradle. O BlackOps1-Recomp precisa de um port equivalente, adaptado ao seu código e às APIs reais do SDK. Copiar somente o `build.yml` dessa referência não produz a integração.
