package com.blackops1.recomp;

import android.content.Context;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** Valida uma pasta de jogo existente sem copiar ou alterar seus arquivos. */
public final class GameFolderValidator {
    private static final ExecutorService EXECUTOR = Executors.newSingleThreadExecutor();

    public interface Callback {
        void onProgress(String message, int checked, int total);
        void onComplete(File folder, int count, String message);
        void onError(String message, Throwable error);
    }

    private GameFolderValidator() {}

    public static void validate(Context context, File folder, Callback callback) {
        final Context app = context.getApplicationContext();
        EXECUTOR.execute(() -> {
            try {
                DiagnosticLog.info(app, "Validador de pasta: início; raiz=" + folder.getAbsolutePath());
                File root = folder.getCanonicalFile();
                if (!root.isDirectory() || !root.canRead()) {
                    throw new IOException("A pasta do jogo não pode ser lida.");
                }
                File defaultXex = new File(root, "default.xex");
                if (!defaultXex.isFile() || !defaultXex.canRead() || defaultXex.length() <= 0) {
                    throw new IOException("default.xex precisa existir, ser legível e ter tamanho maior que zero na raiz da pasta.");
                }
                List<File> files = new ArrayList<>();
                collect(root, files);
                if (files.isEmpty()) throw new IOException("A pasta selecionada não contém arquivos legíveis.");
                int checked = 0;
                for (File file : files) {
                    String relative = root.toURI().relativize(file.toURI()).getPath();
                    if (!file.isFile() || !file.canRead()) {
                        throw new IOException("Arquivo ilegível ou indisponível: " + relative);
                    }
                    if (file.getName().equalsIgnoreCase("default.xex") && file.length() <= 0) {
                        throw new IOException("Foi encontrado um default.xex vazio: " + relative);
                    }
                    checked++;
                    String message = "Verificado " + checked + "/" + files.size() + ": " + relative
                            + " (" + file.length() + " bytes)";
                    DiagnosticLog.info(app, "PASTA " + message);
                    if (callback != null) callback.onProgress(message, checked, files.size());
                }
                if (callback != null) callback.onComplete(root, checked,
                        "Validação estrutural concluída: " + checked + " arquivos legíveis. Nenhum arquivo foi copiado.");
            } catch (Throwable t) {
                DiagnosticLog.error(app, "Validação da pasta falhou: " + t.getMessage(), t);
                if (callback != null) callback.onError(
                        t.getMessage() == null ? "Não foi possível validar a pasta." : t.getMessage(), t);
            }
        });
    }

    private static void collect(File directory, List<File> output) throws IOException {
        File[] children = directory.listFiles();
        if (children == null) throw new IOException("Não foi possível listar a pasta: " + directory.getAbsolutePath());
        for (File child : children) {
            if (child.isDirectory()) collect(child, output);
            else if (child.isFile()) output.add(child);
        }
    }
}
