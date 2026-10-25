package com.blackops1.recomp;

import android.os.Bundle;
import android.util.Log;

import org.libsdl.app.SDLActivity;

/**
 * Inicialização do runtime em processo separado. Nenhum controle de toque é
 * necessário para que esta Activity tente inicializar SDL/ReXGlue.
 */
public final class GameActivity extends SDLActivity {
    private static final String TAG = "BlackOps1Runtime";

    @Override
    protected String[] getLibraries() {
        return new String[] { "SDL3", "blackops1_android" };
    }

    @Override
    protected String getMainFunction() {
        return "SDL_main";
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        DiagnosticLog.info(this, "GameActivity.onCreate: iniciando runtime; processo=" + android.os.Process.myPid());
        Thread.setDefaultUncaughtExceptionHandler((thread, error) -> {
            DiagnosticLog.error(getApplicationContext(),
                    "EXCEÇÃO NÃO CAPTURADA NO RUNTIME; thread=" + thread.getName(), error);
            Log.e(TAG, "Exceção não capturada no runtime", error);
            // Encaminha para o handler anterior para manter o comportamento normal do Android.
            android.os.Process.killProcess(android.os.Process.myPid());
            System.exit(10);
        });
        try {
            super.onCreate(savedInstanceState);
            DiagnosticLog.info(this, "SDLActivity.onCreate retornou; SDL3/runtime solicitado.");
        } catch (Throwable t) {
            DiagnosticLog.error(this, "Falha Java ao criar GameActivity/SDLActivity.", t);
            throw t;
        }
    }

    @Override
    protected void onResume() {
        DiagnosticLog.info(this, "GameActivity.onResume.");
        super.onResume();
    }

    @Override
    protected void onDestroy() {
        DiagnosticLog.info(this, "GameActivity.onDestroy; isFinishing=" + isFinishing());
        super.onDestroy();
    }
}
