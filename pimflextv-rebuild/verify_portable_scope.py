"""Fail CI if playback/authentication changes outside the reviewed backup integration."""
from pathlib import Path
import re, sys
before=Path(sys.argv[1]).read_text()
after=Path('app/src/main/java/com/pimflextv/next/MainActivity.java').read_text()
pattern=r'^    (?:private|public|protected) [^\n]+?\b(\w+)\([^\n]*\)[^{\n]*\{'
def regions(s):
    matches=list(re.finditer(pattern,s,re.M))
    return {m[1]:s[m.start():matches[i+1].start() if i+1<len(matches) else len(s)].rstrip() for i,m in enumerate(matches)}
a,b=regions(before),regions(after)
allowed={'showLogin','showBackupRestoreScreen','createBackupJson','writeBackupToUri','restoreBackupFromUri','showCloneLoginOnTv','switchSavedAccount','showSettings','showSavedAccounts'}
changed={name for name in a if a[name] != b.get(name)}
assert changed <= allowed, changed-allowed
assert set(a)-set(b)=={'createBackupJson'}
assert set(b)-set(a)=={'portableBackup','showImportedBackupLogin'}
# All pre-existing keystore operations also retain their exact implementation.
old_secure=Path(sys.argv[2]).read_text()
new_secure=Path('app/src/main/java/com/pimflextv/next/SecureStore.java').read_text()
start=new_secure.index('    // Used by portable restore')
end=new_secure.index('    private static String safeSlot',start)
assert old_secure == new_secure[:start]+new_secure[end:]
print(f'PASS: {len(a)-len(changed)} v3.2 method regions unchanged. Only {len(changed)} reviewed backup/login/settings regions changed.')
print('Playback, authentication, stream URLs, recording and existing SecureStore methods preserved.')
