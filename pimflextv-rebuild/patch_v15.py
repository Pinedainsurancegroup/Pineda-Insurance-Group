from pathlib import Path

p = Path('app/src/main/java/com/pimflextv/next/MainActivity.java')
s = p.read_text()

s = s.replace('import android.app.Activity;\n', 'import android.app.Activity;\nimport android.app.PictureInPictureParams;\n')
s = s.replace('import android.os.Bundle;\n', 'import android.os.Bundle;\nimport android.os.Build;\n')
s = s.replace('import android.content.SharedPreferences;\n', 'import android.content.SharedPreferences;\nimport android.content.Intent;\n')
s = s.replace('import android.util.LruCache;\n', 'import android.util.LruCache;\nimport android.util.Rational;\n')

field = '    private long parentalUnlockedUntil = 0L;\n'
extra = '''    private String activePlaybackUrl = "";
    private Runnable sleepTimerRunnable;
    private int sleepTimerMinutes = 0;
'''
if field not in s:
    raise SystemExit('field marker not found')
s = s.replace(field, field + extra, 1)

marker = '    private String humanTime(long ms) {\n'
methods = r'''    private void enterPipMode() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) {
            Toast.makeText(this, "Picture-in-Picture requiere Android 8 o superior.", Toast.LENGTH_SHORT).show();
            return;
        }
        try {
            PictureInPictureParams params = new PictureInPictureParams.Builder()
                    .setAspectRatio(new Rational(16, 9))
                    .build();
            enterPictureInPictureMode(params);
        } catch (Exception e) {
            Toast.makeText(this, "No se pudo activar Picture-in-Picture.", Toast.LENGTH_SHORT).show();
        }
    }

    private void openExternalPlayer() {
        if (activePlaybackUrl == null || activePlaybackUrl.isEmpty()) {
            Toast.makeText(this, "No hay un stream activo.", Toast.LENGTH_SHORT).show();
            return;
        }
        try {
            Intent intent = new Intent(Intent.ACTION_VIEW);
            intent.setDataAndType(Uri.parse(activePlaybackUrl), "video/*");
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            startActivity(Intent.createChooser(intent, "Abrir con reproductor externo"));
        } catch (Exception e) {
            Toast.makeText(this, "No hay un reproductor externo compatible.", Toast.LENGTH_LONG).show();
        }
    }

    private void showSleepTimerDialog() {
        String[] labels = {"Desactivado", "15 minutos", "30 minutos", "60 minutos", "90 minutos"};
        int[] values = {0, 15, 30, 60, 90};
        int selected = 0;
        for (int i = 0; i < values.length; i++) {
            if (values[i] == sleepTimerMinutes) selected = i;
        }

        new AlertDialog.Builder(this)
                .setTitle("Temporizador de apagado")
                .setSingleChoiceItems(labels, selected, null)
                .setNegativeButton("Cancelar", null)
                .setPositiveButton("Aplicar", (dialog, which) -> {
                    android.widget.ListView list = ((AlertDialog) dialog).getListView();
                    int pos = list.getCheckedItemPosition();
                    if (pos < 0 || pos >= values.length) pos = 0;
                    setSleepTimer(values[pos]);
                }).show();
    }

    private void setSleepTimer(int minutes) {
        if (sleepTimerRunnable != null) {
            ui.removeCallbacks(sleepTimerRunnable);
            sleepTimerRunnable = null;
        }
        sleepTimerMinutes = minutes;
        if (minutes <= 0) {
            Toast.makeText(this, "Temporizador desactivado.", Toast.LENGTH_SHORT).show();
            return;
        }
        sleepTimerRunnable = () -> {
            sleepTimerRunnable = null;
            sleepTimerMinutes = 0;
            Toast.makeText(this, "Temporizador finalizado.", Toast.LENGTH_SHORT).show();
            Runnable backAction = systemBack;
            if (backAction != null) backAction.run();
            else releasePlayer();
        };
        ui.postDelayed(sleepTimerRunnable, minutes * 60L * 1000L);
        Toast.makeText(this, "Apagado en " + minutes + " minutos.", Toast.LENGTH_SHORT).show();
    }

    private String sleepTimerLabel() {
        return sleepTimerMinutes > 0 ? "⏱ " + sleepTimerMinutes + "m" : "⏱ SLEEP";
    }

'''
if marker not in s:
    raise SystemExit('humanTime marker not found')
s = s.replace(marker, methods + marker, 1)

p.write_text(s)
print('v1.5 player tools patch applied')
