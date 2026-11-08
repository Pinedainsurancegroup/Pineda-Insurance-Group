from pathlib import Path

p = Path('app/src/main/java/com/pimflextv/next/MainActivity.java')
s = p.read_text()

s = s.replace('import java.util.concurrent.ExecutorService;\n', 'import java.util.concurrent.ExecutorService;\nimport java.util.concurrent.CountDownLatch;\nimport java.util.concurrent.TimeUnit;\n')

tile = '        addDashboardTile(menu, "🗓  TV GUIDE", this::loadEpgChannels, cols);\n'
if tile not in s:
    raise SystemExit('TV GUIDE tile marker not found')
s = s.replace(tile, '''        addDashboardTile(menu, "🗓  TV GUIDE", this::loadEpgChannels, cols);
        addDashboardTile(menu, "📡  AHORA / PRÓXIMO", this::loadNowNextGuide, cols);
''', 1)

marker = '    private void loadCatchupChannels() {\n'
methods = r'''    private void loadNowNextGuide() {
        showLoading("Preparando guía Ahora / Próximo…");
        io.execute(() -> {
            try {
                JSONArray channels = new JSONArray(request("get_live_streams", null));
                int limit = Math.min(channels.length(), 48);
                JSONObject[] guide = new JSONObject[limit];
                CountDownLatch latch = new CountDownLatch(limit);
                ExecutorService pool = Executors.newFixedThreadPool(6);

                for (int i = 0; i < limit; i++) {
                    final int index = i;
                    final JSONObject channel = channels.optJSONObject(i);
                    pool.execute(() -> {
                        try {
                            if (channel == null) return;
                            String id = String.valueOf(channel.opt("stream_id"));
                            JSONObject epg = new JSONObject(request("get_short_epg",
                                    "stream_id=" + enc(id) + "&limit=4"));
                            JSONArray listings = epg.optJSONArray("epg_listings");

                            String nowTitle = "";
                            String nextTitle = "";
                            long nowSec = System.currentTimeMillis() / 1000L;
                            if (listings != null) {
                                for (int j = 0; j < listings.length(); j++) {
                                    JSONObject row = listings.optJSONObject(j);
                                    if (row == null) continue;
                                    long start = epgEpoch(row, "start_timestamp", "start");
                                    long end = epgEpoch(row, "stop_timestamp", "end");
                                    String title = decodeMaybeBase64(row.optString("title", "Programa"));

                                    if (start > 0 && end > start && nowSec >= start && nowSec < end) {
                                        nowTitle = title;
                                        if (j + 1 < listings.length()) {
                                            JSONObject next = listings.optJSONObject(j + 1);
                                            if (next != null) nextTitle = decodeMaybeBase64(next.optString("title", ""));
                                        }
                                        break;
                                    }
                                }
                                if (nowTitle.isEmpty() && listings.length() > 0) {
                                    JSONObject first = listings.optJSONObject(0);
                                    if (first != null) nowTitle = decodeMaybeBase64(first.optString("title", ""));
                                    if (listings.length() > 1) {
                                        JSONObject second = listings.optJSONObject(1);
                                        if (second != null) nextTitle = decodeMaybeBase64(second.optString("title", ""));
                                    }
                                }
                            }

                            JSONObject result = new JSONObject();
                            result.put("now", nowTitle);
                            result.put("next", nextTitle);
                            guide[index] = result;
                        } catch (Exception ignored) {
                        } finally {
                            latch.countDown();
                        }
                    });
                }

                latch.await(18, TimeUnit.SECONDS);
                pool.shutdownNow();
                ui.post(() -> showNowNextGuide(channels, guide, limit));
            } catch (Exception e) {
                ui.post(() -> showErrorScreen("No se pudo cargar Ahora / Próximo", e, this::showDashboard));
            }
        });
    }

    private void showNowNextGuide(JSONArray channels, JSONObject[] guide, int limit) {
        systemBack = this::showDashboard;
        root = baseScreen();
        addBack(this::showDashboard);
        addTitle("📡 AHORA / PRÓXIMO", 27);
        addSubtitle("Guía rápida de canales");

        int shown = 0;
        for (int i = 0; i < limit; i++) {
            JSONObject channel = channels.optJSONObject(i);
            if (channel == null) continue;
            JSONObject info = guide[i];
            String name = channel.optString("name", "Canal");
            String now = info == null ? "" : info.optString("now", "");
            String next = info == null ? "" : info.optString("next", "");

            LinearLayout card = new LinearLayout(this);
            card.setOrientation(LinearLayout.VERTICAL);
            card.setBackgroundColor(panel);
            card.setPadding(dp(14), dp(12), dp(14), dp(12));
            LinearLayout.LayoutParams cp = new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
            cp.setMargins(0, dp(4), 0, dp(4));
            card.setLayoutParams(cp);
            card.setFocusable(true);
            card.setClickable(true);
            decorateCardFocus(card);

            TextView channelName = label(name);
            channelName.setTypeface(Typeface.DEFAULT_BOLD);
            channelName.setTextSize(17);
            card.addView(channelName);

            TextView current = label(now.isEmpty() ? "Ahora: sin datos EPG" : "Ahora: " + now);
            current.setTextColor(primary);
            current.setTextSize(14);
            current.setPadding(0, dp(5), 0, 0);
            card.addView(current);

            if (!next.isEmpty()) {
                TextView upcoming = label("Próximo: " + next);
                upcoming.setTextColor(Color.rgb(185, 190, 205));
                upcoming.setTextSize(13);
                upcoming.setPadding(0, dp(3), 0, 0);
                card.addView(upcoming);
            }

            int channelIndex = i;
            card.setOnClickListener(v -> runWithParentalGate(name, () ->
                    playLiveWithZapping(channels, channelIndex,
                            () -> showNowNextGuide(channels, guide, limit))));
            root.addView(card);
            shown++;
        }

        if (shown == 0) root.addView(cardText("No se pudieron cargar canales."));
    }

'''
if marker not in s:
    raise SystemExit('Catch-Up marker not found for now-next')
s = s.replace(marker, methods + marker, 1)

p.write_text(s)
print('v2 Now/Next guide patch applied')
