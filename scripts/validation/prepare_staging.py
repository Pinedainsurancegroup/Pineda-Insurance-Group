#!/usr/bin/env python3
"""Generate an isolated staging resource overlay; never deploys or contacts services."""
import argparse, hashlib, json, pathlib, re, xml.etree.ElementTree as ET
from urllib.parse import urlparse

FIELDS = ('pag_firebase_project_id', 'pag_firebase_application_id', 'pag_firebase_api_key',
          'pag_firebase_sender_id', 'pag_firebase_web_client_id', 'pag_owner_gateway_url')
PACKAGE = 'com.pinedaagencygroup.leads.staging'
ROOT = pathlib.Path(__file__).resolve().parents[2]

def production_values():
    values = {}
    for variant in ('main', 'qa'):
        path = ROOT / f'pag-leads-android/app/src/{variant}/res/values/firebase_config.xml'
        values.update({node.attrib['name']: node.text or '' for node in ET.parse(path).getroot()})
    return values

def validate(config, expected_project):
    if config.get('environment') != 'staging' or config.get('android_package') != PACKAGE:
        raise ValueError('Expected explicit staging environment and isolated Android package')
    if set(config) != set(FIELDS) | {'environment', 'android_package'}:
        raise ValueError('Missing or unexpected fields; use staging-config.example.json')
    for key in FIELDS:
        if not isinstance(config[key], str) or not config[key].strip() or config[key] != config[key].strip():
            raise ValueError(f'Missing or invalid {key}')
    prod = production_values()
    for key in FIELDS:
        if config[key] == prod.get(key):
            raise ValueError(f'Production value prohibited: {key}')
    project = config['pag_firebase_project_id']
    if project != expected_project or not re.fullmatch(r'[a-z][a-z0-9-]{4,28}[a-z0-9]', project):
        raise ValueError('Project ID must match --expected-project and Firebase project syntax')
    sender = config['pag_firebase_sender_id']
    if not re.fullmatch(r'[1-9][0-9]{5,19}', sender):
        raise ValueError('Invalid Firebase sender/project number')
    if not re.fullmatch(r'1:' + sender + r':android:[a-fA-F0-9]+', config['pag_firebase_application_id']):
        raise ValueError('Firebase Android app ID must match staging project number')
    if not re.fullmatch(sender + r'-[a-z0-9]+\.apps\.googleusercontent\.com', config['pag_firebase_web_client_id']):
        raise ValueError('Web client ID must match staging project number')
    if not re.fullmatch(r'AIza[0-9A-Za-z_-]{35}', config['pag_firebase_api_key']):
        raise ValueError('Invalid Firebase public API key format')
    url = urlparse(config['pag_owner_gateway_url'])
    if url.scheme != 'https' or url.netloc != 'script.google.com' or url.query or url.fragment or not re.fullmatch(r'/macros/s/[A-Za-z0-9_-]+/exec', url.path):
        raise ValueError('Expected a separate HTTPS Apps Script staging gateway')
    return config

def generate(config, expected_project, output):
    validate(config, expected_project)
    # Reject values from either known production or legacy QA resource sets.
    for variant in ('main', 'qa'):
        for node in ET.parse(ROOT / f'pag-leads-android/app/src/{variant}/res/values/firebase_config.xml').getroot():
            if node.attrib['name'] in FIELDS and config[node.attrib['name']] == (node.text or ''):
                raise ValueError('Known production/legacy QA configuration prohibited')
    output = pathlib.Path(output)
    if output.exists():
        raise ValueError('Output already exists; choose a new directory to preserve existing configuration')
    resource = ET.Element('resources')
    for key in FIELDS:
        ET.SubElement(resource, 'string', name=key).text = config[key]
    ET.SubElement(resource, 'string', name='pag_app_name').text = 'PAG Leads STAGING'
    ET.SubElement(resource, 'bool', name='pag_qa_build').text = 'true'
    xml = ET.tostring(resource, encoding='utf-8', xml_declaration=True)
    path = output / 'res/values/staging.xml'
    path.parent.mkdir(parents=True)
    path.write_bytes(xml)
    (output / 'validated.json').write_text(json.dumps({
        'environment': 'staging', 'package': PACKAGE, 'project': expected_project,
        'resource_sha256': hashlib.sha256(xml).hexdigest()}, indent=2) + '\n')
    return output

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True, type=pathlib.Path)
    parser.add_argument('--expected-project', required=True)
    parser.add_argument('--output', required=True, type=pathlib.Path)
    args = parser.parse_args()
    try:
        generate(json.loads(args.config.read_text()), args.expected_project, args.output)
    except (ValueError, OSError, ET.ParseError) as error:
        parser.exit(2, f'Staging configuration rejected: {error}\n')
    print('Staging overlay prepared. No service calls, deployment or build executed.')
