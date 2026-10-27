package com.blackops1.recomp;

import android.app.Activity;
import android.app.ActivityManager;
import android.app.ApplicationExitInfo;
import android.app.AlertDialog;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Bundle;
import android.os.Environment;
import android.provider.DocumentsContract;
import android.provider.Settings;
import android.provider.OpenableColumns;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import com.blackops1.recomp.importer.IsoImportManager;

import java.io.File;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.util.List;

/**
 * Launcher Android. Esta Activity NÃO herda de SDLActivity e não inicia o runtime.
 * A SDL/ReXGlue só é carregada em GameActivity depois que o usuário toca em Jogar.
 */
public final class MainActivity extends Activity {
    private static final int REQUEST_ISO = 4101;
    private static final int REQUEST_EXPORT_LOG = 4102;
    private static final int REQUEST_FOLDER = 4103;
    private static final String PREFS = "blackops1_launcher";
    private static final String KEY_URI = "selected_iso_uri";
    private static final String KEY_NAME = "selected_iso_name";
    private static final String KEY_FOLDER_PATH = "selected_game_folder_path";
    private static final String RUNTIME_ROOT_FILE = "runtime-game-root.txt";

    private final int bg = Color.rgb(13, 16, 18);
    private final int panel = Color.rgb(25, 30, 31);
    private final int accent = Color.rgb(190, 157, 82);
    private final int text = Color.rgb(238, 236, 226);
    private final int muted = Color.rgb(158, 164, 158);

    private TextView isoName;
    private TextView status;
    private TextView statusDetail;
    private TextView diagnosticView;
    private ProgressBar progress;
    private Button playButton;
    private Button selectButton;
    private Button selectFolderButton;
    private boolean importing;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().setStatusBarColor(bg);
        getWindow().setNavigationBarColor(bg);
        getWindow().getDecorView().setSystemUiVisibility(0);
        buildInterface();
        collectPreviousProcessExitInfo();
        refreshSavedGame();
        DiagnosticLog.info(this, "Launcher aberto; Android " + android.os.Build.VERSION.RELEASE + ", API " + android.os.Build.VERSION.SDK_INT);
        refreshDiagnosticView();
    }

    private void buildInterface() {
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(bg);

        LinearLayout page = new LinearLayout(this);
        page.setOrientation(LinearLayout.VERTICAL);
        page.setPadding(dp(22), dp(24), dp(22), dp(24));
        page.setGravity(Gravity.CENTER_HORIZONTAL);
        scroll.addView(page, new ScrollView.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        TextView eyebrow = new TextView(this);
        eyebrow.setText("RECOMPILATION PROJECT  /  ANDROID ARM64");
        eyebrow.setTextColor(accent);
        eyebrow.setTextSize(11);
        eyebrow.setTypeface(Typeface.MONOSPACE, Typeface.BOLD);
        eyebrow.setLetterSpacing(0.08f);
        page.addView(eyebrow, matchWrap());

        TextView title = new TextView(this);
        title.setText("BLACK OPS");
        title.setTextColor(text);
        title.setTextSize(38);
        title.setTypeface(Typeface.create("sans-serif-condensed", Typeface.BOLD));
        title.setLetterSpacing(0.04f);
        LinearLayout.LayoutParams titleLp = matchWrap();
        titleLp.topMargin = dp(8);
        page.addView(title, titleLp);

        TextView subtitle = new TextView(this);
        subtitle.setText("CALL OF DUTY  •  RECOMPILED");
        subtitle.setTextColor(muted);
        subtitle.setTextSize(12);
        subtitle.setTypeface(Typeface.MONOSPACE, Typeface.NORMAL);
        LinearLayout.LayoutParams subLp = matchWrap();
        subLp.bottomMargin = dp(22);
        page.addView(subtitle, subLp);

        LinearLayout hero = new LinearLayout(this);
        hero.setOrientation(LinearLayout.VERTICAL);
        hero.setPadding(dp(18), dp(18), dp(18), dp(18));
        hero.setBackground(roundRect(panel, dp(12), Color.rgb(57, 62, 56)));
        page.addView(hero, matchWrap());

        TextView label = new TextView(this);
        label.setText("GAME SETUP");
        label.setTextColor(accent);
        label.setTextSize(11);
        label.setTypeface(Typeface.MONOSPACE, Typeface.BOLD);
        hero.addView(label, matchWrap());

        TextView instructions = new TextView(this);
        instructions.setText("Escolha uma ISO para extrair ou selecione uma pasta comum que já contenha os arquivos do jogo. A pasta selecionada será usada diretamente, sem copiar o conteúdo.");
        instructions.setTextColor(text);
        instructions.setTextSize(15);
        instructions.setLineSpacing(dp(3), 1.0f);
        LinearLayout.LayoutParams instLp = matchWrap();
        instLp.topMargin = dp(10);
        hero.addView(instructions, instLp);

        isoName = new TextView(this);
        isoName.setText("Nenhuma ISO ou pasta selecionada");
        isoName.setTextColor(muted);
        isoName.setTextSize(13);
        isoName.setMaxLines(3);
        isoName.setPadding(dp(12), dp(12), dp(12), dp(12));
        isoName.setBackground(roundRect(Color.rgb(16, 20, 20), dp(8), Color.rgb(50, 56, 51)));
        LinearLayout.LayoutParams isoLp = matchWrap();
        isoLp.topMargin = dp(16);
        hero.addView(isoName, isoLp);

        selectButton = makeButton("SELECIONAR ISO", false);
        LinearLayout.LayoutParams selectLp = matchWrap();
        selectLp.topMargin = dp(14);
        hero.addView(selectButton, selectLp);
        selectButton.setOnClickListener(v -> chooseIso());

        selectFolderButton = makeButton("SELECIONAR PASTA DO JOGO", false);
        LinearLayout.LayoutParams folderLp = matchWrap();
        folderLp.topMargin = dp(8);
        hero.addView(selectFolderButton, folderLp);
        selectFolderButton.setOnClickListener(v -> chooseGameFolder());

        progress = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        progress.setMax(100);
        progress.setVisibility(View.GONE);
        LinearLayout.LayoutParams progressLp = matchWrap();
        progressLp.topMargin = dp(12);
        hero.addView(progress, progressLp);

        status = new TextView(this);
        status.setText("AGUARDANDO ARQUIVO");
        status.setTextColor(accent);
        status.setTextSize(11);
        status.setTypeface(Typeface.MONOSPACE, Typeface.BOLD);
        LinearLayout.LayoutParams statusLp = matchWrap();
        statusLp.topMargin = dp(14);
        hero.addView(status, statusLp);

        statusDetail = new TextView(this);
        statusDetail.setText("O runtime do jogo permanece fechado até você tocar em Jogar.");
        statusDetail.setTextColor(muted);
        statusDetail.setTextSize(12);
        statusDetail.setLineSpacing(dp(2), 1.0f);
        LinearLayout.LayoutParams detailLp = matchWrap();
        detailLp.topMargin = dp(5);
        hero.addView(statusDetail, detailLp);

        playButton = makeButton("JOGAR", true);
        LinearLayout.LayoutParams playLp = matchWrap();
        playLp.topMargin = dp(18);
        hero.addView(playButton, playLp);
        playButton.setEnabled(false);
        playButton.setOnClickListener(v -> launchRuntime());

        Button exportLogButton = makeButton("EXPORTAR LOG TXT", false);
        LinearLayout.LayoutParams exportLp = matchWrap();
        exportLp.topMargin = dp(10);
        hero.addView(exportLogButton, exportLp);
        exportLogButton.setOnClickListener(v -> exportDiagnosticLog());

        TextView diagTitle = new TextView(this);
        diagTitle.setText("DIAGNÓSTICO REAL");
        diagTitle.setTextColor(accent);
        diagTitle.setTextSize(11);
        diagTitle.setTypeface(Typeface.MONOSPACE, Typeface.BOLD);
        LinearLayout.LayoutParams diagTitleLp = matchWrap();
        diagTitleLp.topMargin = dp(14);
        hero.addView(diagTitle, diagTitleLp);

        diagnosticView = new TextView(this);
        diagnosticView.setText("Aguardando eventos de diagnóstico…");
        diagnosticView.setTextColor(muted);
        diagnosticView.setTextSize(10);
        diagnosticView.setTypeface(Typeface.MONOSPACE, Typeface.NORMAL);
        diagnosticView.setMaxLines(12);
        diagnosticView.setTextIsSelectable(true);
        diagnosticView.setPadding(dp(10), dp(10), dp(10), dp(10));
        diagnosticView.setBackground(roundRect(Color.rgb(16, 20, 20), dp(8), Color.rgb(50, 56, 51)));
        LinearLayout.LayoutParams diagLp = matchWrap();
        diagLp.topMargin = dp(6);
        hero.addView(diagnosticView, diagLp);

        TextView footer = new TextView(this);
        footer.setText("BLACKOPS1-RECOMP  •  EXPERIMENTAL BUILD\nÉ necessário possuir uma imagem de jogo compatível.");
        footer.setTextColor(Color.rgb(103, 111, 106));
        footer.setTextSize(10);
        footer.setGravity(Gravity.CENTER);
        footer.setTypeface(Typeface.MONOSPACE, Typeface.NORMAL);
        LinearLayout.LayoutParams footerLp = matchWrap();
        footerLp.topMargin = dp(22);
        page.addView(footer, footerLp);

        setContentView(scroll);
    }


    private void exportDiagnosticLog() {
        DiagnosticLog.info(this, "Usuário solicitou exportação do log TXT.");
        Intent intent = new Intent(Intent.ACTION_CREATE_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("text/plain");
        intent.putExtra(Intent.EXTRA_TITLE, "blackops1-diagnostics.txt");
        startActivityForResult(intent, REQUEST_EXPORT_LOG);
    }

    private void writeDiagnosticExport(Uri uri) {
        try (OutputStream out = getContentResolver().openOutputStream(uri, "w")) {
            if (out == null) throw new java.io.IOException("O Android não abriu o arquivo de destino.");
            out.write(DiagnosticLog.readAll(this).getBytes(StandardCharsets.UTF_8));
            out.flush();
            Toast.makeText(this, "Log TXT salvo no local escolhido.", Toast.LENGTH_LONG).show();
            DiagnosticLog.info(this, "Exportação do log TXT concluída.");
        } catch (Throwable t) {
            DiagnosticLog.error(this, "Falha ao exportar log TXT.", t);
            new AlertDialog.Builder(this).setTitle("Falha ao exportar log")
                    .setMessage(t.toString()).setPositiveButton("OK", null).show();
        }
        refreshDiagnosticView();
    }

    private void refreshDiagnosticView() {
        if (diagnosticView == null) return;
        try {
            String[] lines = DiagnosticLog.readAll(this).split("\\n");
            StringBuilder tail = new StringBuilder();
            int start = Math.max(0, lines.length - 8);
            for (int i = start; i < lines.length; i++) {
                if (!lines[i].trim().isEmpty()) tail.append(lines[i]).append('\n');
            }
            diagnosticView.setText(tail.length() == 0 ? "Nenhum evento registrado." : tail.toString());
        } catch (Throwable t) {
            diagnosticView.setText("Falha ao ler log: " + t);
        }
    }

    private void collectPreviousProcessExitInfo() {
        if (android.os.Build.VERSION.SDK_INT < 30) return;
        try {
            ActivityManager manager = (ActivityManager) getSystemService(ACTIVITY_SERVICE);
            if (manager == null) return;
            long lastSeen = getPreferences(MODE_PRIVATE).getLong("last_exit_timestamp", 0L);
            List<ApplicationExitInfo> exits = manager.getHistoricalProcessExitReasons(getPackageName(), 0, 10);
            long newest = lastSeen;
            for (ApplicationExitInfo info : exits) {
                long timestamp = info.getTimestamp();
                if (timestamp <= lastSeen) continue;
                newest = Math.max(newest, timestamp);
                DiagnosticLog.error(this, "ENCERRAMENTO ANTERIOR: processo=" + info.getProcessName()
                        + ", motivo=" + info.getReason() + ", status=" + info.getStatus()
                        + ", pid=" + info.getPid() + ", descrição=" + info.getDescription(), null);
            }
            if (newest > lastSeen) getPreferences(MODE_PRIVATE).edit().putLong("last_exit_timestamp", newest).apply();
        } catch (Throwable t) {
            DiagnosticLog.error(this, "Falha ao consultar histórico de encerramentos Android.", t);
        }
    }


    private void chooseGameFolder() {
        if (importing) return;
        if (android.os.Build.VERSION.SDK_INT >= 30 && !Environment.isExternalStorageManager()) {
            try {
                DiagnosticLog.info(this, "Acesso amplo a arquivos necessário para o runtime nativo ler a pasta diretamente.");
                Intent settings = new Intent(Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION,
                        Uri.parse("package:" + getPackageName()));
                startActivity(settings);
                status.setText("PERMISSÃO NECESSÁRIA");
                statusDetail.setText("Ative o acesso para gerenciar todos os arquivos nas configurações do Android. Depois volte e toque em SELECIONAR PASTA novamente.");
            } catch (Throwable t) {
                DiagnosticLog.error(this, "Não foi possível abrir a tela de acesso a arquivos.", t);
                statusDetail.setText("Não foi possível abrir as configurações de arquivos: " + t);
            }
            return;
        }
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT_TREE);
        intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION
                | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION
                | Intent.FLAG_GRANT_PREFIX_URI_PERMISSION);
        startActivityForResult(intent, REQUEST_FOLDER);
    }

    private void handleSelectedFolder(Uri treeUri) {
        try {
            try { getContentResolver().takePersistableUriPermission(treeUri, Intent.FLAG_GRANT_READ_URI_PERMISSION); }
            catch (SecurityException ignored) { }
            String path = resolveLocalTreePath(treeUri);
            if (path == null) {
                throw new java.io.IOException("Esta pasta não pertence ao armazenamento local compartilhado. Escolha uma pasta em Armazenamento interno; provedores de nuvem/USB não podem ser usados diretamente pelo runtime nativo.");
            }
            File root = new File(path).getCanonicalFile();
            if (!root.isDirectory() || !root.canRead()) {
                throw new java.io.IOException("A pasta selecionada não existe ou não pode ser lida pelo aplicativo: " + root);
            }
            File xex = new File(root, "default.xex");
            if (!xex.isFile() || !xex.canRead() || xex.length() <= 0) {
                throw new java.io.IOException("default.xex precisa existir, ser legível e ter tamanho maior que zero na raiz da pasta.");
            }
            getPreferences(MODE_PRIVATE).edit().putString(KEY_FOLDER_PATH, root.getAbsolutePath())
                    .remove(KEY_URI).remove(KEY_NAME).apply();
            isoName.setText("Pasta: " + root.getAbsolutePath());
            playButton.setEnabled(false);
            setImporting(true);
            status.setText("VALIDANDO PASTA");
            statusDetail.setText("Verificando os arquivos da pasta original sem copiá-los…");
            DiagnosticLog.info(this, "Pasta de jogo selecionada: " + root.getAbsolutePath());
            refreshDiagnosticView();
            GameFolderValidator.validate(this, root, new GameFolderValidator.Callback() {
                @Override public void onProgress(String message, int checked, int total) {
                    runOnUiThread(() -> {
                        if (isFinishing()) return;
                        status.setText("VALIDANDO PASTA");
                        statusDetail.setText(message);
                        if (total > 0) {
                            progress.setIndeterminate(false);
                            progress.setProgress((int) Math.min(99, checked * 100L / total));
                        } else progress.setIndeterminate(true);
                        refreshDiagnosticView();
                    });
                }
                @Override public void onComplete(File folder, int count, String message) {
                    runOnUiThread(() -> {
                        if (isFinishing()) return;
                        setImporting(false);
                        persistRuntimeRoot(folder);
                        status.setText("PASTA VALIDADA");
                        statusDetail.setText(message + "\nO runtime lerá diretamente desta pasta, sem duplicar os arquivos.");
                        progress.setProgress(100);
                        playButton.setEnabled(true);
                        DiagnosticLog.info(MainActivity.this, "VALIDAÇÃO DA PASTA APROVADA: " + folder + "; arquivos=" + count);
                        refreshDiagnosticView();
                    });
                }
                @Override public void onError(String message, Throwable error) {
                    runOnUiThread(() -> {
                        if (isFinishing()) return;
                        setImporting(false);
                        playButton.setEnabled(false);
                        status.setText("FALHA NA VALIDAÇÃO DA PASTA");
                        statusDetail.setText(message);
                        DiagnosticLog.error(MainActivity.this, "FALHA NA VALIDAÇÃO DA PASTA: " + message, error);
                        refreshDiagnosticView();
                        new AlertDialog.Builder(MainActivity.this).setTitle("Pasta inválida")
                                .setMessage(message).setPositiveButton("OK", null).show();
                    });
                }
            });
        } catch (Throwable t) {
            DiagnosticLog.error(this, "Não foi possível usar a pasta selecionada.", t);
            status.setText("PASTA NÃO SUPORTADA");
            statusDetail.setText(t.getMessage() == null ? t.toString() : t.getMessage());
            playButton.setEnabled(false);
            refreshDiagnosticView();
            new AlertDialog.Builder(this).setTitle("Não foi possível usar a pasta")
                    .setMessage(t.getMessage() == null ? t.toString() : t.getMessage())
                    .setPositiveButton("OK", null).show();
        }
    }

    private String resolveLocalTreePath(Uri treeUri) throws Exception {
        if (!"com.android.externalstorage.documents".equals(treeUri.getAuthority())) return null;
        String documentId = DocumentsContract.getTreeDocumentId(treeUri);
        int separator = documentId.indexOf(':');
        if (separator <= 0) return null;
        String volume = documentId.substring(0, separator);
        String relative = documentId.substring(separator + 1);
        File base = "primary".equalsIgnoreCase(volume)
                ? Environment.getExternalStorageDirectory() : new File("/storage", volume);
        File root = relative.isEmpty() ? base : new File(base, relative);
        return root.getCanonicalPath();
    }

    private void persistRuntimeRoot(File root) {
        try {
            File target = new File(getFilesDir(), RUNTIME_ROOT_FILE);
            try (java.io.FileOutputStream out = new java.io.FileOutputStream(target, false)) {
                out.write(root.getCanonicalPath().getBytes(StandardCharsets.UTF_8));
                out.flush();
                out.getFD().sync();
            }
            DiagnosticLog.info(this, "Raiz do jogo configurada para o runtime: " + root.getCanonicalPath());
        } catch (Throwable t) {
            DiagnosticLog.error(this, "Falha ao gravar a raiz do jogo para o runtime.", t);
        }
    }

    private void chooseIso() {
        if (importing) return;
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("*/*");
        intent.putExtra(Intent.EXTRA_MIME_TYPES, new String[] {
                "application/octet-stream", "application/x-iso9660-image"
        });
        startActivityForResult(intent, REQUEST_ISO);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == REQUEST_FOLDER) {
            if (resultCode == RESULT_OK && data != null && data.getData() != null) handleSelectedFolder(data.getData());
            return;
        }
        if (requestCode == REQUEST_EXPORT_LOG && resultCode == RESULT_OK && data != null && data.getData() != null) {
            writeDiagnosticExport(data.getData());
            return;
        }
        if (requestCode != REQUEST_ISO || resultCode != RESULT_OK || data == null || data.getData() == null) return;

        Uri uri = data.getData();
        DiagnosticLog.info(this, "Usuário selecionou uma ISO: " + displayName(uri));
        try {
            int flags = data.getFlags() & (Intent.FLAG_GRANT_READ_URI_PERMISSION
                    | Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
            getContentResolver().takePersistableUriPermission(uri, flags & Intent.FLAG_GRANT_READ_URI_PERMISSION);
        } catch (SecurityException ignored) {
            // Alguns provedores dão permissão temporária; a cópia começa imediatamente.
        }

        String name = displayName(uri);
        getPreferences(MODE_PRIVATE).edit().remove(KEY_FOLDER_PATH).apply();
        isoName.setText(name);
        getPreferences(MODE_PRIVATE).edit().putString(KEY_URI, uri.toString())
                .putString(KEY_NAME, name).apply();
        playButton.setEnabled(false);
        DiagnosticLog.info(this, "Iniciando importação da ISO.");
        refreshDiagnosticView();
        status.setText("PREPARANDO ARQUIVOS");
        statusDetail.setText("Copiando e extraindo a ISO. O tamanho do arquivo pode tornar esse processo demorado.");
        setImporting(true);

        IsoImportManager.importIso(this, uri, new IsoImportManager.Callback() {
            @Override
            public void onProgress(String message, long processed, long total) {
                runOnUiThread(() -> {
                    if (isFinishing()) return;
                    DiagnosticLog.info(MainActivity.this, "IMPORTAÇÃO: " + message + " [" + processed + "/" + total + "]");
                    refreshDiagnosticView();
                    if (message.startsWith("Copiando ISO")) {
                        status.setText("COPIANDO ISO");
                        statusDetail.setText(message + "\n" + readable(processed)
                                + (total > 0 ? " / " + readable(total) : ""));
                    } else if (message.startsWith("Extraindo") || message.startsWith("Contando")) {
                        status.setText("EXTRAINDO ARQUIVOS");
                        statusDetail.setText(message + "\nO extrator nativo não fornece percentual nesta fase.");
                    } else {
                        status.setText("VALIDANDO ARQUIVOS");
                        statusDetail.setText(message);
                    }
                    if (total > 0) {
                        progress.setIndeterminate(false);
                        progress.setProgress((int) Math.min(99, processed * 100L / total));
                    } else {
                        progress.setIndeterminate(true);
                    }
                });
            }

            @Override
            public void onComplete(File gameDirectory, String message) {
                runOnUiThread(() -> {
                    if (isFinishing()) return;
                    setImporting(false);
                    DiagnosticLog.info(MainActivity.this, "IMPORTAÇÃO CONCLUÍDA: " + message);
                    refreshDiagnosticView();
                    progress.setProgress(100);
                    status.setText("ARQUIVOS VALIDADOS");
                    statusDetail.setText(message + "\nO runtime ainda não foi iniciado.");
                    playButton.setEnabled(new File(gameDirectory, "default.xex").isFile());
                    persistRuntimeRoot(gameDirectory);
                    Toast.makeText(MainActivity.this, "Preparação concluída", Toast.LENGTH_SHORT).show();
                });
            }

            @Override
            public void onError(String message, Throwable error) {
                runOnUiThread(() -> {
                    if (isFinishing()) return;
                    setImporting(false);
                    DiagnosticLog.error(MainActivity.this, "FALHA NA IMPORTAÇÃO: " + message, error);
                    refreshDiagnosticView();
                    status.setText("NÃO FOI POSSÍVEL PREPARAR A ISO");
                    statusDetail.setText(message == null ? "Falha desconhecida durante a importação." : message);
                    playButton.setEnabled(false);
                    new AlertDialog.Builder(MainActivity.this)
                            .setTitle("Falha ao preparar a ISO")
                            .setMessage(message == null ? "Ocorreu um erro ao importar o arquivo." : message)
                            .setPositiveButton("OK", null)
                            .show();
                });
            }
        });
    }

    private void refreshSavedGame() {
        SharedPreferences prefs = getPreferences(MODE_PRIVATE);
        String name = prefs.getString(KEY_NAME, null);
        String selectedFolder = prefs.getString(KEY_FOLDER_PATH, null);
        File gameRoot = selectedFolder == null ? new File(getFilesDir(), "blackops1") : new File(selectedFolder);
        File defaultXex = new File(gameRoot, "default.xex");
        if (selectedFolder != null) name = "Pasta: " + selectedFolder;
        if (name != null) isoName.setText(name);
        if (defaultXex.isFile() && defaultXex.canRead() && defaultXex.length() > 0) {
            persistRuntimeRoot(gameRoot);
            status.setText("ARQUIVOS PREPARADOS");
            statusDetail.setText(selectedFolder == null ? "Os arquivos extraídos estão disponíveis neste dispositivo." : "Pasta original validada e selecionada diretamente; nenhum arquivo foi copiado.");
            playButton.setEnabled(true);
        } else {
            status.setText("AGUARDANDO ARQUIVO");
            statusDetail.setText("Selecione uma ISO ou uma pasta local que contenha default.xex na raiz.");
            playButton.setEnabled(false);
        }
    }

    private void launchRuntime() {
        DiagnosticLog.info(this, "Usuário tocou em JOGAR; verificando executável e abrindo GameActivity.");
        refreshDiagnosticView();
        String selectedFolder = getPreferences(MODE_PRIVATE).getString(KEY_FOLDER_PATH, null);
        File gameRoot = selectedFolder == null ? new File(getFilesDir(), "blackops1") : new File(selectedFolder);
        File defaultXex = new File(gameRoot, "default.xex");
        if (!defaultXex.isFile() || !defaultXex.canRead() || defaultXex.length() <= 0) {
            playButton.setEnabled(false);
            status.setText("JOGO NÃO PREPARADO");
            statusDetail.setText("Selecione uma ISO ou valide novamente a pasta do jogo antes de jogar.");
            return;
        }
        persistRuntimeRoot(gameRoot);
        Intent intent = new Intent(this, GameActivity.class);
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        try {
            startActivity(intent);
            DiagnosticLog.info(this, "Intent de GameActivity enviada; aguardando carregamento SDL3/runtime.");
        } catch (Throwable t) {
            DiagnosticLog.error(this, "Não foi possível abrir GameActivity.", t);
            status.setText("FALHA AO ABRIR O RUNTIME");
            statusDetail.setText(t.toString());
            new AlertDialog.Builder(this).setTitle("Falha ao iniciar o jogo")
                    .setMessage(t.toString()).setPositiveButton("OK", null).show();
        }
        refreshDiagnosticView();
    }

    @Override
    protected void onResume() {
        super.onResume();
        collectPreviousProcessExitInfo();
        refreshDiagnosticView();
    }

    private void setImporting(boolean value) {
        importing = value;
        selectButton.setEnabled(!value);
        if (selectFolderButton != null) selectFolderButton.setEnabled(!value);
        playButton.setEnabled(false);
        progress.setVisibility(value ? View.VISIBLE : View.GONE);
        progress.setIndeterminate(value);
        if (value) status.setText("PREPARANDO ISO…");
    }

    private String displayName(Uri uri) {
        String name = null;
        try (android.database.Cursor cursor = getContentResolver().query(uri,
                new String[] { OpenableColumns.DISPLAY_NAME }, null, null, null)) {
            if (cursor != null && cursor.moveToFirst()) {
                int index = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME);
                if (index >= 0) name = cursor.getString(index);
            }
        } catch (Exception ignored) { }
        return name == null ? uri.getLastPathSegment() : name;
    }

    private Button makeButton(String label, boolean primary) {
        Button button = new Button(this);
        button.setText(label);
        button.setAllCaps(false);
        button.setTextSize(14);
        button.setTypeface(Typeface.MONOSPACE, Typeface.BOLD);
        button.setTextColor(primary ? Color.rgb(20, 22, 18) : text);
        button.setPadding(dp(12), dp(8), dp(12), dp(8));
        button.setBackground(roundRect(primary ? accent : Color.rgb(40, 47, 44),
                dp(8), primary ? accent : Color.rgb(77, 85, 76)));
        return button;
    }

    private GradientDrawable roundRect(int color, int radius, int stroke) {
        GradientDrawable drawable = new GradientDrawable();
        drawable.setColor(color);
        drawable.setCornerRadius(radius);
        drawable.setStroke(dp(1), stroke);
        return drawable;
    }

    private LinearLayout.LayoutParams matchWrap() {
        return new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT);
    }

    private int dp(int value) {
        return (int) (value * getResources().getDisplayMetrics().density + 0.5f);
    }

    private String readable(long bytes) {
        if (bytes < 1024L) return bytes + " B";
        if (bytes < 1024L * 1024L) return String.format(java.util.Locale.US, "%.1f KB", bytes / 1024.0);
        if (bytes < 1024L * 1024L * 1024L) return String.format(java.util.Locale.US, "%.1f MB", bytes / (1024.0 * 1024.0));
        return String.format(java.util.Locale.US, "%.2f GB", bytes / (1024.0 * 1024.0 * 1024.0));
    }
}
