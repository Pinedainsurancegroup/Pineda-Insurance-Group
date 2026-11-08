from pathlib import Path

p = Path('app/build.gradle')
s = p.read_text()
s = s.replace("versionCode 22", "versionCode 23")
s = s.replace("versionName '3.0.0'", "versionName '3.1.0'")
p.write_text(s)
print('Version set to 3.1.0')
