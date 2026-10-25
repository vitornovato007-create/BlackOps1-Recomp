package com.blackops1.recomp;

import android.content.Context;
import android.os.Bundle;
import android.util.Log;
import android.widget.Toast;

import org.libsdl.app.SDLActivity;

/**
 * Somente o runtime vive aqui. O Manifest executa esta Activity em :runtime,
 * separado do processo da interface launcher.
 */
public final class GameActivity extends SDLActivity {
    private static final String TAG = "BlackOps1Runtime";

    @Override
    protected String[] getLibraries() {
        // A SDLActivity carrega primeiro a SDL e depois a biblioteca do jogo.
        return new String[] { "SDL3", "blackops1_android" };
    }

    @Override
    protected String getMainFunction() {
        return "SDL_main";
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        Log.i(TAG, "Solicitada inicialização do runtime BlackOps1/ReXGlue.");
        super.onCreate(savedInstanceState);
    }
}
