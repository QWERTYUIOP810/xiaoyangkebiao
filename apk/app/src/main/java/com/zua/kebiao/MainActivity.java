package com.zua.kebiao;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.view.Menu;
import android.view.MenuItem;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.EditText;

public class MainActivity extends Activity {

    private static final String DEFAULT_URL = "https://qwertyuiop810.github.io/xiaoyangkebiao/";

    private WebView web;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        web = new WebView(this);

        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setUseWideViewPort(true);
        s.setLoadWithOverviewMode(true);
        s.setCacheMode(WebSettings.LOAD_DEFAULT);

        web.setWebViewClient(new WebViewClient());

        setContentView(web);

        if (getActionBar() != null) {
            getActionBar().setTitle("课表");
        }

        web.loadUrl(prefs().getString("url", DEFAULT_URL));
    }

    private SharedPreferences prefs() {
        return getSharedPreferences("cfg", MODE_PRIVATE);
    }

    @Override
    public boolean onCreateOptionsMenu(Menu menu) {
        menu.add(0, 1, 0, "刷新");
        menu.add(0, 2, 1, "修改网址");
        return true;
    }

    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
        if (item.getItemId() == 1) {
            web.reload();
            return true;
        }
        if (item.getItemId() == 2) {
            editUrl();
            return true;
        }
        return super.onOptionsItemSelected(item);
    }

    private void editUrl() {
        final EditText et = new EditText(this);
        et.setText(prefs().getString("url", DEFAULT_URL));

        new AlertDialog.Builder(this)
                .setTitle("课表网址")
                .setMessage("默认是自己的课表；如果别人有自己的课表网址，填进去即可。")
                .setView(et)
                .setPositiveButton("保存", (d, w) -> {
                    String u = et.getText().toString().trim();
                    if (u.length() == 0) {
                        return;
                    }
                    if (!u.startsWith("http://") && !u.startsWith("https://")) {
                        u = "https://" + u;
                    }
                    if (!u.endsWith("/")) {
                        u = u + "/";
                    }
                    prefs().edit().putString("url", u).apply();
                    web.loadUrl(u);
                })
                .setNegativeButton("取消", null)
                .show();
    }

    @Override
    public void onBackPressed() {
        if (web != null && web.canGoBack()) {
            web.goBack();
        } else {
            super.onBackPressed();
        }
    }
}
