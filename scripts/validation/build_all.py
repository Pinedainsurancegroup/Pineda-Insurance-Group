import subprocess,os,json,pathlib
out=pathlib.Path('/workspace/validation-20261102')
e=os.environ.copy();e.update(JAVA_HOME='/workspace/toolchains/jdk-17.0.17+10',ANDROID_HOME='/workspace/toolchains/android-sdk',GRADLE_USER_HOME='/workspace/toolchains/gradle-home')
base=['/workspace/toolchains/gradle-8.13/bin/gradle','-I','/workspace/Pineda-Insurance-Group/scripts/validation/qa.init.gradle','-Djavax.net.ssl.trustStore=/etc/ssl/certs/java/cacerts','-Dhttps.proxyHost=proxy','-Dhttps.proxyPort=8080','--no-daemon','--max-workers=2']
results={}
for name,root,tasks in [('pag','/workspace/Pineda-Insurance-Group/pag-leads-android',['assembleQa','assembleDebugAndroidTest','testQaUnitTest','lintQa']),('pimflex','/workspace/pimflex-dev/pimflextv-rebuild',['assembleDebug','testDebugUnitTest','lintDebug']),('taty','/workspace/taty-audit/TatyNailsAndroid',['assembleDebug','testDebugUnitTest','lintDebug'])]:
 with (out/(name+'-build.log')).open('w') as f:r=subprocess.run(base+['-p',root]+tasks,env=e,stdout=f,stderr=subprocess.STDOUT)
 results[name]=r.returncode;(out/'build-results.json').write_text(json.dumps(results,indent=2));print(name,r.returncode,flush=True)
