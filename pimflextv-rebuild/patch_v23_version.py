from pathlib import Path

p = Path('app/build.gradle')
s = p.read_text()
s = s.replace("versionCode 13", "versionCode 14")
s = s.replace("versionName '2.2.0'", "versionName '2.3.0'")
p.write_text(s)
print('Version set to 2.3.0')
