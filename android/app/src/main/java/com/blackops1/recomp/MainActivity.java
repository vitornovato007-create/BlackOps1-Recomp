package com.blackops1.recomp;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Bundle;
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

/**
 * Launcher Android. Esta Activity NÃO herda de SDLActivity e não inicia o runtime.
 * A SDL/ReXGlue só é carregada em GameActivity depois que o usuário toca em Jogar.
 */
public final class MainActivity extends Activity {
    private static final int REQUEST_ISO = 4101;
    private static final String PREFS = "blackops1_launcher";
    private static final String KEY_URI = "selected_iso_uri";
    private static final String KEY_NAME = "selected_iso_name";

    private final int bg = Color.rgb(13, 16, 18);
    private final int panel = Color.rgb(25, 30, 31);
    private final int accent = Color.rgb(190, 157, 82);
    private final int text = Color.rgb(238, 236, 226);
    private final int muted = Color.rgb(158, 164, 158);

    private TextView isoName;
    private TextView status;
    private TextView statusDetail;
    private ProgressBar progress;
    private Button playButton;
    private Button selectButton;
    private boolean importing;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().setStatusBarColor(bg);
        getWindow().setNavigationBarColor(bg);
        getWindow().getDecorView().setSystemUiVisibility(0);
        buildInterface();
        refreshSavedGame();
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
        instructions.setText("Selecione uma ISO do seu jogo. O launcher vai preparar os arquivos antes de iniciar o runtime.");
        instructions.setTextColor(text);
        instructions.setTextSize(15);
        instructions.setLineSpacing(dp(3), 1.0f);
        LinearLayout.LayoutParams instLp = matchWrap();
        instLp.topMargin = dp(10);
        hero.addView(instructions, instLp);

        isoName = new TextView(this);
        isoName.setText("Nenhuma ISO selecionada");
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
        if (requestCode != REQUEST_ISO || resultCode != RESULT_OK || data == null || data.getData() == null) {
            return;
        }

        Uri uri = data.getData();
        try {
            int flags = data.getFlags() & (Intent.FLAG_GRANT_READ_URI_PERMISSION
                    | Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
            getContentResolver().takePersistableUriPermission(uri, flags & Intent.FLAG_GRANT_READ_URI_PERMISSION);
        } catch (SecurityException ignored) {
            // Alguns provedores dão permissão temporária; a cópia começa imediatamente.
        }

        String name = displayName(uri);
        isoName.setText(name);
        getPreferences(MODE_PRIVATE).edit().putString(KEY_URI, uri.toString())
                .putString(KEY_NAME, name).apply();
        playButton.setEnabled(false);
        status.setText("PREPARANDO ARQUIVOS");
        statusDetail.setText("Copiando e extraindo a ISO. O tamanho do arquivo pode tornar esse processo demorado.");
        setImporting(true);

        IsoImportManager.importIso(this, uri, new IsoImportManager.Callback() {
            @Override
            public void onProgress(String message, long processed, long total) {
                runOnUiThread(() -> {
                    if (isFinishing()) return;
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
                    progress.setProgress(100);
                    status.setText("ARQUIVOS VALIDADOS");
                    statusDetail.setText(message + "\nO runtime ainda não foi iniciado.");
                    playButton.setEnabled(new File(gameDirectory, "default.xex").isFile());
                    Toast.makeText(MainActivity.this, "Preparação concluída", Toast.LENGTH_SHORT).show();
                });
            }

            @Override
            public void onError(String message, Throwable error) {
                runOnUiThread(() -> {
                    if (isFinishing()) return;
                    setImporting(false);
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
        File defaultXex = new File(new File(getFilesDir(), "blackops1"), "default.xex");
        if (name != null) isoName.setText(name);
        if (defaultXex.isFile()) {
            status.setText("ARQUIVOS PREPARADOS");
            statusDetail.setText("Os arquivos extraídos estão disponíveis neste dispositivo.");
            playButton.setEnabled(true);
        } else {
            status.setText("AGUARDANDO ARQUIVO");
            statusDetail.setText("Selecione uma ISO compatível para preparar os arquivos.");
            playButton.setEnabled(false);
        }
    }

    private void launchRuntime() {
        File defaultXex = new File(new File(getFilesDir(), "blackops1"), "default.xex");
        if (!defaultXex.isFile()) {
            playButton.setEnabled(false);
            status.setText("JOGO NÃO PREPARADO");
            statusDetail.setText("Selecione a ISO e aguarde a extração terminar antes de jogar.");
            return;
        }
        Intent intent = new Intent(this, GameActivity.class);
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        startActivity(intent);
    }

    private void setImporting(boolean value) {
        importing = value;
        selectButton.setEnabled(!value);
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
