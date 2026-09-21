from pathlib import Path

p = Path('app/build.gradle')
s = p.read_text()
s = s.replace("versionCode 15", "versionCode 16")
s = s.replace("versionName '2.3.1'", "versionName '2.4.0'")
p.write_text(s)
print('Version set to 2.4.0')
