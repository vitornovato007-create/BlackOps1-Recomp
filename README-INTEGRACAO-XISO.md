# BlackOps1-Recomp — integração inicial do extract-xiso

Este patch NÃO inclui o fonte upstream `extract-xiso.c`; ele é mantido pelo projeto XboxDev e deve ser colocado em `third_party/extract-xiso/extract-xiso.c`.
Fonte: https://github.com/XboxDev/extract-xiso

## Antes de aplicar
1. Copie o arquivo `extract-xiso.c` do repositório upstream para `third_party/extract-xiso/extract-xiso.c`.
2. Preserve o `LICENSE.TXT` upstream em `third_party/extract-xiso/LICENSE.TXT`.
3. Aplique os arquivos deste ZIP mantendo os caminhos.
4. O CMake adiciona o fonte upstream ao alvo existente `blackops1_android`; ele não substitui o CMake ARM64 inteiro.
5. Compile no GitHub Actions e compartilhe o log se houver erro.

## Limitações desta etapa
- O Java abaixo usa um caminho de arquivo local. Um URI `content://` precisa ser copiado para cache pelo seletor Android antes da chamada.
- O bridge executa o modo de extração do extract-xiso via entry point renomeado. Essa integração precisa ser validada no NDK/Android; não afirmamos que já foi compilada.
- Esta etapa ainda não implementa a tela do launcher nem garante que a ISO corresponda à build recompilada.
