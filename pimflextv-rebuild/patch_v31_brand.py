from pathlib import Path
import base64

root = Path("app/src/main")
drawable = root / "res" / "drawable"
drawable.mkdir(parents=True, exist_ok=True)

logo_b64 = "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"
(drawable / "pimflex_brand_exact.webp").write_bytes(base64.b64decode(logo_b64))

java = root / "java" / "com" / "pimflextv" / "next" / "MainActivity.java"
s = java.read_text()

# Use the user-approved PIMFLEX TV logo everywhere the brand mark is shown.
s = s.replace("R.drawable.pimflex_pt", "R.drawable.pimflex_brand_exact")

# Final splash: exact approved logo on white, without duplicated wordmark text.
old = """        splash.setBackgroundColor(bg);
        splash.setPadding(dp(28), dp(28), dp(28), dp(28));

        ImageView logo = new ImageView(this);
        logo.setImageResource(R.drawable.pimflex_brand_exact);
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
"""
new = """        splash.setBackgroundColor(Color.WHITE);
        splash.setPadding(dp(28), dp(28), dp(28), dp(28));

        ImageView logo = new ImageView(this);
        logo.setImageResource(R.drawable.pimflex_brand_exact);
        logo.setScaleType(ImageView.ScaleType.CENTER_INSIDE);
        splash.addView(logo, new LinearLayout.LayoutParams(dp(520), dp(260)));
"""
if old in s:
    s = s.replace(old, new, 1)

# Login screen: use the exact approved logo instead of duplicating the brand as plain text.
old_login_head = """    private void showLogin() {
        systemBack = null;
        root = baseScreen();
        addTitle("PIMFLEX TV", 34);
        addSubtitle("Live TV · Movies · Series · EPG");
"""
new_login_head = """    private void showLogin() {
        systemBack = null;
        root = cloneScreen();

        ImageView loginLogo = new ImageView(this);
        loginLogo.setImageResource(R.drawable.pimflex_brand_exact);
        loginLogo.setScaleType(ImageView.ScaleType.CENTER_INSIDE);
        loginLogo.setBackgroundColor(Color.WHITE);
        loginLogo.setPadding(dp(6), dp(5), dp(6), dp(5));
        LinearLayout.LayoutParams loginLogoParams = new LinearLayout.LayoutParams(dp(360), dp(150));
        loginLogoParams.gravity = Gravity.CENTER_HORIZONTAL;
        root.addView(loginLogo, loginLogoParams);
"""
if old_login_head in s:
    s = s.replace(old_login_head, new_login_head, 1)

# Header badge: keep the approved white-background logo readable on the dark UI.
old_header = """        ImageView logo = new ImageView(this);
        logo.setImageResource(R.drawable.pimflex_brand_exact);
        logo.setScaleType(ImageView.ScaleType.CENTER_INSIDE);
        header.addView(logo, new LinearLayout.LayoutParams(dp(200), dp(78)));
"""
new_header = """        ImageView logo = new ImageView(this);
        logo.setImageResource(R.drawable.pimflex_brand_exact);
        logo.setScaleType(ImageView.ScaleType.CENTER_INSIDE);
        logo.setBackgroundColor(Color.WHITE);
        logo.setPadding(dp(4), dp(3), dp(4), dp(3));
        header.addView(logo, new LinearLayout.LayoutParams(dp(220), dp(78)));
"""
if old_header in s:
    s = s.replace(old_header, new_header, 1)

java.write_text(s)

manifest = root / "AndroidManifest.xml"
m = manifest.read_text()
m = m.replace('android:banner="@drawable/tv_banner"', 'android:banner="@drawable/pimflex_brand_exact"')
m = m.replace('android:icon="@drawable/ic_launcher_pimflex"', 'android:icon="@drawable/pimflex_brand_exact"')
m = m.replace('android:roundIcon="@drawable/ic_launcher_pimflex"', 'android:roundIcon="@drawable/pimflex_brand_exact"')
manifest.write_text(m)

print("v3.1 official PIMFLEX branding applied")
