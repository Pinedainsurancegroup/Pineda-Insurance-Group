from pathlib import Path
import re

p = Path('app/src/main/java/com/pimflextv/next/MainActivity.java')
s = p.read_text()

# Do not stop the foreground DVR service just because the Activity is destroyed.
s = s.replace('''    protected void onDestroy() {
        stopRecording(false);
        releaseLivePreview();
''', '''    protected void onDestroy() {
        releaseLivePreview();
''', 1)

# Replace start/stop methods with foreground-service control.
pattern = r'''    private void startLiveRecording\(String title, String url\) \{.*?
    \}

    private void stopRecording\(boolean notify\) \{.*?
    \}

    private File recordingsDir'''
m = re.search(pattern, s, flags=re.S)
if not m:
    raise SystemExit('recording methods block not found')
replacement = r'''    private void startLiveRecording(String title, String url) {
        if (RecordingService.isRunning()) {
            Toast.makeText(this, "Ya hay una grabación activa.", Toast.LENGTH_LONG).show();
            return;
        }
        try {
            Intent intent = new Intent(this, RecordingService.class);
            intent.setAction(RecordingService.ACTION_START);
            intent.putExtra(RecordingService.EXTRA_URL, url);
            intent.putExtra(RecordingService.EXTRA_TITLE, title);
            if (Build.VERSION.SDK_INT >= 26) startForegroundService(intent);
            else startService(intent);
            recordingActive = true;
            Toast.makeText(this, "Grabación iniciada en segundo plano.", Toast.LENGTH_LONG).show();
        } catch (Exception e) {
            recordingActive = false;
            Toast.makeText(this, "No se pudo iniciar la grabación: " + cleanError(e), Toast.LENGTH_LONG).show();
        }
    }

    private void stopRecording(boolean notify) {
        recordingActive = false;
        try {
            Intent intent = new Intent(this, RecordingService.class);
            intent.setAction(RecordingService.ACTION_STOP);
            startService(intent);
        } catch (Exception ignored) {}
        if (notify) Toast.makeText(this, "Grabación detenida.", Toast.LENGTH_SHORT).show();
    }

    private File recordingsDir'''
s = s[:m.start()] + replacement + s[m.end():]

# Make UI state reflect the service, including after activity recreation.
s = s.replace('Button record = recordingActive ? cloneRedButton("■ DETENER REC") : cloneGreenButton("● GRABAR");',
              'Button record = RecordingService.isRunning() ? cloneRedButton("■ DETENER REC") : cloneGreenButton("● GRABAR");')
s = s.replace('''            if (recordingActive) {
                stopRecording(true);''',
              '''            if (RecordingService.isRunning()) {
                stopRecording(true);''')
s = s.replace('''        if (recordingActive) {
            root.addView(cardText("Grabando ahora:\\n" +
                    (activeRecordingFile == null ? "Stream en directo" : activeRecordingFile.getName())));''',
              '''        if (RecordingService.isRunning()) {
            String currentPath = RecordingService.getCurrentFilePath();
            String recordingName = currentPath == null || currentPath.isEmpty()
                    ? RecordingService.getCurrentTitle() : new File(currentPath).getName();
            root.addView(cardText("Grabando ahora:\\n" + recordingName));''')

p.write_text(s)
print('v2.9 foreground DVR integration patch applied')
