import pathlib,subprocess,hashlib,json,shutil,re,os
out=pathlib.Path('/workspace/test-packages-20261102');sdk=pathlib.Path('/workspace/toolchains/android-sdk/build-tools/35.0.0')
javaenv=os.environ.copy();javaenv['JAVA_HOME']='/workspace/toolchains/jdk-17.0.17+10'
rows=[]
for name,source,identity,ref in [
 ('PAG-Leads-1.9-QA-OFFLINE.apk','/workspace/Pineda-Insurance-Group/pag-leads-android/app/build/outputs/apk/qa/app-qa-unsigned.apk','com.pinedaagencygroup.leads.qa','aa74ef9'),
 ('PIMFLEX-TV-2.1.1-AUDIT-OFFLINE.apk','/workspace/pimflex-dev/pimflextv-rebuild/app/build/outputs/apk/debug/app-debug.apk','com.pimflextv.next.audit','8a0de0f'),
 ('Taty-Nails-4.1-AUDIT-OFFLINE.apk','/workspace/taty-audit/TatyNailsAndroid/app/build/outputs/apk/debug/app-debug.apk','com.tatynails.app.audit','64a333bf8baa0d6f5785ff6e56b33ca9dbe787ae+overlays')]:
 source=pathlib.Path(source)
 metadata=json.loads((source.parent/"output-metadata.json").read_text())
 source=source.parent/metadata["elements"][0]["outputFile"]
 dst=out/name;shutil.copy2(source,dst)
 check=subprocess.run([str(sdk/'apksigner'),'verify',str(dst)],capture_output=True,env=javaenv)
 if check.returncode:
  subprocess.run([str(sdk/'zipalign'),'-f','4',str(dst),str(out/'aligned.apk')],check=True)
  (out/'aligned.apk').replace(dst)
  subprocess.run([str(sdk/'apksigner'),'sign','--ks',str(pathlib.Path.home()/'.android/debug.keystore'),'--ks-pass','pass:android','--key-pass','pass:android',str(dst)],check=True,env=javaenv)
 signature=subprocess.check_output([str(sdk/'apksigner'),'verify','--verbose','--print-certs',str(dst)],text=True,env=javaenv)
 meta=subprocess.check_output([str(sdk/'aapt'),'dump','badging',str(dst)],text=True)
 assert f"package: name='{identity}'" in meta,meta[:300]
 assert '-OFFLINE' in meta.splitlines()[0]
 permissions=subprocess.check_output([str(sdk/'aapt'),'dump','permissions',str(dst)],text=True)
 for permission in ['android.permission.INTERNET','android.permission.READ_CALENDAR','android.permission.WRITE_CALENDAR']:assert permission not in permissions,(name,permission)
 subprocess.run([str(sdk/'zipalign'),'-c','4',str(dst)],check=True,capture_output=True)
 (out/(name+'.signature.txt')).write_text(signature)
 (out/(name+'.manifest.txt')).write_text(meta+'\n'+permissions)
 digest=hashlib.sha256(dst.read_bytes()).hexdigest()
 cert=re.search(r'Signer #1 certificate SHA-256 digest: (.+)',signature).group(1)
 rows.append(dict(file=name,bytes=dst.stat().st_size,sha256=digest,certificate_sha256=cert,package=identity,version=meta.splitlines()[0],source=ref,overlay='scripts/validation/qa.init.gradle + offline-manifest.xml',limitations='Offline, debug/test certificate; not installed or validated on device; not a production build'))
(out/'manifest.json').write_text(json.dumps(rows,indent=2)+'\n')
(out/'SHA256SUMS.txt').write_text(''.join(f"{r['sha256']}  {r['file']}\n" for r in rows))
print(json.dumps(rows,indent=2))
