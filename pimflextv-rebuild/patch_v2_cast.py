from pathlib import Path

p = Path('app/src/main/java/com/pimflextv/next/MainActivity.java')
s = p.read_text()

s = s.replace('import androidx.media3.ui.PlayerView;\n', '''import androidx.media3.ui.PlayerView;\nimport androidx.mediarouter.app.MediaRouteButton;\n\nimport com.google.android.gms.cast.MediaInfo;\nimport com.google.android.gms.cast.MediaMetadata;\nimport com.google.android.gms.cast.framework.CastButtonFactory;\nimport com.google.android.gms.cast.framework.CastContext;\nimport com.google.android.gms.cast.framework.CastSession;\nimport com.google.android.gms.cast.framework.media.RemoteMediaClient;\nimport com.google.android.gms.cast.framework.media.MediaLoadRequestData;\n''')

marker = '    private void enterPipMode() {\n'
methods = r'''    private void castActiveStream(String title) {
        if (activePlaybackUrl == null || activePlaybackUrl.isEmpty()) {
            Toast.makeText(this, "No hay un stream activo para enviar.", Toast.LENGTH_SHORT).show();
            return;
        }
        try {
            CastContext context = CastContext.getSharedInstance(this);
            CastSession session = context.getSessionManager().getCurrentCastSession();
            if (session == null || !session.isConnected()) {
                Toast.makeText(this, "Selecciona primero un dispositivo Chromecast.", Toast.LENGTH_LONG).show();
                return;
            }

            MediaMetadata metadata = new MediaMetadata(MediaMetadata.MEDIA_TYPE_GENERIC);
            metadata.putString(MediaMetadata.KEY_TITLE, title == null ? "PIMFLEX TV" : title);

            String lower = activePlaybackUrl.toLowerCase(Locale.ROOT);
            String contentType = lower.contains(".m3u8") ? "application/x-mpegURL"
                    : lower.endsWith(".mp4") ? "video/mp4" : "video/mp2t";
            int streamType = currentWatchType == null || currentWatchType.isEmpty()
                    ? MediaInfo.STREAM_TYPE_LIVE : MediaInfo.STREAM_TYPE_BUFFERED;

            MediaInfo info = new MediaInfo.Builder(activePlaybackUrl)
                    .setStreamType(streamType)
                    .setContentType(contentType)
                    .setMetadata(metadata)
                    .build();

            RemoteMediaClient remote = session.getRemoteMediaClient();
            if (remote == null) throw new Exception("RemoteMediaClient no disponible");
            remote.load(new MediaLoadRequestData.Builder()
                    .setMediaInfo(info)
                    .setAutoplay(true)
                    .build());
            Toast.makeText(this, "Enviando a Chromecast…", Toast.LENGTH_SHORT).show();
        } catch (Exception e) {
            Toast.makeText(this, "Chromecast: " + cleanError(e), Toast.LENGTH_LONG).show();
        }
    }

'''
if marker not in s:
    raise SystemExit('PiP marker not found for cast methods')
s = s.replace(marker, methods + marker, 1)

p.write_text(s)
print('v2 Chromecast patch applied')
