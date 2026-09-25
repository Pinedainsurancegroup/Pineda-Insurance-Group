from pathlib import Path

p = Path('app/src/main/java/com/pimflextv/next/MainActivity.java')
s = p.read_text()

field = '    private final List<ExoPlayer> multiPlayers = new ArrayList<>();\n'
extra = '''    private JSONArray zappingChannels;
    private int zappingIndex = -1;
    private Runnable zappingBack;
'''
if field not in s:
    raise SystemExit('multiPlayers field marker not found')
s = s.replace(field, field + extra, 1)

base = '''    private LinearLayout baseScreen() {
        releaseMultiPlayers();
        releasePlayer();
'''
repl = '''    private LinearLayout baseScreen() {
        releaseMultiPlayers();
        releasePlayer();
        zappingChannels = null;
        zappingIndex = -1;
        zappingBack = null;
'''
if base not in s:
    raise SystemExit('baseScreen marker not found for zapping')
s = s.replace(base, repl, 1)

old = '''            if ("live".equals(type)) {
                String ts = liveUrl(id, "ts");
                String hls = liveUrl(id, "m3u8");
                b.setOnClickListener(v -> runWithParentalGate(name, () ->
                        playStream(name, ts, hls,
                                () -> showItems(type, categoryId, categoryName, arr))));
'''
new = '''            if ("live".equals(type)) {
                int liveIndex = i;
                b.setOnClickListener(v -> runWithParentalGate(name, () ->
                        playLiveWithZapping(arr, liveIndex,
                                () -> showItems(type, categoryId, categoryName, arr))));
'''
if old not in s:
    raise SystemExit('live render block not found')
s = s.replace(old, new, 1)

marker = '    private void loadMultiScreenChannels() {\n'
methods = r'''    private void playLiveWithZapping(JSONArray channels, int index, Runnable back) {
        if (channels == null || channels.length() == 0) return;
        int normalized = index;
        if (normalized < 0) normalized = channels.length() - 1;
        if (normalized >= channels.length()) normalized = 0;

        JSONObject item = channels.optJSONObject(normalized);
        if (item == null) return;
        String id = String.valueOf(item.opt("stream_id"));
        String name = item.optString("name", "Canal");

        zappingChannels = channels;
        zappingIndex = normalized;
        zappingBack = back;

        String ts = liveUrl(id, "ts");
        String hls = liveUrl(id, "m3u8");
        playStream(name, ts, hls, back);
    }

    private void zapPreviousChannel() {
        if (zappingChannels == null || zappingChannels.length() == 0) return;
        playLiveWithZapping(zappingChannels, zappingIndex - 1,
                zappingBack == null ? this::showDashboard : zappingBack);
    }

    private void zapNextChannel() {
        if (zappingChannels == null || zappingChannels.length() == 0) return;
        playLiveWithZapping(zappingChannels, zappingIndex + 1,
                zappingBack == null ? this::showDashboard : zappingBack);
    }

'''
if marker not in s:
    raise SystemExit('multiscreen marker not found for zapping methods')
s = s.replace(marker, methods + marker, 1)

p.write_text(s)
print('v2 live zapping patch applied')
