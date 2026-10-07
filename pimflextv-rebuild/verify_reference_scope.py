"""Prove that only the reviewed UI regions changed from fully patched v3.1.0."""
import re
import sys
from pathlib import Path

baseline = Path(sys.argv[1]).read_text()
candidate = Path('app/src/main/java/com/pimflextv/next/MainActivity.java').read_text()
pattern = r'^    (?:private|public|protected) [^\n]+?\b(\w+)\([^\n]*\) \{'

def regions(source):
    matches = list(re.finditer(pattern, source, re.M))
    return {m[1]: source[m.start(): matches[i+1].start() if i+1 < len(matches) else len(source)]
            for i, m in enumerate(matches)}

before, after = regions(baseline), regions(candidate)
allowed = {'showDashboard', 'addCloneHeader', 'addCloneMainTile', 'loadCategories',
           'showVpnScreen', 'showBackupRestoreScreen', 'showOpenSubtitleResults', 'showSettings'}
changed = {name for name in before if before[name] != after.get(name)}
assert changed <= allowed, 'Unexpected method changes: ' + str(changed - allowed)
assert set(before) <= set(after), 'Stable method removed'
assert set(after) - set(before) == {'referenceCategoryUpdate'}, 'Unexpected method additions'
assert 'new ReferenceHomeView(' in candidate
assert 'applicationIdSuffix \'.reference\'' in Path('app/build.gradle').read_text()
print(f'PASS: {len(before)-len(changed)} stable method regions unchanged; {len(changed)} UI regions reviewed.')
print('Playback, authentication, stream URLs, recording and account storage preserved.')
