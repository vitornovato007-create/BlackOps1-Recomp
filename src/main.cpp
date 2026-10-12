// Entrada principal do BlackOps1-Recomp.

#include "generated/blackops1_init.h"
#include "blackops1_app.h"

// Registra a aplicação usando a classe BlackOps1App.
// A classe precisa implementar o método Create conforme
// a interface exigida pela versão instalada do ReXGlue.
REX_DEFINE_APP(blackops1, BlackOps1App::Create)
