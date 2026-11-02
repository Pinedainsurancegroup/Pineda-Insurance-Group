#!/usr/bin/env python3
"""Write a staging preparation bundle only. No Firebase CLI, credentials or network."""
import argparse, hashlib, json, pathlib, re, shutil, xml.etree.ElementTree as ET
ROOT = pathlib.Path(__file__).resolve().parents[2]

def validate_project(project):
    known = ET.parse(ROOT/'pag-leads-android/app/src/main/res/values/firebase_config.xml').getroot()
    production = next(n.text for n in known if n.attrib['name']=='pag_firebase_project_id')
    if not isinstance(project,str) or project == production or not re.fullmatch(r'[a-z][a-z0-9-]{4,28}[a-z0-9]',project):
        raise ValueError('Explicit independent Firebase staging project ID required; production is prohibited')
    return project

def generate(project, output):
    validate_project(project)
    output = pathlib.Path(output)
    if output.exists(): raise ValueError('Output exists; refusing to overwrite any files')
    rules = (ROOT/'firebase/firestore.rules').read_bytes()
    bootstrap = (ROOT/'firebase/staging/firestore.bootstrap.rules').read_bytes()
    gateway = (ROOT/'pag-leads-private-api/SparkOwnerGateway.gs').read_text()
    known = "const PAG_FIREBASE_PROJECT = 'pag-leads-8c6ef';"
    if gateway.count(known)!=1: raise ValueError('Gateway project assignment changed; review source before generation')
    gateway = gateway.replace(known, f"const PAG_FIREBASE_PROJECT = '{project}';")
    output.mkdir(parents=True)
    (output/'firestore.bootstrap.rules').write_bytes(bootstrap)
    (output/'firestore.candidate.rules').write_bytes(rules)
    (output/'firestore.indexes.json').write_text(json.dumps({'indexes':[], 'fieldOverrides':[]}, indent=2)+'\n')
    emulators={'auth':{'host':'127.0.0.1','port':9099},'firestore':{'host':'127.0.0.1','port':8085},'ui':{'enabled':False},'singleProjectMode':True}
    for name, rule in [('firebase.json','firestore.bootstrap.rules'),('firebase.candidate.json','firestore.candidate.rules')]:
        (output/name).write_text(json.dumps({'firestore':{'rules':rule,'indexes':'firestore.indexes.json'},'emulators':emulators},indent=2)+'\n')
    # No default alias; no implicit target. Every later CLI action must name project.
    (output/'.firebaserc').write_text(json.dumps({'projects':{'staging':project}},indent=2)+'\n')
    scripts=output/'apps-script';scripts.mkdir()
    (scripts/'OwnerGateway.gs').write_text(gateway)
    shutil.copyfile(ROOT/'pag-leads-private-api/appsscript.readonly.example.json', scripts/'appsscript.json')
    manifest={'project':project, 'credentialsIncluded':False, 'deployExecuted':False,
      'defaultRules':'deny-all','candidateRulesSha256':hashlib.sha256(rules).hexdigest(),
      'gateway':'separate Apps Script and separate test Sheet required',
      'excluded':['Functions','push senders','assignment senders','triggers','production data','production credentials'],
      'indexes':'Empty inventory, not proof that every query is supported; validate actual queries in staging'}
    (output/'preparation.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',required=True)
    parser.add_argument('--output',required=True,type=pathlib.Path)
    args=parser.parse_args()
    try: result=generate(args.project,args.output)
    except (ValueError,OSError,ET.ParseError) as error: parser.exit(2,f'Preparation rejected: {error}\n')
    print(json.dumps(result,indent=2))
