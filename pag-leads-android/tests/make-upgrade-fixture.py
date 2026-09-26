"""Generate a synthetic version-8 app to check Android update storage retention.

Never reads the real stable APK or production data. Same package, preference
names and WebView origin as v1.7; disposable CI signing identity only.
"""
from pathlib import Path
import json
import sys

root = Path(sys.argv[1])
def write(name, text):
    p = root / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)

write('settings.gradle', '''pluginManagement { repositories { google(); mavenCentral(); gradlePluginPortal() } }
dependencyResolutionManagement { repositories { google(); mavenCentral() } }
rootProject.name = 'PAGSyntheticUpgradeBaseline'
include(':app')
''')
write('build.gradle', "plugins { id 'com.android.application' version '8.7.3' apply false }\n")
write('app/build.gradle', '''plugins { id 'com.android.application' }
android {
 namespace 'com.pinedaagencygroup.leads'
 compileSdk 35
 defaultConfig {
  applicationId 'com.pinedaagencygroup.leads'
  minSdk 23
  targetSdk 35
  versionCode 8
  versionName '1.7-SYNTHETIC-TEST'
 }
}
''')
write('app/src/main/AndroidManifest.xml', '''<manifest xmlns:android="http://schemas.android.com/apk/res/android">
<application android:theme="@android:style/Theme.Material.Light.NoActionBar" android:label="PAG synthetic baseline">
<activity android:name=".MainActivity" android:exported="true"><intent-filter>
<action android:name="android.intent.action.MAIN"/><category android:name="android.intent.category.LAUNCHER"/>
</intent-filter></activity></application></manifest>''')
write('app/src/main/java/com/pinedaagencygroup/leads/MainActivity.java', '''package com.pinedaagencygroup.leads;
import android.app.Activity;
import android.os.Bundle;
import android.webkit.*;
import java.io.FileOutputStream;
import java.util.*;
public class MainActivity extends Activity {
 @Override public void onCreate(Bundle state) {
  super.onCreate(state);
  getSharedPreferences("pag_native", MODE_PRIVATE).edit()
   .putString("url", "https://example.invalid/legacy")
   .putString("token", "synthetic-upgrade-only")
   .putBoolean("auto", false).putBoolean("notifications", true)
   .putBoolean("monitor_initialized", true)
   .putStringSet("seen_ids", new HashSet<>(Arrays.asList("PAG-A-2", "PAG-A-3"))).commit();
  WebView view = new WebView(this); setContentView(view);
  view.getSettings().setJavaScriptEnabled(true);
  view.getSettings().setDomStorageEnabled(true);
  view.getSettings().setAllowFileAccess(true);
  view.setWebViewClient(new WebViewClient(){
   @Override public void onPageFinished(WebView v,String url) {
    v.evaluateJavascript("localStorage.getItem('pagov')", result -> {
     if(result==null || !result.contains("Nota local")) return;
     try(FileOutputStream out=openFileOutput("fixture-ready",MODE_PRIVATE)){out.write(1);}
     catch(Exception e){throw new RuntimeException(e);}
    });
   }
  });
  view.loadUrl("file:///android_asset/index.html");
 }
}''')
notes = {'PAG-A-2': {'status': 'Seguimiento', 'note': 'Nota local v1.7 — acción', 'updatedAt': '2026-09-25T22:37:00Z'}}
settings = {'url': 'https://example.invalid/legacy', 'tok': 'synthetic-upgrade-only', 'auto': False, 'notify': True}
write('app/src/main/assets/index.html', '<!doctype html><meta charset="UTF-8"><script>'
      + 'localStorage.setItem("pagov",' + json.dumps(json.dumps(notes, ensure_ascii=False)) + ');'
      + 'localStorage.setItem("pagset12",' + json.dumps(json.dumps(settings)) + ');'
      + '</script><p>Synthetic upgrade fixture ready.</p>')
