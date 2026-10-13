package com.blackops1.recomp;

import android.app.Activity;
import android.os.Bundle;
import android.view.Gravity;
import android.view.ViewGroup;
import android.graphics.Color;
import android.widget.LinearLayout;
import android.widget.TextView;

public class MainActivity extends Activity {


private TextView statusText;

@Override
protected void onCreate(Bundle savedInstanceState) {
    super.onCreate(savedInstanceState);

    getWindow().getDecorView().setSystemUiVisibility(
            5894
            | 1024
            | 512
            | 4096
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
    subtitle.setText("Android ARM64");
    subtitle.setTextColor(Color.rgb(100, 180, 255));
    subtitle.setTextSize(18);
    subtitle.setGravity(Gravity.CENTER);

    statusText = new TextView(this);
    statusText.setText(
            "Aplicativo iniciado.\n"
            + "Aguardando integracao com o ReXGlue."
    );
    statusText.setTextColor(Color.LTGRAY);
    statusText.setTextSize(16);
    statusText.setGravity(Gravity.CENTER);
    statusText.setPadding(0, 40, 0, 0);

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


}
