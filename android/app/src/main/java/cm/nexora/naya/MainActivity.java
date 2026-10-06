package cm.nexora.naya;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.text.InputType;
import android.view.ViewGroup;
import android.webkit.SslErrorHandler;
import android.net.http.SslError;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.EditText;

public final class MainActivity extends Activity {
    private WebView webView;
    private SharedPreferences preferences;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        preferences = getSharedPreferences("naya", MODE_PRIVATE);
        webView = new WebView(this);
        webView.setLayoutParams(new ViewGroup.LayoutParams(-1, -1));
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(false);
        webView.setWebViewClient(new WebViewClient() {
            @Override public void onReceivedSslError(WebView view, SslErrorHandler handler, SslError error) {
                handler.cancel();
            }
        });
        setContentView(webView);
        String pairedUrl = preferences.getString("paired_url", "");
        if (pairedUrl.isEmpty()) showPairingDialog(); else webView.loadUrl(pairedUrl);
    }

    private void showPairingDialog() {
        EditText input = new EditText(this);
        input.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_URI);
        input.setHint("https://your-naya-domain.example/app/");
        new AlertDialog.Builder(this)
            .setTitle("Connect Naya")
            .setMessage("Enter your secure Naya cloud URL, or the private PC pairing link for local mode.")
            .setView(input)
            .setCancelable(false)
            .setPositiveButton("Pair", (dialog, which) -> {
                String value = input.getText().toString().trim();
                if (!value.startsWith("http://") && !value.startsWith("https://")) {
                    showPairingDialog(); return;
                }
                preferences.edit().putString("paired_url", value).apply();
                webView.loadUrl(value);
            }).setNegativeButton("Exit", (dialog, which) -> finish()).show();
    }

    @Override public void onBackPressed() {
        if (webView.canGoBack()) webView.goBack(); else super.onBackPressed();
    }
}
