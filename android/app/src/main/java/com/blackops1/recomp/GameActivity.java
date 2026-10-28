package com.blackops1.recomp;

import android.net.Uri;
import android.os.Bundle;
import android.os.ParcelFileDescriptor;
import android.util.Log;


import org.libsdl.app.SDLActivity;

/**
 * Inicialização do runtime em processo separado. Nenhum controle de toque é
 * necessário para que esta Activity tente inicializar SDL/ReXGlue.
 */
public final class GameActivity extends SDLActivity {
    private static final String TAG = "BlackOps1Runtime";

    // The native ReXGlue Android bridge resolves this method through JNI.
    // The current launcher extracts the ISO to a normal folder, but keeping
    // the bridge available also supports content:// paths without a JNI lookup
    // failure during Android context initialization.
    private static volatile GameActivity currentInstance;

    public static ParcelFileDescriptor openContentFd(String uriText, String mode) {
        GameActivity activity = currentInstance;
        if (activity == null || uriText == null || uriText.isEmpty()) {
            return null;
        }

        Uri uri = Uri.parse(uriText);
        String openMode = (mode != null && mode.contains("w")) ? "w" : "r";
        try {
            return activity.getContentResolver().openFileDescriptor(uri, openMode);
        } catch (Exception error) {
            Log.w(TAG, "Nao foi possivel abrir URI Android pelo ContentResolver: " + uri, error);
            return null;
        }
    }

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
        currentInstance = this;
        DiagnosticLog.info(this, "GameActivity.onCreate: iniciando runtime; processo=" + android.os.Process.myPid());
        Thread.UncaughtExceptionHandler previousHandler = Thread.getDefaultUncaughtExceptionHandler();
        Thread.setDefaultUncaughtExceptionHandler((thread, error) -> {
            DiagnosticLog.error(getApplicationContext(),
                    "EXCEÇÃO NÃO CAPTURADA NO RUNTIME; thread=" + thread.getName(), error);
            Log.e(TAG, "Exceção não capturada no runtime", error);
            // Mantém o handler padrão do Android para que o sistema registre o crash.
            if (previousHandler != null) {
                previousHandler.uncaughtException(thread, error);
            } else {
                android.os.Process.killProcess(android.os.Process.myPid());
                System.exit(10);
            }
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
        if (currentInstance == this) {
            currentInstance = null;
        }
    }
}
