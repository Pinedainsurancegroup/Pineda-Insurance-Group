from pathlib import Path
import re

p = Path('app/src/main/java/com/pimflextv/next/MainActivity.java')
s = p.read_text()

field = '    private String lastGlobalQuery = "";\n'
if field in s and 'private JSONArray cloneCategoryArray' not in s:
    s = s.replace(field, field + '''    private JSONArray cloneCategoryArray = new JSONArray();
    private String cloneCategoryType = "";
''', 1)

# Preserve currently loaded categories for the split browser.
needle = '''    private void showCategories(String type, JSONArray arr) {
        systemBack = this::showDashboard;
'''
repl = '''    private void showCategories(String type, JSONArray arr) {
        cloneCategoryType = type;
        cloneCategoryArray = arr == null ? new JSONArray() : arr;
        systemBack = this::showDashboard;
'''
if needle not in s:
    raise SystemExit('showCategories header not found')
s = s.replace(needle, repl, 1)

# Replace item browser with the original-style split layout.
pattern = r'    private void showItems\(String type, String categoryId, String categoryName, JSONArray arr\) \{.*?\n    \}\n\n    private void renderItems'
replacement = r'''    private void showItems(String type, String categoryId, String categoryName, JSONArray arr) {
        Runnable back = () -> loadCategories(type);
        systemBack = back;
        root = cloneScreen();
        addCloneHeader("", back);

        LinearLayout browser = new LinearLayout(this);
        browser.setOrientation(LinearLayout.HORIZONTAL);
        browser.setGravity(Gravity.TOP);
        root.addView(browser, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        LinearLayout sidebar = new LinearLayout(this);
        sidebar.setOrientation(LinearLayout.VERTICAL);
        sidebar.setBackgroundColor(Color.BLACK);
        sidebar.setPadding(dp(10), dp(8), dp(10), dp(12));
        browser.addView(sidebar, new LinearLayout.LayoutParams(
                dp(isTvLayout() ? 360 : 300), ViewGroup.LayoutParams.WRAP_CONTENT));

        TextView sideLogo = label("PT  PIMFLEX TV");
        sideLogo.setTypeface(Typeface.DEFAULT_BOLD);
        sideLogo.setTextColor(Color.WHITE);
        sideLogo.setTextSize(17);
        sideLogo.setGravity(Gravity.CENTER);
        sideLogo.setPadding(0, dp(4), 0, dp(10));
        sidebar.addView(sideLogo);

        EditText catSearch = input("⌕ Buscar en categorías", false);
        catSearch.setBackgroundColor(Color.rgb(28, 28, 28));
        sidebar.addView(catSearch, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(52)));

        LinearLayout categoryList = new LinearLayout(this);
        categoryList.setOrientation(LinearLayout.VERTICAL);
        sidebar.addView(categoryList);
        renderCloneBrowserCategories(categoryList, type, categoryId, "");

        LinearLayout content = new LinearLayout(this);
        content.setOrientation(LinearLayout.VERTICAL);
        content.setPadding(dp(14), 0, 0, 0);
        browser.addView(content, new LinearLayout.LayoutParams(
                0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        LinearLayout top = new LinearLayout(this);
        top.setOrientation(LinearLayout.HORIZONTAL);
        top.setGravity(Gravity.CENTER_VERTICAL);

        TextView title = label(categoryName == null || categoryName.isEmpty() ? "TODO" : categoryName);
        title.setTextSize(22);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setGravity(Gravity.CENTER);
        top.addView(title, new LinearLayout.LayoutParams(0, dp(56), 1f));

        TextView searchIcon = label("⌕");
        searchIcon.setTextSize(34);
        searchIcon.setGravity(Gravity.CENTER);
        top.addView(searchIcon, new LinearLayout.LayoutParams(dp(58), dp(56)));

        TextView dots = label("⋮");
        dots.setTextSize(32);
        dots.setGravity(Gravity.CENTER);
        top.addView(dots, new LinearLayout.LayoutParams(dp(50), dp(56)));
        content.addView(top);

        EditText contentSearch = input("Buscar contenido", false);
        contentSearch.setVisibility(View.GONE);
        content.addView(contentSearch);

        GridLayout grid = new GridLayout(this);
        grid.setColumnCount(Math.max(3, posterColumns()));
        grid.setUseDefaultMargins(false);
        content.addView(grid);

        if ("live".equals(type)) {
            renderCloneLiveGrid(grid, categoryId, categoryName, arr, "");
        } else {
            renderPosterGrid(grid, type, categoryId, categoryName, arr, "");
        }

        searchIcon.setOnClickListener(v -> {
            contentSearch.setVisibility(contentSearch.getVisibility() == View.VISIBLE ? View.GONE : View.VISIBLE);
            if (contentSearch.getVisibility() == View.VISIBLE) contentSearch.requestFocus();
        });

        contentSearch.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
            @Override public void onTextChanged(CharSequence text, int start, int before, int count) {
                String q = text == null ? "" : text.toString();
                if ("live".equals(type)) {
                    renderCloneLiveGrid(grid, categoryId, categoryName, arr, q);
                } else {
                    renderPosterGrid(grid, type, categoryId, categoryName, arr, q);
                }
            }
            @Override public void afterTextChanged(Editable s) {}
        });

        catSearch.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
            @Override public void onTextChanged(CharSequence text, int start, int before, int count) {
                renderCloneBrowserCategories(categoryList, type, categoryId,
                        text == null ? "" : text.toString());
            }
            @Override public void afterTextChanged(Editable s) {}
        });
    }

    private void renderCloneBrowserCategories(LinearLayout list, String type, String selectedCategoryId,
                                              String query) {
        list.removeAllViews();
        String q = query == null ? "" : query.trim().toLowerCase(Locale.ROOT);

        Button all = listButton("TODO");
        all.setBackgroundColor(selectedCategoryId == null || selectedCategoryId.isEmpty()
                ? Color.rgb(47, 146, 230) : Color.BLACK);
        all.setOnClickListener(v -> loadAllItemsClone(type, "TODO"));
        list.addView(all);

        Button fav = listButton("FAVORITOS");
        fav.setBackgroundColor(Color.BLACK);
        fav.setOnClickListener(v -> loadFavorites());
        list.addView(fav);

        if ("live".equals(type)) {
            Button history = listButton("CHANNELS HISTORY");
            history.setBackgroundColor(Color.BLACK);
            history.setOnClickListener(v -> showWatchHistory(false));
            list.addView(history);
        } else if ("vod".equals(type)) {
            Button recent = listButton("RECIENTEMENTE MIRADA");
            recent.setBackgroundColor(Color.BLACK);
            recent.setOnClickListener(v -> showWatchHistory(false));
            list.addView(recent);
        }

        JSONArray categories = type.equals(cloneCategoryType) ? cloneCategoryArray : new JSONArray();
        for (int i = 0; i < categories.length(); i++) {
            JSONObject item = categories.optJSONObject(i);
            if (item == null) continue;
            String id = item.optString("category_id", "");
            String name = item.optString("category_name", "Categoría");
            if (!q.isEmpty() && !name.toLowerCase(Locale.ROOT).contains(q)) continue;

            Button b = listButton(name);
            b.setBackgroundColor(id.equals(selectedCategoryId) ? Color.rgb(47, 146, 230) : Color.BLACK);
            b.setOnClickListener(v -> loadItems(type, id, name));
            list.addView(b);
        }
    }

    private void renderCloneLiveGrid(GridLayout grid, String categoryId, String categoryName,
                                     JSONArray arr, String query) {
        grid.removeAllViews();
        int cols = Math.max(3, posterColumns());
        grid.setColumnCount(cols);
        String q = query == null ? "" : query.trim().toLowerCase(Locale.ROOT);

        int widthDp = Math.round(getResources().getDisplayMetrics().widthPixels /
                getResources().getDisplayMetrics().density);
        int available = Math.max(440, widthDp - (isTvLayout() ? 430 : 355));
        int cardWidth = Math.max(108, (available - (cols - 1) * 8) / cols);
        int shown = 0;

        for (int i = 0; i < arr.length() && shown < 350; i++) {
            JSONObject item = arr.optJSONObject(i);
            if (item == null) continue;
            String name = item.optString("name", "Canal");
            if (!q.isEmpty() && !name.toLowerCase(Locale.ROOT).contains(q)) continue;
            String id = String.valueOf(item.opt("stream_id"));

            LinearLayout card = new LinearLayout(this);
            card.setOrientation(LinearLayout.VERTICAL);
            card.setBackgroundResource(R.drawable.clone_tile_bg);
            card.setPadding(dp(3), dp(3), dp(3), dp(4));
            card.setFocusable(true);
            card.setClickable(true);
            decorateCardFocus(card);

            GridLayout.LayoutParams gp = new GridLayout.LayoutParams();
            gp.width = dp(cardWidth);
            gp.height = dp(Math.round(cardWidth * 1.15f));
            gp.setMargins(dp(3), dp(3), dp(3), dp(3));
            card.setLayoutParams(gp);

            ImageView art = new ImageView(this);
            art.setScaleType(ImageView.ScaleType.CENTER_CROP);
            art.setImageResource(R.drawable.poster_placeholder);
            loadArtwork(item.optString("stream_icon", ""), art);
            card.addView(art, new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));

            TextView label = this.label(name);
            label.setTextSize(13);
            label.setMaxLines(2);
            label.setEllipsize(TextUtils.TruncateAt.END);
            label.setGravity(Gravity.CENTER);
            label.setBackgroundColor(Color.argb(190, 16, 19, 30));
            card.addView(label, new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT, dp(46)));

            int liveIndex = i;
            card.setOnClickListener(v -> runWithParentalGate(name, () ->
                    playLiveWithZapping(arr, liveIndex,
                            () -> showItems("live", categoryId, categoryName, arr))));
            grid.addView(card);
            shown++;
        }

        if (shown == 0) {
            TextView empty = cardText("No se encontraron canales.");
            GridLayout.LayoutParams ep = new GridLayout.LayoutParams();
            ep.width = GridLayout.LayoutParams.MATCH_PARENT;
            ep.height = GridLayout.LayoutParams.WRAP_CONTENT;
            ep.columnSpec = GridLayout.spec(0, cols);
            empty.setLayoutParams(ep);
            grid.addView(empty);
        }
    }

    private void renderItems'''
s, n = re.subn(pattern, replacement, s, flags=re.S)
if n != 1:
    raise SystemExit(f'v2.3 showItems replacement count={n}')

# Expand settings hub with the screens seen in the reference recording.
settings_pattern = r'    private void showSettings\(\) \{.*?\n    \}\n\n    private void addCloneSettingsTile'
settings_repl = r'''    private void showSettings() {
        systemBack = this::showDashboard;
        root = cloneScreen();
        addCloneHeader("AJUSTES", this::showDashboard);

        GridLayout grid = new GridLayout(this);
        grid.setColumnCount(3);
        grid.setUseDefaultMargins(false);
        root.addView(grid);

        addCloneSettingsTile(grid, "⚙", "Ajustes", this::showCloneGeneralSettings);
        addCloneSettingsTile(grid, "◷", "GUÍA", this::showCloneGuideSettings);
        addCloneSettingsTile(grid, "▣", "Formato de reproduccion", this::showClonePlaybackFormat);
        addCloneSettingsTile(grid, "◴", "Formato de Hora", this::showCloneTimeFormat);
        addCloneSettingsTile(grid, "⚙", "Automatización", this::showCloneAutomation);
        addCloneSettingsTile(grid, "♢", "Control Parental", this::showParentalSettings);
        addCloneSettingsTile(grid, "▣", "Elige Reproductor", this::showClonePlayerPicker);
        addCloneSettingsTile(grid, "⚙", "Configurar Reproductor", this::showCloneDecoderSettings);
        addCloneSettingsTile(grid, "◉", "Mediaplayer externos", this::showCloneExternalPlayersSettings);
        addCloneSettingsTile(grid, "▦", "PANTALLA MÚLTIPLE", this::loadMultiScreenChannels);
        addCloneSettingsTile(grid, "⌁", "Prueba de velocidad", this::runSpeedTest);
        addCloneSettingsTile(grid, "PT", "Comprueba la actualización", this::showCloneUpdateCheck);
        addCloneSettingsTile(grid, "▦", "Switch Device Mode", this::showCloneDeviceMode);
        addCloneSettingsTile(grid, "CC", "Subtitles", this::showCloneSubtitleSettings);
        addCloneSettingsTile(grid, "▱", "Feedback", this::sendCloneFeedback);
        addCloneSettingsTile(grid, "▣", "Log in on TV", this::showCloneLoginOnTv);

        TextView version = label("v2.3.0");
        version.setTextColor(Color.rgb(130, 140, 165));
        version.setGravity(Gravity.CENTER);
        version.setPadding(0, dp(18), 0, 0);
        root.addView(version);
    }

    private void showCloneGuideSettings() {
        systemBack = this::showSettings;
        root = cloneScreen();
        addCloneHeader("Ajustes  |  GUÍA", this::showSettings);

        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.HORIZONTAL);
        panel.setBackgroundResource(R.drawable.clone_panel_bg);
        panel.setPadding(dp(16), dp(16), dp(16), dp(16));
        root.addView(panel);

        LinearLayout menu = new LinearLayout(this);
        menu.setOrientation(LinearLayout.VERTICAL);
        menu.setPadding(0, 0, dp(18), 0);
        panel.addView(menu, new LinearLayout.LayoutParams(dp(250), ViewGroup.LayoutParams.WRAP_CONTENT));

        Button sources = cloneGrayButton("FUENTES EPG");
        menu.addView(sources, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(58)));

        Button chrono = cloneGrayButton("EPG CRONOLOGÍA");
        menu.addView(chrono, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(58)));

        Button timeshift = cloneGrayButton("TIMESHIFT EPG");
        timeshift.setBackgroundColor(Color.rgb(47, 146, 230));
        menu.addView(timeshift, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(58)));

        LinearLayout content = new LinearLayout(this);
        content.setOrientation(LinearLayout.VERTICAL);
        panel.addView(content, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        TextView title = label("TIMESHIFT EPG");
        title.setTextSize(20);
        title.setGravity(Gravity.CENTER);
        content.addView(title);

        EditText shift = input("0", false);
        shift.setInputType(InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_FLAG_SIGNED);
        shift.setText(String.valueOf(prefs == null ? 0 : prefs.getInt("clone_epg_timeshift", 0)));
        content.addView(shift, new LinearLayout.LayoutParams(dp(170), dp(56)));

        Button save = cloneGreenButton("GUARDAR CAMBIOS");
        save.setOnClickListener(v -> {
            int value = 0;
            try { value = Integer.parseInt(shift.getText().toString().trim()); } catch (Exception ignored) {}
            if (prefs != null) prefs.edit().putInt("clone_epg_timeshift", value).apply();
            Toast.makeText(this, "EPG guardado.", Toast.LENGTH_SHORT).show();
        });
        content.addView(save, new LinearLayout.LayoutParams(dp(220), dp(58)));
    }

    private void showCloneExternalPlayersSettings() {
        systemBack = this::showSettings;
        root = cloneScreen();
        addCloneHeader("Ajustes  |  Mediaplayer externos", this::showSettings);
        root.addView(cardText("Los reproductores externos se abren desde el botón ↗ EXTERNO del reproductor. "
                + "PIMFLEX TV mantiene el reproductor interno como opción predeterminada."));
        Button back = cloneRedButton("ATRÁS");
        back.setOnClickListener(v -> showSettings());
        root.addView(back);
    }

    private void showCloneUpdateCheck() {
        systemBack = this::showSettings;
        root = cloneScreen();
        addCloneHeader("Ajustes  |  Comprueba la actualización", this::showSettings);
        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setBackgroundResource(R.drawable.clone_panel_bg);
        panel.setPadding(dp(40), dp(28), dp(40), dp(28));
        root.addView(panel);

        TextView heading = label("Versión instalada: v2.3.0");
        heading.setTypeface(Typeface.DEFAULT_BOLD);
        heading.setTextSize(20);
        panel.addView(heading);
        panel.addView(cardText("Las actualizaciones de esta edición son controladas por tu propio proyecto. "
                + "No depende de un servidor de activación externo."));
        Button back = cloneRedButton("ATRÁS");
        back.setOnClickListener(v -> showSettings());
        panel.addView(back);
    }

    private void showCloneDeviceMode() {
        systemBack = this::showSettings;
        root = cloneScreen();
        addCloneHeader("Ajustes  |  Switch Device Mode", this::showSettings);

        android.widget.RadioGroup group = new android.widget.RadioGroup(this);
        group.setOrientation(android.widget.RadioGroup.VERTICAL);
        String current = prefs == null ? "auto" : prefs.getString("clone_device_mode", "auto");

        String[] values = {"auto", "tv", "mobile"};
        String[] labels = {"Automático", "Android TV / pantalla grande", "Teléfono / tablet"};
        for (int i = 0; i < values.length; i++) {
            android.widget.RadioButton radio = new android.widget.RadioButton(this);
            radio.setText(labels[i]);
            radio.setTextColor(Color.WHITE);
            radio.setTextSize(19);
            radio.setTag(values[i]);
            radio.setChecked(values[i].equals(current));
            group.addView(radio);
        }
        root.addView(group);

        root.addView(cloneBottomButtons("GUARDAR", "ATRÁS", () -> {
            int id = group.getCheckedRadioButtonId();
            android.widget.RadioButton selected = group.findViewById(id);
            if (selected != null && prefs != null) {
                prefs.edit().putString("clone_device_mode", String.valueOf(selected.getTag())).apply();
            }
            Toast.makeText(this, "Modo guardado.", Toast.LENGTH_SHORT).show();
        }, this::showSettings));
    }

    private void showCloneSubtitleSettings() {
        systemBack = this::showSettings;
        root = cloneScreen();
        addCloneHeader("Ajustes  |  Subtitles", this::showSettings);

        boolean enabled = prefs == null || prefs.getBoolean("clone_subtitles_on", true);
        CheckBox box = cloneCheck("Subtítulos activos por defecto", enabled, "clone_subtitles_on");
        root.addView(box);

        Button apply = cloneGreenButton("GUARDAR CAMBIOS");
        apply.setOnClickListener(v -> {
            if (prefs != null) {
                prefs.edit()
                        .putString(scopedKey("subtitle_mode"), box.isChecked() ? "auto" : "off")
                        .apply();
            }
            Toast.makeText(this, "Preferencia de subtítulos guardada.", Toast.LENGTH_SHORT).show();
        });
        root.addView(apply);
    }

    private void sendCloneFeedback() {
        try {
            Intent intent = new Intent(Intent.ACTION_SEND);
            intent.setType("text/plain");
            intent.putExtra(Intent.EXTRA_SUBJECT, "PIMFLEX TV Feedback");
            intent.putExtra(Intent.EXTRA_TEXT, "PIMFLEX TV v2.3.0\n\n");
            startActivity(Intent.createChooser(intent, "Enviar feedback"));
        } catch (Exception e) {
            Toast.makeText(this, "No hay una aplicación disponible para enviar feedback.", Toast.LENGTH_LONG).show();
        }
    }

    private void showCloneLoginOnTv() {
        systemBack = this::showSettings;
        root = cloneScreen();
        addCloneHeader("Ajustes  |  Log in on TV", this::showSettings);
        root.addView(cardText("Este acceso conserva tus cuentas guardadas localmente. "
                + "El emparejamiento por código entre dispositivos se puede añadir después con un backend propio."));
        Button accounts = cloneGreenButton("ABRIR CUENTAS");
        accounts.setOnClickListener(v -> showSavedAccounts());
        root.addView(accounts);
    }

    private void addCloneSettingsTile'''
s, n = re.subn(settings_pattern, settings_repl, s, flags=re.S)
if n != 1:
    raise SystemExit(f'v2.3 settings replacement count={n}')

# Add one missing general setting shown in the recording.
needle = '''        panel.addView(cloneCheck("Auto Clear Cache", prefs == null || prefs.getBoolean("clone_clear_cache", true),
                "clone_clear_cache"));

        Button clear = cloneGrayButton("DESPEJADO AHORA");
'''
repl = '''        panel.addView(cloneCheck("Auto Clear Cache", prefs == null || prefs.getBoolean("clone_clear_cache", true),
                "clone_clear_cache"));
        panel.addView(cloneCheck("Mostrar EPG en la lista de canales",
                prefs == null || prefs.getBoolean("clone_epg_in_channel_list", true),
                "clone_epg_in_channel_list"));

        Button clear = cloneGrayButton("DESPEJADO AHORA");
'''
if needle not in s:
    raise SystemExit('general settings insertion marker not found')
s = s.replace(needle, repl, 1)

# Match player picker rows more closely.
s = s.replace('String[] labels = {"DIRECTO", "CINE", "SERIES", "CATCH UP", "GRABACIÓN"};',
              'String[] labels = {"DIRECTO", "CINE", "SERIES", "CATCH UP", "GRABACIÓN", "TV EN DIRECTO CON GUÍA"};', 1)

# Respect the manual device-mode selector without changing playback.
old = '''    private boolean isTvLayout() {
        return getPackageManager().hasSystemFeature("android.software.leanback") ||
                getResources().getConfiguration().smallestScreenWidthDp >= 720;
    }
'''
new = '''    private boolean isTvLayout() {
        if (prefs != null) {
            String mode = prefs.getString("clone_device_mode", "auto");
            if ("tv".equals(mode)) return true;
            if ("mobile".equals(mode)) return false;
        }
        return getPackageManager().hasSystemFeature("android.software.leanback") ||
                getResources().getConfiguration().smallestScreenWidthDp >= 720;
    }
'''
if old not in s:
    raise SystemExit('isTvLayout marker not found')
s = s.replace(old, new, 1)

p.write_text(s)
print('PIMFLEX reference-video UI patch v2.3 applied')
