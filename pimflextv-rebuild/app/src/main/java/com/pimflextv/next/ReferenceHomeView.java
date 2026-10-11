package com.pimflextv.next;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.graphics.drawable.StateListDrawable;
import android.text.TextUtils;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.HorizontalScrollView;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.PopupMenu;
import android.widget.TextClock;
import android.widget.TextView;

/** Original presentation layer. All content and playback stay in MainActivity. */
public final class ReferenceHomeView extends LinearLayout {
    public interface Actions { void open(String destination); }
    private final Actions actions;
    private final boolean compact;
    private final int blue = Color.rgb(77, 137, 241);

    public ReferenceHomeView(Context context, boolean use24, String user, String expiry,
                             String[] updates, Actions actions) {
        super(context);
        this.actions = actions;
        compact = getResources().getConfiguration().screenWidthDp < 760;
        setOrientation(VERTICAL);
        setLayoutParams(new LayoutParams(-1, -2));
        setPadding(dp(2), 0, dp(2), dp(4));

        LinearLayout header = row();
        ImageView logo = new ImageView(context);
        logo.setImageResource(R.drawable.pimflex_brand_exact);
        logo.setContentDescription("PIMFLEX TV");
        logo.setBackgroundColor(Color.WHITE);
        logo.setScaleType(ImageView.ScaleType.FIT_CENTER);
        logo.setPadding(dp(5), dp(3), dp(5), dp(3));
        header.addView(logo, new LayoutParams(dp(compact ? 140 : 185), dp(52)));

        TextClock clock = new TextClock(context);
        clock.setFormat12Hour(use24 ? "HH:mm" : "h:mm a");
        clock.setFormat24Hour(use24 ? "HH:mm" : "h:mm a");
        clock.setTextColor(Color.WHITE);
        clock.setTextSize(compact ? 16 : 20);
        clock.setPadding(dp(14), 0, dp(10), 0);
        header.addView(clock, new LayoutParams(-2, -2));

        TextClock date = new TextClock(context);
        date.setFormat12Hour("EEE, d MMM");
        date.setFormat24Hour("EEE, d MMM");
        date.setTextColor(Color.LTGRAY);
        date.setTextSize(13);
        date.setSingleLine(true);
        date.setEllipsize(TextUtils.TruncateAt.END);
        header.addView(date, new LayoutParams(0, -2, 1));
        Button more = button("⋮", "Más opciones");
        more.setTextSize(26);
        more.setOnClickListener(this::showMenu);
        header.addView(more, new LayoutParams(dp(48), dp(48)));
        addView(header);

        HorizontalScrollView tools = new HorizontalScrollView(context);
        tools.setHorizontalScrollBarEnabled(false);
        tools.setFillViewport(true);
        tools.setClipToPadding(false);
        LinearLayout shortcuts = row();
        addShortcut(shortcuts, "Buscar", "search");
        addShortcut(shortcuts, "Grabaciones", "recordings");
        addShortcut(shortcuts, "Descargas", "downloads");
        addShortcut(shortcuts, "Radio", "radio");
        addShortcut(shortcuts, "Favoritos", "favorites");
        tools.addView(shortcuts, new HorizontalScrollView.LayoutParams(-1, -2));
        LayoutParams toolParams = new LayoutParams(-1, dp(55));
        toolParams.setMargins(0, dp(8), 0, dp(4));
        addView(tools, toolParams);

        LinearLayout primary = row();
        String[] labels = {"TV EN DIRECTO", "PELÍCULAS", "SERIES"};
        String[] destinations = {"live", "vod", "series"};
        for (int i = 0; i < labels.length; i++) {
            LinearLayout tile = new LinearLayout(context);
            tile.setOrientation(VERTICAL);
            tile.setGravity(Gravity.CENTER);
            tile.setBackground(focusBackground());
            tile.setFocusable(true);
            tile.setClickable(true);
            tile.setContentDescription(labels[i]);
            final String target = destinations[i];
            tile.setOnClickListener(v -> actions.open(target));
            TextView title = text(labels[i], compact ? 16 : 21, Color.WHITE);
            title.setTypeface(Typeface.DEFAULT_BOLD);
            tile.addView(title, new LayoutParams(-1, dp(38)));
            tile.addView(new MediaIcon(context, i), new LayoutParams(-1, 0, 1));
            TextView last = text(updates[i], compact ? 10 : 12, Color.LTGRAY);
            last.setMaxLines(2);
            last.setPadding(dp(4), 0, dp(4), 0);
            tile.addView(last, new LayoutParams(-1, dp(34)));
            LayoutParams lp = new LayoutParams(0, dp(compact ? 152 : 204), 1);
            lp.setMargins(dp(4), dp(3), dp(4), dp(3));
            primary.addView(tile, lp);
        }
        addView(primary);

        LinearLayout secondary = row();
        addWideAction(secondary, "GUÍA EPG", "epg", compact ? 54 : 66);
        addWideAction(secondary, "GRABACIONES", "recordings", compact ? 54 : 66);
        addWideAction(secondary, "MULTIPANTALLA", "multiscreen", compact ? 54 : 66);
        addWideAction(secondary, "CATCH UP", "catchup", compact ? 54 : 66);
        addView(secondary);

        LinearLayout footerActions = row();
        addWideAction(footerActions, "AJUSTES", "settings", 48);
        addWideAction(footerActions, "CUENTAS", "accounts", 48);
        addWideAction(footerActions, "MI CUENTA", "account", 48);
        addView(footerActions);
        String detail = user == null || user.isEmpty() ? "" : "Usuario: " + user;
        if (expiry != null && !expiry.isEmpty()) detail += "    ·    Expiración: " + expiry;
        TextView account = text(detail, 12, Color.LTGRAY);
        account.setMaxLines(2);
        account.setPadding(0, dp(8), 0, 0);
        addView(account, new LayoutParams(-1, -2));
    }

    private void addShortcut(LinearLayout row, String label, String destination) {
        Button b = button(label, label);
        b.setOnClickListener(v -> actions.open(destination));
        LayoutParams lp = new LayoutParams(dp(compact ? 106 : 130), dp(46));
        lp.setMargins(dp(3), 0, dp(3), 0);
        row.addView(b, lp);
    }

    private void addWideAction(LinearLayout row, String label, String destination, int height) {
        Button b = button(label, label);
        b.setTextSize(compact ? 11 : 14);
        b.setOnClickListener(v -> actions.open(destination));
        LayoutParams lp = new LayoutParams(0, dp(height), 1);
        lp.setMargins(dp(4), dp(5), dp(4), 0);
        row.addView(b, lp);
    }

    private void showMenu(View anchor) {
        PopupMenu menu = new PopupMenu(getContext(), anchor);
        String[] names = {"Media local", "M3U / archivo", "Anuncios", "VPN externa",
                          "Respaldo y restauración", "Área de clientes", "Estado del sistema"};
        String[] targets = {"local", "m3u", "announcements", "vpn", "backup", "client", "status"};
        for (int i = 0; i < names.length; i++) menu.getMenu().add(0, i, i, names[i]);
        menu.setOnMenuItemClickListener(item -> {
            actions.open(targets[item.getItemId()]);
            return true;
        });
        menu.show();
    }

    private LinearLayout row() {
        LinearLayout row = new LinearLayout(getContext());
        row.setOrientation(HORIZONTAL);
        row.setGravity(Gravity.CENTER_VERTICAL);
        row.setLayoutParams(new LayoutParams(-1, -2));
        return row;
    }

    private Button button(String label, String description) {
        Button b = new Button(getContext());
        b.setText(label);
        b.setTextColor(Color.WHITE);
        b.setTextSize(14);
        b.setAllCaps(false);
        b.setMinWidth(0);
        b.setMinimumWidth(0);
        b.setPadding(dp(6), 0, dp(6), 0);
        b.setMaxLines(2);
        b.setBackground(focusBackground());
        b.setFocusable(true);
        b.setContentDescription(description);
        return b;
    }

    private TextView text(String value, int size, int color) {
        TextView text = new TextView(getContext());
        text.setText(value);
        text.setTextSize(size);
        text.setTextColor(color);
        text.setGravity(Gravity.CENTER);
        return text;
    }

    private StateListDrawable focusBackground() {
        StateListDrawable state = new StateListDrawable();
        state.addState(new int[]{android.R.attr.state_focused}, shape(0xff16375b, blue, 3));
        state.addState(new int[]{android.R.attr.state_pressed}, shape(0xff23578a, blue, 3));
        state.addState(new int[]{}, shape(0xff171d2a, 0xff303a4a, 1));
        return state;
    }

    private GradientDrawable shape(int fill, int stroke, int width) {
        GradientDrawable shape = new GradientDrawable();
        shape.setColor(fill);
        shape.setCornerRadius(dp(9));
        shape.setStroke(dp(width), stroke);
        return shape;
    }

    private int dp(int value) { return Math.round(value * getResources().getDisplayMetrics().density); }

    /** Simple original vector shapes; no extracted third-party art. */
    private final class MediaIcon extends View {
        private final int type;
        private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
        MediaIcon(Context context, int type) { super(context); this.type = type; }
        @Override protected void onDraw(Canvas canvas) {
            super.onDraw(canvas);
            canvas.save();
            float size = Math.min(getWidth(), getHeight()) * .72f;
            canvas.translate((getWidth() - size) / 2f, (getHeight() - size) / 2f);
            canvas.scale(size / 100f, size / 100f);
            paint.setColor(blue); paint.setStyle(Paint.Style.STROKE); paint.setStrokeWidth(4);
            if (type == 0) {
                canvas.drawRoundRect(8, 20, 92, 76, 8, 8, paint);
                canvas.drawLine(35, 90, 65, 90, paint); canvas.drawLine(50, 77, 50, 90, paint);
                canvas.drawLine(35, 6, 50, 20, paint); canvas.drawLine(65, 6, 50, 20, paint);
            } else if (type == 1) {
                canvas.drawRoundRect(8, 22, 92, 88, 6, 6, paint);
                canvas.drawLine(8, 42, 92, 42, paint);
                for (int x = 16; x < 85; x += 22) canvas.drawLine(x, 22, x + 12, 42, paint);
                triangle(canvas, 42, 52, 65, 65, 42, 78);
            } else {
                canvas.drawRoundRect(15, 8, 89, 66, 7, 7, paint);
                canvas.drawRoundRect(7, 27, 81, 87, 7, 7, paint);
                triangle(canvas, 34, 42, 61, 57, 34, 73);
            }
            canvas.restore();
        }
        private void triangle(Canvas canvas, float x1, float y1, float x2, float y2, float x3, float y3) {
            Path path = new Path(); path.moveTo(x1, y1); path.lineTo(x2, y2); path.lineTo(x3, y3); path.close();
            paint.setStyle(Paint.Style.FILL); canvas.drawPath(path, paint); paint.setStyle(Paint.Style.STROKE);
        }
    }
}
