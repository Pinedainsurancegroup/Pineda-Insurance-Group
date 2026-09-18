from pathlib import Path
import re

p = Path('app/src/main/java/com/pimflextv/next/MainActivity.java')
s = p.read_text()

s = s.replace('import android.graphics.Color;\n', 'import android.graphics.Color;\nimport android.graphics.Bitmap;\nimport android.graphics.BitmapFactory;\n')
s = s.replace('import android.text.Editable;\n', 'import android.text.Editable;\nimport android.text.TextUtils;\n')
s = s.replace('import android.view.Gravity;\n', 'import android.view.Gravity;\nimport android.view.View;\n')
s = s.replace('import android.widget.EditText;\n', 'import android.widget.EditText;\nimport android.widget.GridLayout;\nimport android.widget.ImageView;\n')
s = s.replace('import android.util.Base64;\n', 'import android.util.Base64;\nimport android.util.LruCache;\n')

s = s.replace(
    '    private final ExecutorService io = Executors.newSingleThreadExecutor();\n',
    '    private final ExecutorService io = Executors.newSingleThreadExecutor();\n'
    '    private final ExecutorService imageIo = Executors.newFixedThreadPool(4);\n'
)

field_marker = '    private Runnable systemBack;\n'
if field_marker not in s:
    raise SystemExit('field marker not found')
s = s.replace(field_marker, field_marker + '    private final LruCache<String, Bitmap> artCache = new LruCache<>(48);\n')

old_oncreate = '''    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        prefs = getSharedPreferences("pimflex_settings", MODE_PRIVATE);
        showLogin();
        if (prefs.getBoolean("remember", false)) {
            String savedPassword = SecureStore.loadPassword(this, prefs);
            if (!savedPassword.isEmpty()) {
                passInput.setText(savedPassword);
                authenticate();
            }
        }
    }
'''
new_oncreate = '''    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        prefs = getSharedPreferences("pimflex_settings", MODE_PRIVATE);
        showSplash();
        ui.postDelayed(this::startAfterSplash, 650);
    }

    private void startAfterSplash() {
        showLogin();
        if (prefs.getBoolean("remember", false)) {
            String savedPassword = SecureStore.loadPassword(this, prefs);
            if (!savedPassword.isEmpty()) {
                passInput.setText(savedPassword);
                authenticate();
            }
        }
    }

    private void showSplash() {
        systemBack = null;
        LinearLayout splash = new LinearLayout(this);
        splash.setOrientation(LinearLayout.VERTICAL);
        splash.setGravity(Gravity.CENTER);
        splash.setBackgroundColor(bg);
        splash.setPadding(dp(28), dp(28), dp(28), dp(28));

        ImageView logo = new ImageView(this);
        logo.setImageResource(R.drawable.pimflex_pt);
        logo.setScaleType(ImageView.ScaleType.CENTER_INSIDE);
        splash.addView(logo, new LinearLayout.LayoutParams(dp(190), dp(130)));

        TextView name = label("PIMFLEX TV");
        name.setTextSize(30);
        name.setTypeface(Typeface.DEFAULT_BOLD);
        name.setGravity(Gravity.CENTER);
        name.setTextColor(Color.WHITE);
        splash.addView(name);

        TextView sub = label("Entertainment · Live TV · Movies · Series");
        sub.setTextSize(14);
        sub.setTextColor(Color.rgb(180, 188, 210));
        sub.setGravity(Gravity.CENTER);
        sub.setPadding(0, dp(8), 0, 0);
        splash.addView(sub);

        setContentView(splash);
    }
'''
if old_oncreate not in s:
    raise SystemExit('onCreate visual target not found')
s = s.replace(old_oncreate, new_oncreate)

s = s.replace(
    '        io.shutdownNow();\n        super.onDestroy();',
    '        io.shutdownNow();\n        imageIo.shutdownNow();\n        super.onDestroy();'
)

dashboard_pattern = r'    private void showDashboard\(\) \{.*?\n    \}\n\n    private void loadCategories'
dashboard_repl = r'''    private void showDashboard() {
        systemBack = this::showLogin;
        root = baseScreen();
        addBrandHeader();

        String status = accountInfo == null ? "" : accountInfo.optString("status", "");
        String exp = accountInfo == null ? "" : formatEpoch(accountInfo.optString("exp_date", ""));
        root.addView(cardText("Cuenta: " + status + (exp.isEmpty() ? "" : "  ·  Expira: " + exp)));

        TextView welcome = label("Hola, " + username);
        welcome.setTextSize(18);
        welcome.setTypeface(Typeface.DEFAULT_BOLD);
        welcome.setTextColor(Color.WHITE);
        welcome.setPadding(0, dp(12), 0, dp(8));
        root.addView(welcome);

        GridLayout menu = new GridLayout(this);
        int cols = isTvLayout() ? 3 : 2;
        menu.setColumnCount(cols);
        menu.setUseDefaultMargins(false);
        root.addView(menu);

        addDashboardTile(menu, "📺\nLIVE TV", () -> loadCategories("live"), cols);
        addDashboardTile(menu, "🎬\nMOVIES", () -> loadCategories("vod"), cols);
        addDashboardTile(menu, "▶\nSERIES", () -> loadCategories("series"), cols);
        addDashboardTile(menu, "★\nFAVORITOS", this::loadFavorites, cols);
        addDashboardTile(menu, "🗓\nTV GUIDE", this::loadEpgChannels, cols);
        addDashboardTile(menu, "👤\nMI CUENTA", this::showAccount, cols);

        Button logout = secondaryButton("CAMBIAR CUENTA");
        logout.setOnClickListener(v -> {
            if (prefs != null) prefs.edit().putBoolean("remember", false).apply();
            if (prefs != null) SecureStore.clearPassword(prefs);
            password = "";
            showLogin();
        });
        root.addView(logout);
    }

    private void loadCategories'''
s, n = re.subn(dashboard_pattern, dashboard_repl, s, flags=re.S)
if n != 1:
    raise SystemExit(f'dashboard replacement count={n}')

show_items_pattern = r'    private void showItems\(String type, String categoryId, String categoryName, JSONArray arr\) \{.*?\n    \}\n\n    private void renderItems'
show_items_repl = r'''    private void showItems(String type, String categoryId, String categoryName, JSONArray arr) {
        Runnable back = () -> loadCategories(type);
        systemBack = back;
        root = baseScreen();
        addBack(back);
        addTitle(categoryName, 26);
        addSubtitle("Elementos: " + arr.length());

        EditText search = input("Buscar en " + categoryName, false);
        root.addView(search);

        final View list;
        if ("live".equals(type)) {
            LinearLayout liveList = new LinearLayout(this);
            liveList.setOrientation(LinearLayout.VERTICAL);
            list = liveList;
            root.addView(liveList);
            renderItems(liveList, type, categoryId, categoryName, arr, "");
        } else {
            GridLayout grid = new GridLayout(this);
            grid.setColumnCount(posterColumns());
            grid.setUseDefaultMargins(false);
            list = grid;
            root.addView(grid);
            renderPosterGrid(grid, type, categoryId, categoryName, arr, "");
        }

        search.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
            @Override public void onTextChanged(CharSequence text, int start, int before, int count) {
                String q = text == null ? "" : text.toString();
                if (list instanceof GridLayout) {
                    renderPosterGrid((GridLayout) list, type, categoryId, categoryName, arr, q);
                } else {
                    renderItems((LinearLayout) list, type, categoryId, categoryName, arr, q);
                }
            }
            @Override public void afterTextChanged(Editable s) {}
        });
    }

    private void renderItems'''
s, n = re.subn(show_items_pattern, show_items_repl, s, flags=re.S)
if n != 1:
    raise SystemExit(f'showItems replacement count={n}')

epg_pattern = r'    private void showChannelEpg\(String channelName, JSONObject obj, JSONArray parent\) \{.*?\n    \}\n\n    private void showAccount'
epg_repl = r'''    private void showChannelEpg(String channelName, JSONObject obj, JSONArray parent) {
        Runnable back = () -> showEpgChannels(parent);
        systemBack = back;
        root = baseScreen();
        addBack(back);
        addTitle(channelName, 26);
        addSubtitle("Programación");

        JSONArray listings = obj.optJSONArray("epg_listings");
        if (listings == null || listings.length() == 0) {
            root.addView(cardText("Este canal no devolvió programación EPG."));
            return;
        }
        for (int i = 0; i < listings.length(); i++) {
            JSONObject row = listings.optJSONObject(i);
            if (row == null) continue;
            String title = decodeMaybeBase64(row.optString("title", "Programa"));
            String desc = decodeMaybeBase64(row.optString("description", ""));
            String start = row.optString("start", "");
            String end = row.optString("end", "");

            LinearLayout card = new LinearLayout(this);
            card.setOrientation(LinearLayout.VERTICAL);
            card.setBackgroundColor(panel);
            card.setPadding(dp(16), dp(14), dp(16), dp(14));
            LinearLayout.LayoutParams cp = new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
            cp.setMargins(0, dp(5), 0, dp(5));
            card.setLayoutParams(cp);

            TextView t = label(title);
            t.setTypeface(Typeface.DEFAULT_BOLD);
            t.setTextSize(17);
            card.addView(t);

            if (!start.isEmpty()) {
                TextView time = label(start + "  →  " + end);
                time.setTextSize(13);
                time.setTextColor(primary);
                time.setPadding(0, dp(5), 0, 0);
                card.addView(time);
            }
            if (!desc.isEmpty() && !desc.equals(title)) {
                TextView d = label(desc);
                d.setTextSize(13);
                d.setTextColor(Color.rgb(185, 190, 205));
                d.setMaxLines(3);
                d.setEllipsize(TextUtils.TruncateAt.END);
                d.setPadding(0, dp(7), 0, 0);
                card.addView(d);
            }
            root.addView(card);
        }
    }

    private void showAccount'''
s, n = re.subn(epg_pattern, epg_repl, s, flags=re.S)
if n != 1:
    raise SystemExit(f'EPG replacement count={n}')

helper_marker = '    private void decorateFocus(Button b, int normalColor) {'
visual_helpers = r'''    private void addBrandHeader() {
        LinearLayout header = new LinearLayout(this);
        header.setOrientation(LinearLayout.HORIZONTAL);
        header.setGravity(Gravity.CENTER_VERTICAL);
        header.setPadding(0, 0, 0, dp(10));

        ImageView logo = new ImageView(this);
        logo.setImageResource(R.drawable.pimflex_pt);
        logo.setScaleType(ImageView.ScaleType.CENTER_INSIDE);
        header.addView(logo, new LinearLayout.LayoutParams(dp(82), dp(62)));

        LinearLayout texts = new LinearLayout(this);
        texts.setOrientation(LinearLayout.VERTICAL);
        texts.setPadding(dp(8), 0, 0, 0);
        TextView title = label("PIMFLEX TV");
        title.setTextSize(27);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        texts.addView(title);
        TextView sub = label("Premium entertainment");
        sub.setTextSize(13);
        sub.setTextColor(Color.rgb(172, 181, 205));
        texts.addView(sub);
        header.addView(texts, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        root.addView(header);
    }

    private void addDashboardTile(GridLayout grid, String text, Runnable action, int cols) {
        int widthDp = Math.round(getResources().getDisplayMetrics().widthPixels /
                getResources().getDisplayMetrics().density);
        int available = Math.max(280, widthDp - 52);
        int tileWidth = Math.max(130, (available - (cols - 1) * 10) / cols);

        Button b = new Button(this);
        b.setText(text);
        b.setTextColor(Color.WHITE);
        b.setTextSize(isTvLayout() ? 20 : 17);
        b.setGravity(Gravity.CENTER);
        b.setAllCaps(false);
        b.setBackgroundColor(Color.rgb(28, 36, 67));
        b.setFocusable(true);
        b.setOnClickListener(v -> action.run());
        decorateFocus(b, Color.rgb(28, 36, 67));

        GridLayout.LayoutParams gp = new GridLayout.LayoutParams();
        gp.width = dp(tileWidth);
        gp.height = dp(isTvLayout() ? 120 : 106);
        gp.setMargins(dp(4), dp(4), dp(4), dp(4));
        b.setLayoutParams(gp);
        grid.addView(b);
    }

    private int posterColumns() {
        int widthDp = Math.round(getResources().getDisplayMetrics().widthPixels /
                getResources().getDisplayMetrics().density);
        if (isTvLayout()) return 5;
        if (widthDp >= 720) return 4;
        if (widthDp >= 520) return 3;
        return 2;
    }

    private boolean isTvLayout() {
        return getPackageManager().hasSystemFeature("android.software.leanback") ||
                getResources().getConfiguration().smallestScreenWidthDp >= 720;
    }

    private void renderPosterGrid(GridLayout grid, String type, String categoryId, String categoryName,
                                  JSONArray arr, String query) {
        grid.removeAllViews();
        int cols = posterColumns();
        grid.setColumnCount(cols);
        String q = query == null ? "" : query.trim().toLowerCase(Locale.ROOT);

        int widthDp = Math.round(getResources().getDisplayMetrics().widthPixels /
                getResources().getDisplayMetrics().density);
        int available = Math.max(280, widthDp - 52);
        int cardWidth = Math.max(118, (available - (cols - 1) * 8) / cols);
        int posterHeight = Math.round(cardWidth * 1.38f);
        int shown = 0;
        int limit = Math.min(arr.length(), 350);

        for (int i = 0; i < limit; i++) {
            JSONObject item = arr.optJSONObject(i);
            if (item == null) continue;
            String name = item.optString("name", item.optString("title", "Contenido"));
            if (!q.isEmpty() && !name.toLowerCase(Locale.ROOT).contains(q)) continue;

            String id = itemId(type, item);
            LinearLayout card = new LinearLayout(this);
            card.setOrientation(LinearLayout.VERTICAL);
            card.setBackgroundColor(panel);
            card.setPadding(dp(4), dp(4), dp(4), dp(6));
            card.setFocusable(true);
            card.setClickable(true);
            decorateCardFocus(card);

            GridLayout.LayoutParams gp = new GridLayout.LayoutParams();
            gp.width = dp(cardWidth);
            gp.height = ViewGroup.LayoutParams.WRAP_CONTENT;
            gp.setMargins(dp(3), dp(4), dp(3), dp(4));
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
            title.setTypeface(Typeface.DEFAULT_BOLD);
            title.setTextSize(isTvLayout() ? 15 : 14);
            title.setMaxLines(2);
            title.setEllipsize(TextUtils.TruncateAt.END);
            title.setGravity(Gravity.CENTER_HORIZONTAL);
            title.setPadding(dp(4), dp(7), dp(4), dp(3));
            card.addView(title, new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT, dp(48)));

            Button fav = secondaryButton(isFavorite(type, id) ? "★ FAVORITO" : "☆ FAVORITO");
            fav.setTextSize(11);
            LinearLayout.LayoutParams fp = new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT, dp(42));
            fp.setMargins(0, 0, 0, 0);
            fav.setLayoutParams(fp);
            fav.setOnClickListener(v -> {
                toggleFavorite(type, id);
                fav.setText(isFavorite(type, id) ? "★ FAVORITO" : "☆ FAVORITO");
            });
            card.addView(fav);

            if ("vod".equals(type)) {
                String ext = safeExt(item.optString("container_extension", "mp4"));
                String url = server + "/movie/" + encPath(username) + "/" + encPath(password) + "/" + id + "." + ext;
                card.setOnClickListener(v -> playStream(name, url, null,
                        () -> showItems(type, categoryId, categoryName, arr)));
            } else {
                card.setOnClickListener(v -> loadSeriesEpisodes(id, name, categoryId, categoryName, arr));
            }

            grid.addView(card);
            shown++;
            if (shown >= 250) break;
        }

        if (shown == 0) {
            TextView empty = cardText(q.isEmpty() ? "No hay contenido disponible." : "No se encontraron resultados.");
            GridLayout.LayoutParams ep = new GridLayout.LayoutParams();
            ep.width = GridLayout.LayoutParams.MATCH_PARENT;
            ep.height = GridLayout.LayoutParams.WRAP_CONTENT;
            ep.columnSpec = GridLayout.spec(0, cols);
            empty.setLayoutParams(ep);
            grid.addView(empty);
        }
    }

    private void decorateCardFocus(View v) {
        v.setOnFocusChangeListener((view, hasFocus) -> {
            view.setBackgroundColor(hasFocus ? Color.rgb(46, 58, 104) : panel);
            float scale = hasFocus ? 1.035f : 1.0f;
            view.animate().scaleX(scale).scaleY(scale).setDuration(90).start();
        });
    }

    private void loadArtwork(String url, ImageView target) {
        if (url == null || url.trim().isEmpty() || "null".equalsIgnoreCase(url.trim())) return;
        final String key = url.trim();
        target.setTag(key);
        Bitmap cached = artCache.get(key);
        if (cached != null) {
            target.setImageBitmap(cached);
            return;
        }
        imageIo.execute(() -> {
            HttpURLConnection conn = null;
            try {
                conn = (HttpURLConnection) new URL(key).openConnection();
                conn.setConnectTimeout(9000);
                conn.setReadTimeout(12000);
                conn.setInstanceFollowRedirects(true);
                conn.setRequestProperty("User-Agent", "PIMFLEXTV/1.2 Android");
                Bitmap bitmap = BitmapFactory.decodeStream(conn.getInputStream());
                if (bitmap != null) {
                    artCache.put(key, bitmap);
                    ui.post(() -> {
                        Object tag = target.getTag();
                        if (tag != null && key.equals(tag.toString())) target.setImageBitmap(bitmap);
                    });
                }
            } catch (Exception ignored) {
            } finally {
                if (conn != null) conn.disconnect();
            }
        });
    }

'''
if helper_marker not in s:
    raise SystemExit('visual helper marker not found')
s = s.replace(helper_marker, visual_helpers + helper_marker, 1)

p.write_text(s)
print('Visual patch applied')
