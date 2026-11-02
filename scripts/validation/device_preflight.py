#!/usr/bin/env python3
"""Read-only Android staging preflight. Never installs, grants permissions or launches apps."""
import argparse, json, pathlib, re, subprocess, sys
ADB = '/workspace/toolchains/android-sdk/platform-tools/adb'
AAPT = '/workspace/toolchains/android-sdk/build-tools/35.0.0/aapt'
PACKAGE = 'com.pinedaagencygroup.leads.staging'

def run(args):
    return subprocess.run(args, check=True, text=True, capture_output=True).stdout.strip()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serial', required=True)
    parser.add_argument('--apk', type=pathlib.Path, required=True)
    parser.add_argument('--report', type=pathlib.Path, required=True)
    args = parser.parse_args()
    if args.report.exists(): parser.error('Report exists; choose a new path')
    badging = run([AAPT, 'dump', 'badging', str(args.apk)])
    if f"package: name='{PACKAGE}'" not in badging or '-STAGING' not in badging.splitlines()[0]:
        parser.error('Only the isolated connected staging APK is accepted; offline/production APK rejected')
    if run([ADB, '-s', args.serial, 'get-state']) != 'device': parser.error('Device is not authorized')
    sdk = int(run([ADB, '-s', args.serial, 'shell', 'getprop', 'ro.build.version.sdk']))
    if sdk < 23: parser.error('Android API23+ required')
    probe = subprocess.run([ADB, '-s', args.serial, 'shell', 'pm', 'path', PACKAGE], text=True, capture_output=True)
    if probe.returncode not in (0, 1) or (probe.returncode == 1 and (probe.stdout.strip() or probe.stderr.strip())):
        parser.error('Cannot determine whether staging is already installed')
    installed = probe.stdout.strip()
    # Existing staging app could contain fixtures; never replace it automatically.
    report = {'sdk': sdk, 'apk': args.apk.name, 'package': PACKAGE,
              'staging_package_already_installed': bool(installed),
              'functional_tests': 'NOT_RUN', 'actions': 'Read-only; no install, launch, permission grants or service calls'}
    args.report.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    try: main()
    except (subprocess.CalledProcessError, ValueError, OSError) as e:
        sys.exit(f'Preflight blocked: {type(e).__name__}; verify APK, authorized device and output path')
