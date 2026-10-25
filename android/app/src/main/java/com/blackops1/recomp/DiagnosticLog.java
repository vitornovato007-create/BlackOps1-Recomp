package com.blackops1.recomp;

import android.content.Context;
import android.util.Log;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

/** Registro persistente de diagnóstico do launcher, importador e runtime. */
public final class DiagnosticLog {
    private static final String TAG = "BlackOps1Diag";
    private static final Object LOCK = new Object();
    private DiagnosticLog() {}

    public static File getFile(Context context) {
        File dir = new File(context.getApplicationContext().getFilesDir(), "logs");
        if (!dir.exists()) dir.mkdirs();
        return new File(dir, "blackops1-diagnostics.txt");
    }

    public static void info(Context context, String message) {
        append(context, "INFO", message, null);
    }

    public static void error(Context context, String message, Throwable error) {
        append(context, "ERROR", message, error);
    }

    private static void append(Context context, String level, String message, Throwable error) {
        String time = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSS", Locale.US).format(new Date());
        StringBuilder entry = new StringBuilder()
                .append('[').append(time).append("] [").append(level).append("] ")
                .append(message == null ? "(sem mensagem)" : message).append('\n');
        if (error != null) {
            entry.append(Log.getStackTraceString(error)).append('\n');
            Log.e(TAG, message, error);
        } else if ("ERROR".equals(level)) {
            Log.e(TAG, String.valueOf(message));
        } else {
            Log.i(TAG, String.valueOf(message));
        }
        synchronized (LOCK) {
            File file = getFile(context);
            try (FileOutputStream out = new FileOutputStream(file, true)) {
                out.write(entry.toString().getBytes(StandardCharsets.UTF_8));
                out.flush();
            } catch (IOException e) {
                Log.e(TAG, "Não foi possível gravar o log em arquivo", e);
            }
        }
    }

    public static String readAll(Context context) throws IOException {
        File file = getFile(context);
        if (!file.exists()) return "BlackOps1-Recomp - Diagnóstico\nNenhum evento registrado ainda.\n";
        byte[] data = java.nio.file.Files.readAllBytes(file.toPath());
        return new String(data, StandardCharsets.UTF_8);
    }
}
