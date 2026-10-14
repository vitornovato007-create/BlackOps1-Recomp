
package com.blackops1.recomp;

import org.libsdl.app.SDLActivity;

/**
 * Activity principal do BlackOps1-Recomp.
 *
 * O SDL3 cuida da janela, da superfície gráfica e da entrada.
 * A biblioteca blackops1_android contém o código nativo do projeto.
 */
public class MainActivity extends SDLActivity {

    @Override
    protected String[] getLibraries() {
        // A SDLActivity carrega as bibliotecas nesta ordem.
        // SDL3 precisa ser carregada antes da biblioteca do jogo.
        return new String[] {
            "SDL3",
            "blackops1_android"
        };
    }

    @Override
    protected String getMainFunction() {
        // Ponto de entrada SDL esperado pela SDLActivity.
        return "SDL_main";
    }
}
