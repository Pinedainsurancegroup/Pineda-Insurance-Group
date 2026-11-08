from pathlib import Path

p = Path('app/build.gradle')
s = p.read_text()
s = s.replace("versionCode 18", "versionCode 19")
s = s.replace("versionName '2.6.0'", "versionName '2.7.0'")
p.write_text(s)
print('Version set to 2.7.0')
