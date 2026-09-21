from pathlib import Path

p = Path('app/build.gradle')
s = p.read_text()
s = s.replace("versionCode 20", "versionCode 21")
s = s.replace("versionName '2.8.0'", "versionName '2.9.0'")
p.write_text(s)
print('Version set to 2.9.0')
