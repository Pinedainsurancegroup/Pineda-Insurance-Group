from pathlib import Path
import re

p = Path('app/src/main/java/com/pimflextv/next/MainActivity.java')
s = p.read_text()

# Clone-style dashboard and shared visual helpers
dashboard_pattern = r'    private void showDashboard\(\) \{.*?\n    \}\n\n    private void loadCategories'
dashboard_repl = r'''    private void showDashboard() {
        systemBack = this::showLogin;
        root = cloneScreen();
        addCloneHeader("", null);

        LinearLayout searchRow = new LinearLayout(this);
        searchRow.setGravity(Gravity.END | Gravity.CENTER_VERTICAL);
        Button masterSearch = cloneGrayButton("⌕  Búsqueda maestra");
        masterSearch.setOnClickListener(v -> loadGlobalSearch());
        LinearLayout.LayoutParams ms = new LinearLayout.LayoutParams(dp(230), dp(54));
        ms.setMargins(0, dp(4), dp(4), dp(12));
        masterSearch.setLayoutParams(ms);
        searchRow.addView(masterSearch);
        TextView dots = label("⋮");
        dots.setTextSize(34);
        dots.setGravity(Gravity.CENTER);
        searchRow.addView(dots, new LinearLayout.LayoutParams(dp(54), dp(54)));
        root.addView(searchRow);

        GridLayout primaryGrid = new GridLayout(this);
        primaryGrid.setColumnCount(3);
        primaryGrid.setUseDefaultMargins(false);
        root.addView(primaryGrid, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        addCloneMainTile(primaryGrid, "TV EN DIRECTO", "⌁", () -> loadCategories("live"));
        addCloneMainTile(primaryGrid, "CINE", "●", () -> loadCategories("vod"));
        addCloneMainTile(primaryGrid, "SERIES", "▶", () -> loadCategories("series"));

        GridLayout lowerGrid = new GridLayout(this);
        lowerGrid.setColumnCount(3);
        lowerGrid.setUseDefaultMargins(false);
        LinearLayout.LayoutParams lowerParams = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        lowerParams.setMargins(dp(26), dp(12), dp(26), 0);
        lowerGrid.setLayoutParams(lowerParams);
        root.addView(lowerGrid);

        addCloneSmallTile(lowerGrid, "↶", "CATCH UP", this::loadCatchupChannels);
        addCloneSmallTile(lowerGrid, "▦", "PANTALLA MÚLTIPLE", this::loadMultiScreenChannels);
        addCloneSmallTile(lowerGrid, "▣", "EPG", this::loadEpgChannels);

        LinearLayout quickRow = new LinearLayout(this);
        quickRow.setOrientation(LinearLayout.HORIZONTAL);
        quickRow.setGravity(Gravity.CENTER);
        quickRow.setPadding(dp(26), dp(12), dp(26), 0);

        Button settings = cloneGrayButton("⚙  AJUSTES");
        settings.setOnClickListener(v -> showSettings());
        quickRow.addView(settings, weightedButtonParams());

        Button accounts = cloneGrayButton("♙  CUENTAS");
        accounts.setOnClickListener(v -> showSavedAccounts());
        quickRow.addView(accounts, weightedButtonParams());

        Button favorites = cloneGrayButton("♥  FAVORITOS");
        favorites.setOnClickListener(v -> loadFavorites());
        quickRow.addView(favorites, weightedButtonParams());
        root.addView(quickRow);

        String exp = accountInfo == null ? "" : formatEpoch(accountInfo.optString("exp_date", ""));
        TextView expiry = label(exp.isEmpty() ? "" : "EXPIRACIÓN: " + exp);
        expiry.setGravity(Gravity.CENTER);
        expiry.setTextSize(15);
        expiry.setPadding(0, dp(16), 0, dp(2));
        root.addView(expiry);
    }

    private LinearLayout cloneScreen() {
        LinearLayout body = baseScreen();
        body.setBackgroundResource(R.drawable.clone_screen_bg);
        body.setPadding(dp(28), dp(18), dp(28), dp(28));
        return body;
    }

    private void addCloneHeader(String middleTitle, Runnable back) {
        LinearLayout header = new LinearLayout(this);
        header.setOrientation(LinearLayout.HORIZONTAL);
        header.setGravity(Gravity.CENTER_VERTICAL);
        header.setPadding(0, 0, 0, dp(10));

        if (back != null) {
            Button backBtn = new Button(this);
            backBtn.setText("←");
            backBtn.setTextSize(28);
            backBtn.setTextColor(Color.WHITE);
            backBtn.setBackgroundColor(Color.TRANSPARENT);
            backBtn.setFocusable(true);
            backBtn.setOnClickListener(v -> back.run());
            header.addView(backBtn, new LinearLayout.LayoutParams(dp(70), dp(58)));
        }

        ImageView logo = new ImageView(this);
        logo.setImageResource(R.drawable.pimflex_pt);
        logo.setScaleType(ImageView.ScaleType.CENTER_INSIDE);
        header.addView(logo, new LinearLayout.LayoutParams(dp(200), dp(78)));

        TextView middle = label(middleTitle == null ? "" : middleTitle);
        middle.setTextSize(23);
        middle.setTypeface(Typeface.DEFAULT_BOLD);
        middle.setGravity(Gravity.CENTER);
        header.addView(middle, new LinearLayout.LayoutParams(0, dp(70), 1f));

        LinearLayout clock = new LinearLayout(this);
        clock.setOrientation(LinearLayout.HORIZONTAL);
        clock.setGravity(Gravity.END | Gravity.CENTER_VERTICAL);
        String timeText = DateFormat.getTimeInstance(DateFormat.SHORT, Locale.getDefault()).format(new Date());
        String dateText = DateFormat.getDateInstance(DateFormat.LONG, Locale.getDefault()).format(new Date());
        TextView time = label(timeText);
        time.setTextSize(20);
        time.setPadding(0, 0, dp(18), 0);
        clock.addView(time);
        TextView date = label(dateText);
        date.setTextSize(14);
        date.setTextColor(Color.rgb(210, 214, 225));
        clock.addView(date);
        header.addView(clock, new LinearLayout.LayoutParams(dp(360), dp(70)));

        root.addView(header);
    }

    private void addCloneMainTile(GridLayout grid, String titleText, String symbol, Runnable action) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setGravity(Gravity.CENTER);
        card.setBackgroundResource(R.drawable.clone_tile_bg);
        card.setPadding(dp(10), dp(10), dp(10), 0);
        card.setFocusable(true);
        card.setClickable(true);
        decorateCardFocus(card);
        card.setOnClickListener(v -> action.run());

        TextView title = label(titleText);
        title.setTextSize(23);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setGravity(Gravity.CENTER);
        card.addView(title, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(50)));

        TextView icon = label(symbol);
        icon.setTextSize(58);
        icon.setTextColor(Color.rgb(75, 126, 232));
        icon.setGravity(Gravity.CENTER);
        card.addView(icon, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));

        TextView footer = label("Última actualización: ahora     ↻");
        footer.setTextSize(11);
        footer.setGravity(Gravity.CENTER);
        footer.setBackgroundColor(Color.rgb(22, 28, 39));
        card.addView(footer, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(38)));

        GridLayout.LayoutParams gp = new GridLayout.LayoutParams();
        gp.width = 0;
        gp.height = dp(isTvLayout() ? 255 : 220);
        gp.columnSpec = GridLayout.spec(GridLayout.UNDEFINED, 1f);
        gp.setMargins(dp(8), dp(5), dp(8), dp(5));
        card.setLayoutParams(gp);
        grid.addView(card);
    }

    private void addCloneSmallTile(GridLayout grid, String symbol, String title, Runnable action) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.HORIZONTAL);
        card.setGravity(Gravity.CENTER);
        card.setBackgroundResource(R.drawable.clone_tile_bg);
        card.setPadding(dp(12), dp(8), dp(12), dp(8));
        card.setFocusable(true);
        card.setClickable(true);
        decorateCardFocus(card);
        card.setOnClickListener(v -> action.run());

        TextView icon = label(symbol);
        icon.setTextSize(34);
        icon.setTextColor(Color.rgb(75, 126, 232));
        icon.setGravity(Gravity.CENTER);
        card.addView(icon, new LinearLayout.LayoutParams(dp(72), dp(70)));

        TextView text = label(title);
        text.setTextSize(17);
        text.setTypeface(Typeface.DEFAULT_BOLD);
        text.setGravity(Gravity.CENTER_VERTICAL);
        card.addView(text, new LinearLayout.LayoutParams(0, dp(70), 1f));

        GridLayout.LayoutParams gp = new GridLayout.LayoutParams();
        gp.width = 0;
        gp.height = dp(92);
        gp.columnSpec = GridLayout.spec(GridLayout.UNDEFINED, 1f);
        gp.setMargins(dp(8), dp(5), dp(8), dp(5));
        card.setLayoutParams(gp);
        grid.addView(card);
    }

    private LinearLayout.LayoutParams weightedButtonParams() {
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(0, dp(54), 1f);
        p.setMargins(dp(5), 0, dp(5), 0);
        return p;
    }

    private Button cloneGrayButton(String text) {
        Button b = new Button(this);
        b.setText(text);
        b.setTextColor(Color.WHITE);
        b.setTextSize(15);
        b.setAllCaps(false);
        b.setBackgroundResource(R.drawable.clone_gray_button);
        b.setFocusable(true);
        return b;
    }

    private Button cloneGreenButton(String text) {
        Button b = new Button(this);
        b.setText(text);
        b.setTextColor(Color.WHITE);
        b.setTextSize(17);
        b.setTypeface(Typeface.DEFAULT_BOLD);
        b.setBackgroundResource(R.drawable.clone_green_button);
        b.setFocusable(true);
        return b;
    }

    private Button cloneRedButton(String text) {
        Button b = new Button(this);
        b.setText(text);
        b.setTextColor(Color.WHITE);
        b.setTextSize(17);
        b.setTypeface(Typeface.DEFAULT_BOLD);
        b.setBackgroundResource(R.drawable.clone_red_button);
        b.setFocusable(true);
        return b;
    }

    private void loadCategories'''
s, n = re.subn(dashboard_pattern, dashboard_repl, s, flags=re.S)
if n != 1:
    raise SystemExit(f'clone dashboard replacement count={n}')

# Clone category list
categories_pattern = r'    private void showCategories\(String type, JSONArray arr\) \{.*?\n    \}\n\n    private void loadItems'
categories_repl = r'''    private void showCategories(String type, JSONArray arr) {
        systemBack = this::showDashboard;
        root = cloneScreen();
        addCloneHeader(typeTitle(type), this::showDashboard);

        LinearLayout searchBar = new LinearLayout(this);
        searchBar.setOrientation(LinearLayout.HORIZONTAL);
        searchBar.setBackgroundColor(Color.rgb(25, 25, 25));
        searchBar.setPadding(dp(12), dp(5), dp(12), dp(5));

        EditText search = input("Buscar en categorías", false);
        search.setBackgroundColor(Color.TRANSPARENT);
        searchBar.addView(search, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(52)));
        root.addView(searchBar);

        LinearLayout list = new LinearLayout(this);
        list.setOrientation(LinearLayout.VERTICAL);
        root.addView(list);
        renderCloneCategories(list, type, arr, "");

        search.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
            @Override public void onTextChanged(CharSequence s, int start, int before, int count) {
                renderCloneCategories(list, type, arr, s == null ? "" : s.toString());
            }
            @Override public void afterTextChanged(Editable s) {}
        });
    }

    private void renderCloneCategories(LinearLayout list, String type, JSONArray arr, String query) {
        list.removeAllViews();
        String q = query == null ? "" : query.trim().toLowerCase(Locale.ROOT);

        Button all = listButton("TODO");
        all.setBackgroundColor(Color.rgb(47, 146, 230));
        all.setOnClickListener(v -> loadAllItemsClone(type, "TODO"));
        list.addView(all);

        Button fav = listButton("FAVORITOS");
        fav.setOnClickListener(v -> loadFavorites());
        list.addView(fav);

        if ("vod".equals(type)) {
            Button recent = listButton("RECIENTEMENTE MIRADA");
            recent.setOnClickListener(v -> showWatchHistory(false));
            list.addView(recent);
        }

        for (int i = 0; i < arr.length(); i++) {
            JSONObject item = arr.optJSONObject(i);
            if (item == null) continue;
            String id = item.optString("category_id", "");
            String name = item.optString("category_name", "Categoría");
            if (!q.isEmpty() && !name.toLowerCase(Locale.ROOT).contains(q)) continue;
            Button b = listButton(name);
            b.setOnClickListener(v -> loadItems(type, id, name));
            list.addView(b);
        }
    }

    private void loadAllItemsClone(String type, String categoryName) {
        String action = "live".equals(type) ? "get_live_streams" :
                "vod".equals(type) ? "get_vod_streams" : "get_series";
        showLoading("Cargando " + categoryName + "…");
        io.execute(() -> {
            try {
                JSONArray arr = new JSONArray(request(action, null));
                ui.post(() -> showItems(type, "", categoryName, arr));
            } catch (Exception e) {
                ui.post(() -> showErrorScreen("No se pudo cargar el contenido", e, () -> loadCategories(type)));
            }
        });
    }

    private void loadItems'''
s, n = re.subn(categories_pattern, categories_repl, s, flags=re.S)
if n != 1:
    raise SystemExit(f'clone categories replacement count={n}')

# Clone content header/grid without touching playback logic
items_pattern = r'    private void showItems\(String type, String categoryId, String categoryName, JSONArray arr\) \{.*?\n    \}\n\n    private void renderItems'
items_repl = r'''    private void showItems(String type, String categoryId, String categoryName, JSONArray arr) {
        Runnable back = () -> loadCategories(type);
        systemBack = back;
        root = cloneScreen();
        addCloneHeader(categoryName, back);

        LinearLayout top = new LinearLayout(this);
        top.setOrientation(LinearLayout.HORIZONTAL);
        top.setGravity(Gravity.CENTER_VERTICAL);
        EditText search = input("Buscar", false);
        top.addView(search, new LinearLayout.LayoutParams(0, dp(54), 1f));
        TextView menu = label("⋮");
        menu.setTextSize(34);
        menu.setGravity(Gravity.CENTER);
        top.addView(menu, new LinearLayout.LayoutParams(dp(56), dp(54)));
        root.addView(top);

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
s, n = re.subn(items_pattern, items_repl, s, flags=re.S)
if n != 1:
    raise SystemExit(f'clone showItems replacement count={n}')

# Convert current detailed settings into a submenu and create screenshot-matched settings hub
settings_pattern = r'    private void showSettings\(\) \{.*?\n    \}\n\n    private String playerModeLabel'
settings_repl = r'''    private void showSettings() {
        systemBack = this::showDashboard;
        root = cloneScreen();
        addCloneHeader("AJUSTES", this::showDashboard);

        GridLayout grid = new GridLayout(this);
        grid.setColumnCount(3);
        grid.setUseDefaultMargins(false);
        root.addView(grid);

        addCloneSettingsTile(grid, "⚙", "Ajustes", this::showCloneGeneralSettings);
        addCloneSettingsTile(grid, "◷", "GUÍA", this::loadNowNextGuide);
        addCloneSettingsTile(grid, "▣", "Formato de reproduccion", this::showClonePlaybackFormat);
        addCloneSettingsTile(grid, "◴", "Formato de Hora", this::showCloneTimeFormat);
        addCloneSettingsTile(grid, "⚙", "Automatización", this::showCloneAutomation);
        addCloneSettingsTile(grid, "♢", "Control Parental", this::showParentalSettings);

        TextView version = label("v2.2.0");
        version.setTextColor(Color.rgb(130, 140, 165));
        version.setGravity(Gravity.CENTER);
        version.setPadding(0, dp(18), 0, 0);
        root.addView(version);
    }

    private void addCloneSettingsTile(GridLayout grid, String iconText, String titleText, Runnable action) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setGravity(Gravity.CENTER);
        card.setBackgroundResource(R.drawable.clone_tile_bg);
        card.setFocusable(true);
        card.setClickable(true);
        decorateCardFocus(card);
        card.setOnClickListener(v -> action.run());

        TextView icon = label(iconText);
        icon.setTextColor(Color.rgb(61, 118, 222));
        icon.setTextSize(48);
        icon.setGravity(Gravity.CENTER);
        card.addView(icon, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(92)));

        TextView title = label(titleText);
        title.setTextSize(17);
        title.setGravity(Gravity.CENTER);
        card.addView(title, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(56)));

        GridLayout.LayoutParams gp = new GridLayout.LayoutParams();
        gp.width = 0;
        gp.height = dp(180);
        gp.columnSpec = GridLayout.spec(GridLayout.UNDEFINED, 1f);
        gp.setMargins(dp(14), dp(12), dp(14), dp(12));
        card.setLayoutParams(gp);
        grid.addView(card);
    }

    private void showCloneGeneralSettings() {
        systemBack = this::showSettings;
        root = cloneScreen();
        addCloneHeader("Ajustes  |  Ajustes", this::showSettings);

        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setBackgroundResource(R.drawable.clone_panel_bg);
        panel.setPadding(dp(56), dp(20), dp(56), dp(20));
        root.addView(panel);

        panel.addView(cloneCheck("Autoboot en inicio", prefs != null && prefs.getBoolean("clone_autoboot", true),
                "clone_autoboot"));
        panel.addView(cloneCheck("Mostrar la guía completa", prefs == null || prefs.getBoolean("clone_full_guide", true),
                "clone_full_guide"));
        panel.addView(cloneCheck("Subtítulo activo", prefs == null || prefs.getBoolean("clone_subtitles_on", true),
                "clone_subtitles_on"));
        panel.addView(cloneCheck("Reproducción automática del próximo episodio en 30s",
                prefs == null || prefs.getBoolean("clone_autonext", true), "clone_autonext"));
        panel.addView(cloneCheck("Imagen en imagen", prefs == null || prefs.getBoolean("clone_pip", true),
                "clone_pip"));
        panel.addView(cloneCheck("Auto Clear Cache", prefs == null || prefs.getBoolean("clone_clear_cache", true),
                "clone_clear_cache"));

        Button clear = cloneGrayButton("DESPEJADO AHORA");
        clear.setOnClickListener(v -> {
            artCache.evictAll();
            Toast.makeText(this, "Caché visual despejada.", Toast.LENGTH_SHORT).show();
        });
        panel.addView(clear);

        Button picker = cloneGrayButton("ELIGE REPRODUCTOR");
        picker.setOnClickListener(v -> showClonePlayerPicker());
        panel.addView(picker);

        Button decoder = cloneGrayButton("CONFIGURAR REPRODUCTOR");
        decoder.setOnClickListener(v -> showCloneDecoderSettings());
        panel.addView(decoder);

        Button engine = cloneGrayButton("MOTOR DE REPRODUCCIÓN");
        engine.setOnClickListener(v -> showPlayerEngineSettings());
        panel.addView(engine);
    }

    private CheckBox cloneCheck(String text, boolean checked, String key) {
        CheckBox box = new CheckBox(this);
        box.setText(text);
        box.setTextColor(Color.WHITE);
        box.setTextSize(18);
        box.setChecked(checked);
        box.setPadding(dp(8), dp(8), dp(8), dp(8));
        box.setFocusable(true);
        box.setOnCheckedChangeListener((buttonView, value) -> {
            if (prefs != null) prefs.edit().putBoolean(key, value).apply();
        });
        return box;
    }

    private void showClonePlaybackFormat() {
        systemBack = this::showSettings;
        root = cloneScreen();
        addCloneHeader("Ajustes  |  Formato de Reproduccion", this::showSettings);

        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setBackgroundResource(R.drawable.clone_panel_bg);
        panel.setPadding(dp(60), dp(22), dp(60), dp(22));
        root.addView(panel);

        TextView title = label("Formato de Reproduccion");
        title.setTextSize(24);
        title.setGravity(Gravity.CENTER);
        title.setPadding(0, 0, 0, dp(20));
        panel.addView(title);

        android.widget.RadioGroup group = new android.widget.RadioGroup(this);
        group.setOrientation(android.widget.RadioGroup.VERTICAL);
        String saved = prefs == null ? "ts" : prefs.getString("clone_stream_format", "ts");
        String[] values = {"default", "ts", "m3u8"};
        String[] labels = {"Default", "MPEGTS (.ts)", "HLS (.m3u8)"};
        for (int i = 0; i < values.length; i++) {
            android.widget.RadioButton radio = new android.widget.RadioButton(this);
            radio.setText(labels[i]);
            radio.setTextColor(Color.WHITE);
            radio.setTextSize(20);
            radio.setPadding(dp(10), dp(10), dp(10), dp(10));
            radio.setTag(values[i]);
            radio.setChecked(values[i].equals(saved));
            group.addView(radio);
        }
        panel.addView(group);

        LinearLayout buttons = cloneBottomButtons("GUARDAR CAMBIOS", "ATRÁS",
                () -> {
                    int id = group.getCheckedRadioButtonId();
                    android.widget.RadioButton selected = group.findViewById(id);
                    if (selected != null && prefs != null) {
                        prefs.edit().putString("clone_stream_format", String.valueOf(selected.getTag())).apply();
                    }
                    Toast.makeText(this, "Formato guardado.", Toast.LENGTH_SHORT).show();
                }, this::showSettings);
        root.addView(buttons);
    }

    private void showCloneTimeFormat() {
        systemBack = this::showSettings;
        root = cloneScreen();
        addCloneHeader("Ajustes  |  Formato de Hora", this::showSettings);

        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setBackgroundResource(R.drawable.clone_panel_bg);
        panel.setPadding(dp(60), dp(22), dp(60), dp(22));
        root.addView(panel);

        TextView title = label("Formato de Hora");
        title.setTextSize(24);
        title.setGravity(Gravity.CENTER);
        panel.addView(title);

        android.widget.RadioGroup group = new android.widget.RadioGroup(this);
        group.setOrientation(android.widget.RadioGroup.VERTICAL);
        boolean use24 = prefs != null && prefs.getBoolean("clone_clock_24", false);
        android.widget.RadioButton r12 = new android.widget.RadioButton(this);
        r12.setText("12 Horas");
        r12.setTextColor(Color.WHITE);
        r12.setTextSize(20);
        r12.setChecked(!use24);
        group.addView(r12);
        android.widget.RadioButton r24 = new android.widget.RadioButton(this);
        r24.setText("24 Horas");
        r24.setTextColor(Color.WHITE);
        r24.setTextSize(20);
        r24.setChecked(use24);
        group.addView(r24);
        panel.addView(group);

        root.addView(cloneBottomButtons("GUARDAR CAMBIOS", "ATRÁS",
                () -> {
                    if (prefs != null) prefs.edit().putBoolean("clone_clock_24", r24.isChecked()).apply();
                    Toast.makeText(this, "Formato de hora guardado.", Toast.LENGTH_SHORT).show();
                }, this::showSettings));
    }

    private void showCloneAutomation() {
        systemBack = this::showSettings;
        root = cloneScreen();
        addCloneHeader("Ajustes  |  Automatización", this::showSettings);

        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setBackgroundResource(R.drawable.clone_panel_bg);
        panel.setPadding(dp(44), dp(20), dp(44), dp(20));
        root.addView(panel);

        TextView title = label("Automatización");
        title.setTextSize(24);
        title.setGravity(Gravity.CENTER);
        title.setPadding(0, 0, 0, dp(16));
        panel.addView(title);

        panel.addView(cloneCheck("Actualización automática en vivo, películas & Serie después de cada 2 Día(s)",
                prefs == null || prefs.getBoolean("clone_auto_content", true), "clone_auto_content"));
        panel.addView(cloneCheck("Actualización automática de EPG después de cada 1 Día(s)",
                prefs == null || prefs.getBoolean("clone_auto_epg", true), "clone_auto_epg"));

        root.addView(cloneBottomButtons("GUARDAR CAMBIOS", "ATRÁS",
                () -> Toast.makeText(this, "Cambios guardados.", Toast.LENGTH_SHORT).show(),
                this::showSettings));
    }

    private LinearLayout cloneBottomButtons(String leftText, String rightText,
                                            Runnable leftAction, Runnable rightAction) {
        LinearLayout row = new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        row.setGravity(Gravity.CENTER);
        row.setPadding(dp(30), dp(18), dp(30), 0);

        Button left = cloneGreenButton(leftText);
        left.setOnClickListener(v -> leftAction.run());
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(0, dp(62), 1f);
        lp.setMargins(dp(10), 0, dp(30), 0);
        row.addView(left, lp);

        Button right = cloneRedButton(rightText);
        right.setOnClickListener(v -> rightAction.run());
        LinearLayout.LayoutParams rp = new LinearLayout.LayoutParams(0, dp(62), 1f);
        rp.setMargins(dp(30), 0, dp(10), 0);
        row.addView(right, rp);
        return row;
    }

    private void showClonePlayerPicker() {
        systemBack = this::showCloneGeneralSettings;
        root = cloneScreen();
        addCloneHeader("Ajustes  |  Elige Reproductor", this::showCloneGeneralSettings);

        Button add = cloneGrayButton("＋  AÑADIR MEDIAPLAYER");
        add.setOnClickListener(v -> openExternalPlayer());
        root.addView(add);

        String[] labels = {"DIRECTO", "CINE", "SERIES", "CATCH UP", "GRABACIÓN"};
        for (String labelText : labels) {
            LinearLayout row = new LinearLayout(this);
            row.setOrientation(LinearLayout.HORIZONTAL);
            row.setGravity(Gravity.CENTER_VERTICAL);
            TextView label = label(labelText);
            label.setTypeface(Typeface.DEFAULT_BOLD);
            label.setTextSize(18);
            row.addView(label, new LinearLayout.LayoutParams(dp(300), dp(76)));

            Button builtIn = new Button(this);
            builtIn.setText("Built-in Player (Hardware/Software Decoder)");
            builtIn.setTextColor(Color.rgb(25, 25, 25));
            builtIn.setTextSize(18);
            builtIn.setAllCaps(false);
            builtIn.setBackgroundColor(Color.rgb(168, 176, 195));
            builtIn.setOnClickListener(v -> showPlayerEngineSettings());
            row.addView(builtIn, new LinearLayout.LayoutParams(0, dp(64), 1f));
            root.addView(row);
        }
    }

    private void showCloneDecoderSettings() {
        systemBack = this::showCloneGeneralSettings;
        root = cloneScreen();
        addCloneHeader("Ajustes  |  Configurar Reproductor", this::showCloneGeneralSettings);

        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setBackgroundResource(R.drawable.clone_panel_bg);
        panel.setPadding(dp(70), dp(20), dp(70), dp(20));
        root.addView(panel);

        TextView title = label("Configuración incorporada del reproductor");
        title.setTextSize(24);
        title.setGravity(Gravity.CENTER);
        title.setPadding(0, 0, 0, dp(18));
        panel.addView(title);

        android.widget.RadioGroup group = new android.widget.RadioGroup(this);
        group.setOrientation(android.widget.RadioGroup.VERTICAL);
        boolean software = prefs != null && prefs.getBoolean("clone_software_decoder", false);
        android.widget.RadioButton hw = new android.widget.RadioButton(this);
        hw.setText("Hardware Decoder");
        hw.setTextColor(Color.WHITE);
        hw.setTextSize(18);
        hw.setChecked(!software);
        group.addView(hw);
        android.widget.RadioButton sw = new android.widget.RadioButton(this);
        sw.setText("Software Decoder");
        sw.setTextColor(Color.WHITE);
        sw.setTextSize(18);
        sw.setChecked(software);
        group.addView(sw);
        panel.addView(group);

        TextView buffer = label("Límite de tamaño de búfer     20⌄");
        buffer.setTextSize(18);
        buffer.setPadding(dp(8), dp(12), 0, dp(12));
        panel.addView(buffer);

        panel.addView(cloneCheck("Habilitar OpenSL ES (audio acelerado por hardware)",
                prefs != null && prefs.getBoolean("clone_opensl", false), "clone_opensl"));
        panel.addView(cloneCheck("Habilitar OpenGL (formato de píxel OpenGL)",
                prefs != null && prefs.getBoolean("clone_opengl", false), "clone_opengl"));

        root.addView(cloneBottomButtons("GUARDAR", "ATRÁS",
                () -> {
                    if (prefs != null) prefs.edit().putBoolean("clone_software_decoder", sw.isChecked()).apply();
                    Toast.makeText(this, "Configuración guardada.", Toast.LENGTH_SHORT).show();
                }, this::showCloneGeneralSettings));
    }

    private void showPlayerEngineSettings() {
        systemBack = this::showCloneGeneralSettings;
        root = cloneScreen();
        addCloneHeader("Ajustes  |  Motor de Reproducción", this::showCloneGeneralSettings);

        String mode = prefs == null ? "auto" : prefs.getString("player_mode", "auto");
        int cache = prefs == null ? 2500 : prefs.getInt("network_cache_ms", 2500);
        boolean immersive = prefs != null && prefs.getBoolean("immersive_player", true);

        root.addView(cardText("Reproductor: " + playerModeLabel(mode)
                + "\nCaché de red: " + cache + " ms"
                + "\nModo inmersivo: " + (immersive ? "Sí" : "No")));

        Button auto = actionButton(("auto".equals(mode) ? "✓  " : "") + "AUTOMÁTICO · EXO + VLC");
        auto.setOnClickListener(v -> setPlayerMode("auto"));
        root.addView(auto);

        Button exo = secondaryButton(("exo".equals(mode) ? "✓  " : "") + "FORZAR EXOPLAYER");
        exo.setOnClickListener(v -> setPlayerMode("exo"));
        root.addView(exo);

        Button vlc = secondaryButton(("vlc".equals(mode) ? "✓  " : "") + "FORZAR VLC");
        vlc.setOnClickListener(v -> setPlayerMode("vlc"));
        root.addView(vlc);

        Button low = secondaryButton((cache == 1500 ? "✓  " : "") + "CACHÉ RÁPIDO · 1500 ms");
        low.setOnClickListener(v -> setNetworkCache(1500));
        root.addView(low);

        Button normal = secondaryButton((cache == 2500 ? "✓  " : "") + "CACHÉ NORMAL · 2500 ms");
        normal.setOnClickListener(v -> setNetworkCache(2500));
        root.addView(normal);

        Button stable = secondaryButton((cache == 5000 ? "✓  " : "") + "CACHÉ ESTABLE · 5000 ms");
        stable.setOnClickListener(v -> setNetworkCache(5000));
        root.addView(stable);

        CheckBox immersiveBox = new CheckBox(this);
        immersiveBox.setText("Pantalla completa inmersiva al reproducir");
        immersiveBox.setTextColor(Color.WHITE);
        immersiveBox.setChecked(immersive);
        immersiveBox.setPadding(dp(4), dp(12), dp(4), dp(12));
        immersiveBox.setOnCheckedChangeListener((buttonView, checked) -> {
            if (prefs != null) prefs.edit().putBoolean("immersive_player", checked).apply();
        });
        root.addView(immersiveBox);
    }

    private String playerModeLabel'''
s, n = re.subn(settings_pattern, settings_repl, s, flags=re.S)
if n != 1:
    raise SystemExit(f'clone settings replacement count={n}')

s = s.replace('        showSettings();\n    }\n\n    private void setNetworkCache',
              '        showPlayerEngineSettings();\n    }\n\n    private void setNetworkCache', 1)
s = s.replace('        showSettings();\n    }\n\n    private void loadCatchupChannels',
              '        showPlayerEngineSettings();\n    }\n\n    private void loadCatchupChannels', 1)

# Clone subscription info
account_pattern = r'    private void showAccount\(\) \{.*?\n    \}\n\n    private void playStream'
account_repl = r'''    private void showAccount() {
        systemBack = this::showDashboard;
        root = cloneScreen();
        addCloneHeader("Subscription Info", this::showDashboard);

        if (accountInfo == null) {
            root.addView(cardText("No hay información de cuenta disponible."));
            return;
        }

        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setBackgroundResource(R.drawable.clone_panel_bg);
        panel.setPadding(dp(120), dp(18), dp(120), dp(18));
        root.addView(panel);

        TextView title = label("Subscription Info");
        title.setTextSize(22);
        title.setGravity(Gravity.CENTER);
        title.setPadding(0, 0, 0, dp(16));
        panel.addView(title);

        addCloneInfoRow(panel, "Usuario:", accountInfo.optString("username", username));
        addCloneInfoRow(panel, "Estado:", accountInfo.optString("status", "—"));
        addCloneInfoRow(panel, "Expiracion Activas:", formatEpoch(accountInfo.optString("exp_date", "")));
        addCloneInfoRow(panel, "Prueba:", "1".equals(String.valueOf(accountInfo.opt("is_trial"))) ? "SI" : "NO");
        addCloneInfoRow(panel, "Conexiones:", accountInfo.optString("active_cons", "N/A"));
        addCloneInfoRow(panel, "Creado:", formatEpoch(accountInfo.optString("created_at", "")));
        addCloneInfoRow(panel, "Conexiones Máximas:", accountInfo.optString("max_connections", "—"));
    }

    private void addCloneInfoRow(LinearLayout panel, String leftText, String rightText) {
        LinearLayout row = new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        TextView left = label(leftText);
        left.setTextSize(20);
        row.addView(left, new LinearLayout.LayoutParams(0, dp(48), 1f));
        TextView right = label(rightText == null || rightText.isEmpty() ? "N/A" : rightText);
        right.setTextSize(20);
        row.addView(right, new LinearLayout.LayoutParams(0, dp(48), 1f));
        panel.addView(row);
    }

    private void playStream'''
s, n = re.subn(account_pattern, account_repl, s, flags=re.S)
if n != 1:
    raise SystemExit(f'clone account replacement count={n}')

# Clone movie detail screen
vod_pattern = r'    private void showVodDetails\(String id, String fallbackTitle, String ext, String fallbackArt,\n                                JSONObject payload, Runnable back\) \{.*?\n    \}\n\n    private void addSeriesInfoHeader'
vod_repl = r'''    private void showVodDetails(String id, String fallbackTitle, String ext, String fallbackArt,
                                JSONObject payload, Runnable back) {
        systemBack = back;
        root = cloneScreen();

        JSONObject movieData = payload.optJSONObject("movie_data");
        JSONObject info = payload.optJSONObject("info");
        String title = movieData == null ? fallbackTitle : movieData.optString("name", fallbackTitle);
        addCloneHeader(title, back);

        String art = fallbackArt == null ? "" : fallbackArt;
        if (movieData != null) art = movieData.optString("stream_icon", movieData.optString("cover_big", art));
        if (info != null) art = info.optString("movie_image", info.optString("cover_big", art));

        String plot = info == null ? "" : info.optString("plot", "");
        String genre = info == null ? "" : info.optString("genre", "");
        String release = info == null ? "" : info.optString("releasedate", info.optString("releaseDate", ""));
        String rating = info == null ? "" : info.optString("rating", "");
        String duration = info == null ? "" : info.optString("duration", "");
        String cast = info == null ? "" : info.optString("cast", "");
        String director = info == null ? "" : info.optString("director", "");

        LinearLayout body = new LinearLayout(this);
        body.setOrientation(LinearLayout.HORIZONTAL);
        body.setGravity(Gravity.TOP);
        root.addView(body);

        LinearLayout left = new LinearLayout(this);
        left.setOrientation(LinearLayout.VERTICAL);
        left.setGravity(Gravity.CENTER_HORIZONTAL);
        ImageView poster = new ImageView(this);
        poster.setImageResource(R.drawable.poster_placeholder);
        poster.setScaleType(ImageView.ScaleType.CENTER_CROP);
        left.addView(poster, new LinearLayout.LayoutParams(dp(240), dp(370)));
        loadArtwork(art, poster);
        TextView stars = label(cloneStars(rating));
        stars.setTextSize(28);
        stars.setTextColor(Color.YELLOW);
        stars.setGravity(Gravity.CENTER);
        left.addView(stars, new LinearLayout.LayoutParams(dp(250), dp(52)));
        body.addView(left, new LinearLayout.LayoutParams(dp(280), ViewGroup.LayoutParams.WRAP_CONTENT));

        LinearLayout details = new LinearLayout(this);
        details.setOrientation(LinearLayout.VERTICAL);
        details.setPadding(dp(25), 0, dp(10), 0);
        body.addView(details, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        addCloneMovieMeta(details, "Dirigido:", director);
        addCloneMovieMeta(details, "Lanzamiento:", release);
        addCloneMovieMeta(details, "Duración:", duration);
        addCloneMovieMeta(details, "Género:", genre);
        addCloneMovieMeta(details, "Emitir:", cast);

        long saved = getSavedPosition("vod", id);
        String url = server + "/movie/" + encPath(username) + "/" + encPath(password) + "/" + id + "." + ext;
        String finalTitle = title;
        String finalArt = art;

        LinearLayout actions = new LinearLayout(this);
        actions.setOrientation(LinearLayout.HORIZONTAL);
        actions.setGravity(Gravity.CENTER);
        actions.setPadding(0, dp(20), 0, 0);

        Button play = cloneGrayButton(saved > 60000 ? "Continuar" : "Play");
        play.setTextSize(18);
        play.setOnClickListener(v -> startTrackedPlayback("vod", id, finalTitle, ext, finalArt, url,
                () -> showVodDetails(id, fallbackTitle, ext, fallbackArt, payload, back)));
        LinearLayout.LayoutParams ap = new LinearLayout.LayoutParams(0, dp(62), 1f);
        ap.setMargins(dp(6), 0, dp(6), 0);
        actions.addView(play, ap);

        Button download = cloneGrayButton("Download");
        download.setTextSize(18);
        download.setOnClickListener(v -> downloadVod(finalTitle, url, ext));
        actions.addView(download, ap);

        Button favorite = cloneGrayButton(isFavorite("vod", id) ? "♥" : "♡");
        favorite.setTextSize(28);
        favorite.setOnClickListener(v -> {
            toggleFavorite("vod", id);
            favorite.setText(isFavorite("vod", id) ? "♥" : "♡");
        });
        LinearLayout.LayoutParams fp = new LinearLayout.LayoutParams(dp(72), dp(62));
        fp.setMargins(dp(6), 0, dp(6), 0);
        actions.addView(favorite, fp);
        details.addView(actions);

        if (saved > 0) {
            Button restart = cloneGrayButton("↺ Ver desde el inicio");
            restart.setOnClickListener(v -> {
                clearSavedPosition("vod", id);
                startTrackedPlayback("vod", id, finalTitle, ext, finalArt, url,
                        () -> showVodDetails(id, fallbackTitle, ext, fallbackArt, payload, back));
            });
            details.addView(restart, new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT, dp(54)));
        }

        if (!plot.isEmpty()) {
            TextView description = label(plot);
            description.setTextSize(18);
            description.setTextColor(Color.rgb(215, 218, 229));
            description.setPadding(dp(10), dp(18), dp(10), dp(10));
            root.addView(description);
        }
    }

    private void addCloneMovieMeta(LinearLayout parent, String labelText, String valueText) {
        LinearLayout row = new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        TextView left = label(labelText);
        left.setTypeface(Typeface.DEFAULT_BOLD);
        left.setTextSize(18);
        row.addView(left, new LinearLayout.LayoutParams(dp(260), dp(56)));
        TextView right = label(valueText == null || valueText.isEmpty() ? "—" : valueText);
        right.setTextSize(18);
        right.setTextColor(Color.rgb(210, 213, 224));
        right.setMaxLines(2);
        right.setEllipsize(TextUtils.TruncateAt.END);
        row.addView(right, new LinearLayout.LayoutParams(0, dp(56), 1f));
        parent.addView(row);
    }

    private String cloneStars(String ratingText) {
        int stars = 0;
        try {
            double rating = Double.parseDouble(ratingText);
            stars = (int) Math.round(rating / 2.0);
        } catch (Exception ignored) {}
        stars = Math.max(0, Math.min(5, stars));
        StringBuilder out = new StringBuilder();
        for (int i = 0; i < 5; i++) out.append(i < stars ? "★" : "☆");
        return out.toString();
    }

    private void addSeriesInfoHeader'''
s, n = re.subn(vod_pattern, vod_repl, s, flags=re.S)
if n != 1:
    raise SystemExit(f'clone VOD replacement count={n}')

p.write_text(s)
print('PIMFLEX clone UI v2.2 patch applied')
