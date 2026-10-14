package com.blackops1.recomp;

import android.util.Log;
import org.libsdl.app.SDLActivity;

/** SDL3 activity: SDL starts the native entry point from windowed_app_main_sdl.cpp. */
public class MainActivity extends SDLActivity {
    private static final String TAG = "BlackOps1Recomp";

    static {
        System.loadLibrary("blackops1_android");
    }

    @Override
    protected String[] getLibraries() {
        // SDL3 must be loaded before the application library.
        return new String[] { "SDL3", "blackops1_android" };
    }

    public native String getNativeStatus();
    public native void nativeSetRuntimeStatus(String message);

    @Override
    protected void onResume() {
        super.onResume();
        Log.i(TAG, "Activity SDL retomada; o runtime nativo e iniciado pelo entrypoint SDL.");
    }
}
