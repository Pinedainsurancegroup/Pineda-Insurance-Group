from pathlib import Path

p = Path('app/build.gradle')
s = p.read_text()
s = s.replace("versionCode 12", "versionCode 13")
s = s.replace("versionName '2.1.1'", "versionName '2.2.0'")
p.write_text(s)
print('Version set to 2.2.0')
