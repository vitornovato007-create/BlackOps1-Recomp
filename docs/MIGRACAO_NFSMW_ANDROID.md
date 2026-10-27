# Migração controlada a partir do NFSMW Android Evolved

Este documento registra quais práticas de integração Android foram adotadas como referência para
BlackOps1-Recomp e quais partes não devem ser copiadas diretamente.

## Referência e escopo

- Referência técnica: [NFSMW Android Evolved](https://github.com/codepdbh/nfsmw-android).
- A referência compila código nativo ARM64 com SDL3/ReXGlue e usa CMake/Gradle para empacotar o APK.
- O BlackOps1-Recomp mantém seu próprio launcher, importação de ISO/XISO, validação de arquivos,
  classe `GameActivity`, ponte JNI e configuração do runtime Black Ops 1.
- A referência usa lógica, shaders, formatos de assets e código de jogo próprios do Need for Speed.
  Esses componentes não são substitutos do executável recompilado nem do backend Xenos do BO1.

## Práticas incorporadas nesta etapa

1. **Compatibilidade com páginas Android de 16 KiB:** os alvos nativos do runtime BO1, SDL3 e
   extrator XISO recebem `-Wl,-z,max-page-size=16384`, seguindo a estratégia de build usada pela
   referência Android.
2. **Verificação do artefato real:** o workflow agora inspeciona os segmentos ELF dentro do APK
   final, em vez de confiar apenas em que Gradle terminou sem erros.
3. **Separação de runtime e launcher:** mantemos a Activity leve do launcher e iniciamos SDL3/ReXGlue
   somente em `GameActivity`, depois da seleção/importação do jogo.
4. **Logs persistentes:** mantemos `DiagnosticLog.java` e os marcadores nativos `[BO1-STAGE]`.
   O log deve continuar distinguindo falha de importação, inicialização SDL, configuração do runtime
   e execução do jogo.

## O que fica deliberadamente fora desta migração

- Não copiar o renderizador Vulkan, o código de shaders ou os hooks de Need for Speed.
- Não exigir descriptor indexing apenas porque o renderizador do NFS o exige; as capacidades devem
  ser verificadas contra o backend Xenos/ReXGlue realmente usado pelo BO1.
- Não copiar arquivos de jogo, executáveis, shaders derivados ou assets proprietários.
- Não adicionar controles de toque; o objetivo atual é estabilizar o runtime e preservar o suporte
  a controles físicos existente no SDL.

## Licenças e atribuição

A referência NFSMW Android Evolved declara o projeto sob GPL-3.0 e identifica o SDK ReXGlue como
BSD-3-Clause em seu arquivo `THIRD_PARTY_NOTICES.md`. Esta etapa usa a referência para orientar
configuração e validação de build; não importa arquivos-fonte do renderizador ou da lógica de jogo
do NFS. As dependências já utilizadas pelo BlackOps1-Recomp mantêm suas próprias licenças e avisos;
consulte os avisos upstream correspondentes antes de redistribuir binários.

Se futuramente for copiado/adaptado qualquer arquivo-fonte GPL do NFSMW Android Evolved, esse arquivo
deverá manter os avisos de copyright/licença upstream e a distribuição do trabalho derivado deverá
cumprir a GPL-3.0. Não remover nem substituir os avisos de licenças de terceiros.

## Validação

A compilação CI comprova apenas que o APK pode ser montado. A auditoria ELF desta etapa verifica
somente o alinhamento dos segmentos das bibliotecas nativas críticas. Ela não comprova que o BO1
chegou ao menu ou que a GPU do dispositivo executa o jogo corretamente; isso continua exigindo teste
no aparelho e análise do log exportado.
