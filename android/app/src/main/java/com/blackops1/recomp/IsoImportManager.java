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
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Copia a ISO, extrai-a e faz uma validação estrutural dos arquivos extraídos.
 * O progresso de cópia e de validação é mensurável. O extrator nativo atual
 * não expõe callbacks de progresso, portanto a fase de extração usa spinner.
 */
public final class IsoImportManager {
    private static final String TAG = "BlackOps1Import";
    private static final int BUFFER_SIZE = 1024 * 1024;
    private static final ExecutorService EXECUTOR = Executors.newSingleThreadExecutor();

    public interface Callback {
        /** totalBytes > 0 significa progresso mensurável; caso contrário a fase é indeterminada. */
        void onProgress(String message, long processed, long total);
        void onComplete(File gameDirectory, String message);
        void onError(String message, Throwable error);
    }

    private IsoImportManager() {}

    public static void importIso(Context context, Uri uri, Callback callback) {
        final Context app = context.getApplicationContext();
        EXECUTOR.execute(() -> {
            File staging = null;
            File iso = null;
            File gameDir = new File(app.getFilesDir(), "blackops1");
            try {
                ContentResolver resolver = app.getContentResolver();
                File root = new File(app.getFilesDir(), "game-import");
                if (!root.exists() && !root.mkdirs()) {
                    throw new IOException("Não foi possível criar a pasta temporária de importação.");
                }
                staging = new File(root, "selected.iso.part");
                iso = new File(root, "selected.iso");

                long total = -1;
                try (ParcelFileDescriptor pfd = resolver.openFileDescriptor(uri, "r")) {
                    if (pfd != null) total = pfd.getStatSize();
                } catch (Exception ignored) {
                    // Alguns provedores não informam o tamanho antecipadamente.
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
                        if (callback != null) callback.onProgress("Copiando ISO", copied, total);
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
                staging = null;

                if (!NativeXisoBridge.isAvailable()) {
                    throw new IOException("O extrator XISO nativo não está disponível nesta compilação.");
                }
                if (gameDir.exists() && !deleteTree(gameDir)) {
                    throw new IOException("Não foi possível limpar a extração anterior.");
                }
                if (!gameDir.mkdirs()) {
                    throw new IOException("Não foi possível criar a pasta de destino da extração.");
                }

                if (callback != null) callback.onProgress("Extraindo conteúdo da ISO…", 0, 0);
                int result = NativeXisoBridge.extract(iso.getAbsolutePath(), gameDir.getAbsolutePath(), true);
                if (result != 0) {
                    throw new IOException("O extrator XISO falhou (código " + result + "). Verifique se a imagem é uma ISO XGD/XISO compatível.");
                }

                if (callback != null) callback.onProgress("Contando arquivos extraídos…", 0, 0);
                List<File> files = new ArrayList<>();
                collectFiles(gameDir, files);
                if (files.isEmpty()) {
                    throw new IOException("A extração não produziu arquivos. A ISO pode ser incompatível ou inválida.");
                }

                int checked = 0;
                for (File file : files) {
                    String relative = gameDir.toURI().relativize(file.toURI()).getPath();
                    if (!file.isFile() || !file.canRead()) {
                        throw new IOException("Falha na validação: arquivo ausente ou ilegível: " + relative);
                    }
                    // Arquivos vazios podem existir legitimamente; apenas o executável é exigido como não vazio.
                    if ("default.xex".equalsIgnoreCase(file.getName()) && file.length() <= 0) {
                        throw new IOException("O arquivo default.xex está vazio.");
                    }
                    checked++;
                    if (callback != null) callback.onProgress(
                            "Validando " + relative + " (" + checked + "/" + files.size() + ")",
                            checked, files.size());
                }

                File defaultXex = new File(gameDir, "default.xex");
                if (!defaultXex.isFile() || !defaultXex.canRead() || defaultXex.length() <= 0) {
                    throw new IOException("Validação reprovada: default.xex não foi encontrado na raiz ou está vazio/ilegível.");
                }

                if (callback != null) callback.onProgress(
                        "Validação estrutural concluída: " + checked + " arquivos verificados",
                        checked, files.size());
                if (callback != null) callback.onComplete(gameDir,
                        "ISO extraída; " + checked + " arquivos verificados. A validação é estrutural, não uma verificação de hash oficial.");
            } catch (Throwable t) {
                Log.e(TAG, "Falha ao importar ou validar ISO", t);
                if (callback != null) callback.onError(
                        t.getMessage() == null ? "Falha ao importar a ISO." : t.getMessage(), t);
            }
        });
    }

    private static void collectFiles(File directory, List<File> output) throws IOException {
        File[] children = directory.listFiles();
        if (children == null) throw new IOException("Não foi possível ler o diretório extraído: " + directory.getName());
        for (File child : children) {
            if (child.isDirectory()) {
                collectFiles(child, output);
            } else if (child.isFile()) {
                output.add(child);
            }
        }
    }

    private static boolean deleteTree(File file) {
        if (file == null || !file.exists()) return true;
        File[] children = file.listFiles();
        if (children != null) {
            for (File child : children) {
                if (!deleteTree(child)) return false;
            }
        }
        return file.delete();
    }
}
