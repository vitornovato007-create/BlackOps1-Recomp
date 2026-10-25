package com.blackops1.recomp.importer;

import android.content.ContentResolver;
import android.content.Context;
import android.net.Uri;
import android.os.ParcelFileDescriptor;
import android.util.Log;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Prepara a ISO selecionada pelo usuário sem carregar o arquivo inteiro na RAM.
 * O extrator XISO nativo recebe um caminho local, portanto a imagem é copiada
 * em blocos para uma área temporária e extraída para files/blackops1, diretório
 * configurado como game_data_root pelo runtime ReXGlue.
 */
public final class IsoImportManager {
    private static final String TAG = "BlackOps1Import";
    private static final int BUFFER_SIZE = 1024 * 1024;
    private static final ExecutorService EXECUTOR = Executors.newSingleThreadExecutor();

    public interface Callback {
        void onProgress(String message, long copiedBytes, long totalBytes);
        void onComplete(File gameDirectory, String message);
        void onError(String message, Throwable error);
    }

    private IsoImportManager() {}

    public static void importIso(Context context, Uri uri, Callback callback) {
        final Context app = context.getApplicationContext();
        EXECUTOR.execute(() -> {
            File staging = null;
            File gameDir = new File(app.getFilesDir(), "blackops1");
            try {
                ContentResolver resolver = app.getContentResolver();
                File root = new File(app.getFilesDir(), "game-import");
                if (!root.exists() && !root.mkdirs()) {
                    throw new IOException("Não foi possível criar a pasta temporária de importação.");
                }
                staging = new File(root, "selected.iso.part");
                File iso = new File(root, "selected.iso");

                long total = -1;
                try (ParcelFileDescriptor pfd = resolver.openFileDescriptor(uri, "r")) {
                    if (pfd != null) total = pfd.getStatSize();
                } catch (Exception ignored) {
                    // Nem todos os provedores de documentos informam o tamanho antecipadamente.
                }

                long copied = 0;
                try (InputStream in = resolver.openInputStream(uri);
                     FileOutputStream out = new FileOutputStream(staging, false)) {
                    if (in == null) throw new IOException("O Android não conseguiu abrir a ISO selecionada.");
                    byte[] buffer = new byte[BUFFER_SIZE];
                    int n;
                    while ((n = in.read(buffer)) != -1) {
                        out.write(buffer, 0, n);
                        copied += n;
                        if (callback != null) callback.onProgress("Copiando ISO para preparar a extração…", copied, total);
                    }
                    out.getFD().sync();
                }

                if (copied < 1024L * 1024L) {
                    throw new IOException("O arquivo selecionado é pequeno demais para uma ISO de jogo.");
                }
                if (iso.exists() && !iso.delete()) {
                    throw new IOException("Não foi possível substituir a ISO temporária anterior.");
                }
                if (!staging.renameTo(iso)) {
                    throw new IOException("Não foi possível finalizar a cópia temporária da ISO.");
                }

                if (!NativeXisoBridge.isAvailable()) {
                    throw new IOException("O extrator XISO nativo não está disponível nesta compilação.");
                }
                if (gameDir.exists()) deleteTree(gameDir);
                if (!gameDir.mkdirs()) {
                    throw new IOException("Não foi possível criar a pasta de destino da extração.");
                }

                int result = NativeXisoBridge.extract(iso.getAbsolutePath(), gameDir.getAbsolutePath(), true);
                if (result != 0) {
                    deleteTree(gameDir);
                    throw new IOException("O extrator XISO falhou (código " + result + "). Verifique se a imagem é uma ISO XGD/XISO compatível.");
                }

                File defaultXex = new File(gameDir, "default.xex");
                if (!defaultXex.isFile()) {
                    throw new IOException("A extração terminou, mas não foi encontrado default.xex na raiz da pasta extraída.");
                }
                if (callback != null) {
                    callback.onComplete(gameDir, "Importação concluída.");
                }
            } catch (Throwable t) {
                if (staging != null && staging.exists()) staging.delete();
                Log.e(TAG, "Falha ao importar ISO", t);
                if (callback != null) {
                    callback.onError(t.getMessage() == null ? "Falha ao importar a ISO." : t.getMessage(), t);
                }
            }
        });
    }

    private static void deleteTree(File file) {
        if (file == null || !file.exists()) return;
        File[] children = file.listFiles();
        if (children != null) for (File child : children) deleteTree(child);
        //noinspection ResultOfMethodCallIgnored
        file.delete();
    }
}
