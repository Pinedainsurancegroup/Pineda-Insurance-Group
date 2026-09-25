from pathlib import Path

p = Path('app/build.gradle')
s = p.read_text()
s = s.replace("versionCode 21", "versionCode 22")
s = s.replace("versionName '2.9.0'", "versionName '3.0.0'")
p.write_text(s)
print('Version set to 3.0.0')
