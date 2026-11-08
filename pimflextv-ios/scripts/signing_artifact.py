#!/usr/bin/env python3
"""Keep signed IPA artifacts private in a public repository's Actions storage."""
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys

CIPHER = 'PIMFLEXTV-signed.zip.enc'
AUTH = 'PIMFLEXTV-signed.auth.json'
ITERATIONS = 200000
DOMAIN = b'PIMFLEXTV-artifact-HMAC-v1\x00'


def digest(path, key=None):
    state = hmac.new(key, digestmod='sha256') if key is not None else hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            state.update(chunk)
    return state.hexdigest()


def crypt(source, target, password, decrypt=False):
    args = ['openssl', 'enc', '-aes-256-cbc', '-pbkdf2', '-iter', str(ITERATIONS),
            '-md', 'sha256', '-in', str(source), '-out', str(target), '-pass', 'stdin']
    if decrypt:
        args.append('-d')
    result = subprocess.run(args, input=password + b'\n', capture_output=True)
    if result.returncode:
        Path(target).unlink(missing_ok=True)
        raise ValueError('Artifact encryption/decryption failed.')


def encrypt(source, target_dir, password):
    target_dir = Path(target_dir)
    target_dir.mkdir(mode=0o700, parents=True, exist_ok=False)
    cipher = target_dir / CIPHER
    crypt(source, cipher, password)
    salt = secrets.token_bytes(16)
    key = hashlib.pbkdf2_hmac('sha256', password, DOMAIN + salt, ITERATIONS, 32)
    metadata = {'format': 'pimflex-signed-artifact-v1', 'cipher': CIPHER,
                'authentication_salt': salt.hex(), 'iterations': ITERATIONS,
                'cipher_sha256': digest(cipher), 'hmac_sha256': digest(cipher, key)}
    (target_dir / AUTH).write_text(json.dumps(metadata, indent=2) + '\n')


def decrypt(source_dir, target, password):
    source_dir, target = Path(source_dir), Path(target)
    if target.exists():
        raise ValueError('Refusing to replace an existing decrypted artifact.')
    metadata = json.loads((source_dir / AUTH).read_text())
    if (metadata.get('format') != 'pimflex-signed-artifact-v1' or
            metadata.get('cipher') != CIPHER or metadata.get('iterations') != ITERATIONS):
        raise ValueError('Unsupported artifact format.')
    salt = bytes.fromhex(metadata['authentication_salt'])
    if len(salt) != 16:
        raise ValueError('Invalid artifact authentication salt.')
    key = hashlib.pbkdf2_hmac('sha256', password, DOMAIN + salt, ITERATIONS, 32)
    cipher = source_dir / CIPHER
    if not hmac.compare_digest(digest(cipher, key), metadata.get('hmac_sha256', '')):
        raise ValueError('Artifact integrity check failed; no decryption was performed.')
    if not hmac.compare_digest(digest(cipher), metadata.get('cipher_sha256', '')):
        raise ValueError('Artifact digest mismatch.')
    crypt(cipher, target, password, decrypt=True)


def main():
    if len(sys.argv) != 5 or sys.argv[1] not in ['encrypt', 'decrypt']:
        raise SystemExit('Usage: signing_artifact.py encrypt|decrypt SOURCE TARGET PASSWORD_FILE')
    os.umask(0o077)
    password = Path(sys.argv[4]).read_bytes().rstrip(b'\r\n')
    if len(password) < 32 or b'\n' in password or b'\r' in password:
        raise ValueError('Use the existing private signing recovery password.')
    if sys.argv[1] == 'encrypt':
        encrypt(sys.argv[2], sys.argv[3], password)
    else:
        decrypt(sys.argv[2], sys.argv[3], password)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, OSError) as error:
        raise SystemExit(str(error)) from None
