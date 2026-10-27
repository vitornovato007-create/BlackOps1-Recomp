# Avisos de terceiros

Este repositório integra componentes de software com licenças próprias. Não se deve interpretar
este documento como substituto das licenças e avisos distribuídos pelos respectivos projetos.

| Componente | Uso neste projeto | Licença/aviso |
|---|---|---|
| ReXGlue SDK | Runtime Xbox 360, sistema de arquivos, subsistemas de kernel, UI e backend Xenos | BSD-3-Clause; preservar o arquivo LICENSE do checkout upstream usado na compilação |
| SDL3 | Activity Android, janela, eventos, áudio e integração de plataforma | zlib; preservar avisos upstream |
| extract-xiso | Extração de conteúdo de ISO/XISO fornecido pelo usuário | Verificar e preservar o aviso de licença da versão upstream usada |
| NFSMW Android Evolved | Referência técnica para integração Android/SDL3, configuração de build e compatibilidade de páginas de memória | Projeto upstream declara GPL-3.0; nesta etapa não foram importados seus arquivos-fonte de renderização ou lógica específica do jogo |

Os arquivos gerados a partir de `default.xex` e os dados do jogo devem continuar fora do repositório.
Este projeto não deve distribuir executáveis, ISOs, chaves, assets ou outros dados proprietários do jogo.

Quando um arquivo de terceiros for copiado para este repositório no futuro, registre aqui o arquivo,
a origem, o titular dos direitos autorais e a licença aplicável, e mantenha o cabeçalho de licença
original. Não conclua que todo arquivo tem a mesma licença apenas porque está no mesmo repositório.
