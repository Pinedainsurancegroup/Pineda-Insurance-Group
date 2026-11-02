#!/usr/bin/env python3
"""Import authorized google-services.json for the existing staging app, without network."""
import argparse, json, pathlib
from prepare_staging import validate, generate, PACKAGE
PROJECT = 'pag-leads-staging'
NUMBER = '301600139735'

def convert(data, gateway=''):
    info = data.get('project_info', {})
    if info.get('project_id') != PROJECT or str(info.get('project_number')) != NUMBER:
        raise ValueError('Wrong Firebase project; expected existing pag-leads-staging / 301600139735')
    clients = [c for c in data.get('client', []) if c.get('client_info', {}).get('android_client_info', {}).get('package_name') == PACKAGE]
    if len(clients) != 1: raise ValueError('Expected exactly one com.pinedaagencygroup.leads.staging Android client')
    client = clients[0]
    keys = {k.get('current_key') for k in client.get('api_key', []) if k.get('current_key')}
    oauth = {c.get('client_id') for c in client.get('oauth_client', []) if c.get('client_type') == 3 and c.get('client_id')}
    if len(keys) != 1: raise ValueError('Missing or ambiguous Firebase client API key')
    if len(oauth) != 1: raise ValueError('Missing or ambiguous Web OAuth client; export config after staging Google setup')
    config = dict(environment='staging', android_package=PACKAGE,
        pag_firebase_project_id=PROJECT, pag_firebase_sender_id=NUMBER,
        pag_firebase_application_id=client.get('client_info', {}).get('mobilesdk_app_id', ''),
        pag_firebase_api_key=next(iter(keys)),pag_firebase_web_client_id=next(iter(oauth)),pag_owner_gateway_url=gateway)
    validate(config, PROJECT)
    return config

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--google-services',required=True,type=pathlib.Path)
    parser.add_argument('--gateway-url-file',type=pathlib.Path,help='Optional real staging gateway URL; omit for auth-only')
    parser.add_argument('--output',required=True,type=pathlib.Path)
    args=parser.parse_args()
    try:
        config=convert(json.loads(args.google_services.read_text()), args.gateway_url_file.read_text().strip() if args.gateway_url_file else '')
        generate(config, PROJECT, args.output)
    except (ValueError, OSError, KeyError, TypeError) as error: parser.exit(2, f'Staging Android import rejected: {error}\n')
    print('Authorized staging client overlay prepared; no deployment or Firebase calls performed.')
