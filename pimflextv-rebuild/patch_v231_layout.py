from pathlib import Path

p = Path('app/src/main/java/com/pimflextv/next/MainActivity.java')
s = p.read_text()

s = s.replace('renderPosterGrid(grid, type, categoryId, categoryName, arr, "");',
              'renderClonePosterGridFixed(grid, type, categoryId, categoryName, arr, "");')
s = s.replace('renderPosterGrid(grid, type, categoryId, categoryName, arr, q);',
              'renderClonePosterGridFixed(grid, type, categoryId, categoryName, arr, q);')

marker = '    private void renderCloneLiveGrid(GridLayout grid, String categoryId, String categoryName,\n'
if marker not in s:
    raise SystemExit('renderCloneLiveGrid marker not found')

method = r'''    private void renderClonePosterGridFixed(GridLayout grid, String type, String categoryId,
                                            String categoryName, JSONArray arr, String query) {
        grid.removeAllViews();
        int widthDp = Math.round(getResources().getDisplayMetrics().widthPixels /
                getResources().getDisplayMetrics().density);
        int available = Math.max(420, widthDp - (isTvLayout() ? 430 : 355));
        int cols = available >= 700 ? 5 : available >= 560 ? 4 : 3;
        grid.setColumnCount(cols);

        String q = query == null ? "" : query.trim().toLowerCase(Locale.ROOT);
        int cardWidth = Math.max(104, (available - (cols - 1) * 8) / cols);
        int posterHeight = Math.round(cardWidth * 1.38f);
        int shown = 0;

        for (int i = 0; i < arr.length() && shown < 250; i++) {
            JSONObject item = arr.optJSONObject(i);
            if (item == null) continue;

            String name = item.optString("name", item.optString("title", "Contenido"));
            if (!q.isEmpty() && !name.toLowerCase(Locale.ROOT).contains(q)) continue;

            String id = itemId(type, item);
            LinearLayout card = new LinearLayout(this);
            card.setOrientation(LinearLayout.VERTICAL);
            card.setBackgroundResource(R.drawable.clone_tile_bg);
            card.setPadding(dp(3), dp(3), dp(3), dp(4));
            card.setFocusable(true);
            card.setClickable(true);
            decorateCardFocus(card);

            GridLayout.LayoutParams gp = new GridLayout.LayoutParams();
            gp.width = dp(cardWidth);
            gp.height = ViewGroup.LayoutParams.WRAP_CONTENT;
            gp.setMargins(dp(3), dp(3), dp(3), dp(3));
            card.setLayoutParams(gp);

            ImageView poster = new ImageView(this);
            poster.setScaleType(ImageView.ScaleType.CENTER_CROP);
            poster.setImageResource(R.drawable.poster_placeholder);
            String art = item.optString("stream_icon",
                    item.optString("cover_big", item.optString("cover", "")));
            loadArtwork(art, poster);
            card.addView(poster, new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT, dp(posterHeight)));

            TextView title = label(name);
            title.setTextSize(13);
            title.setMaxLines(2);
            title.setEllipsize(TextUtils.TruncateAt.END);
            title.setGravity(Gravity.CENTER);
            title.setBackgroundColor(Color.argb(190, 16, 19, 30));
            card.addView(title, new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT, dp(46)));

            if ("vod".equals(type)) {
                String ext = safeExt(item.optString("container_extension", "mp4"));
                String artFinal = art;
                card.setOnClickListener(v -> runWithParentalGate(name, () ->
                        loadVodDetails(id, name, ext, artFinal,
                                () -> showItems(type, categoryId, categoryName, arr))));
            } else {
                card.setOnClickListener(v -> runWithParentalGate(name, () ->
                        loadSeriesEpisodes(id, name, categoryId, categoryName, arr)));
            }

            grid.addView(card);
            shown++;
        }

        if (shown == 0) {
            TextView empty = cardText("No se encontró contenido.");
            GridLayout.LayoutParams ep = new GridLayout.LayoutParams();
            ep.width = GridLayout.LayoutParams.MATCH_PARENT;
            ep.height = GridLayout.LayoutParams.WRAP_CONTENT;
            ep.columnSpec = GridLayout.spec(0, cols);
            empty.setLayoutParams(ep);
            grid.addView(empty);
        }
    }

'''
s = s.replace(marker, method + marker, 1)
p.write_text(s)
print('v2.3.1 landscape split-grid hotfix applied')
