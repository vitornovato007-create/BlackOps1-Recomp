package com.blackops1.recomp;

import android.app.Activity;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.graphics.Color;
import android.widget.LinearLayout;
import android.widget.TextView;

public class MainActivity extends Activity {


static {
    System.loadLibrary("blackops1_android");
}

private TextView statusText;

private native String getNativeStatus();

@Override
protected void onCreate(Bundle savedInstanceState) {
    super.onCreate(savedInstanceState);

    getWindow().getDecorView().setSystemUiVisibility(
            View.SYSTEM_UI_FLAG_FULLSCREEN
            | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
            | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
            | View.SYSTEM_UI_FLAG_LAYOUT_STABLE
            | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
            | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
    );

    LinearLayout layout = new LinearLayout(this);
    layout.setOrientation(LinearLayout.VERTICAL);
    layout.setGravity(Gravity.CENTER);
    layout.setPadding(32, 32, 32, 32);
    layout.setBackgroundColor(Color.rgb(15, 18, 25));

    TextView title = new TextView(this);
    title.setText("BLACK OPS 1 RECOMP");
    title.setTextColor(Color.WHITE);
    title.setTextSize(26);
    title.setGravity(Gravity.CENTER);

    TextView subtitle = new TextView(this);
    subtitle.setText("ANDROID ARM64");
    subtitle.setTextColor(Color.rgb(100, 180, 255));
    subtitle.setTextSize(18);
    subtitle.setGravity(Gravity.CENTER);
    subtitle.setPadding(0, 16, 0, 0);

    statusText = new TextView(this);
    statusText.setTextColor(Color.LTGRAY);
    statusText.setTextSize(16);
    statusText.setGravity(Gravity.CENTER);
    statusText.setPadding(0, 40, 0, 0);

    try {
        statusText.setText(getNativeStatus());
    } catch (UnsatisfiedLinkError e) {
        statusText.setText(
                "Erro ao carregar a biblioteca C++.\n"
                + "Verifique a compilacao nativa."
        );
    }

    layout.addView(title,
            new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,
                    ViewGroup.LayoutParams.WRAP_CONTENT));

    layout.addView(subtitle,
            new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,
                    ViewGroup.LayoutParams.WRAP_CONTENT));

    layout.addView(statusText,
            new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,
                    ViewGroup.LayoutParams.WRAP_CONTENT));

    setContentView(layout);
}

@Override
protected void onDestroy() {
    super.onDestroy();
}


}
