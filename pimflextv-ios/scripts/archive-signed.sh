#!/bin/bash
# Exports an IPA locally. Does not create credentials or upload to Apple.
set -euo pipefail
umask 077

SOURCE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
: "${PIMFLEX_PROFILE_PATH:?Set the absolute path to the App Store Connect mobileprovision file.}"
: "${PIMFLEX_SIGNING_IDENTITY:?Set the installed Apple Distribution identity SHA-1 fingerprint.}"
: "${PIMFLEX_EXPORT_DIR:?Set a new absolute directory for the signed export.}"
[[ "$(uname -s)" == Darwin ]] || { echo 'macOS with Xcode is required.' >&2; exit 1; }
for executable in xcodebuild xcodegen security codesign python3 ditto; do
  command -v "$executable" >/dev/null || { echo "Missing executable: $executable" >&2; exit 1; }
done
[[ "$PIMFLEX_PROFILE_PATH" == /* && -f "$PIMFLEX_PROFILE_PATH" ]] || { echo 'Invalid profile path.' >&2; exit 1; }
[[ "$PIMFLEX_EXPORT_DIR" == /* && ! -e "$PIMFLEX_EXPORT_DIR" ]] || { echo 'Export directory must be new and absolute.' >&2; exit 1; }
[[ "$PIMFLEX_SIGNING_IDENTITY" =~ ^[[:xdigit:]]{40}$ ]] || { echo 'Invalid identity fingerprint.' >&2; exit 1; }
IDENTITY="$(printf '%s' "$PIMFLEX_SIGNING_IDENTITY" | tr '[:lower:]' '[:upper:]')"

WORK_DIR="$(mktemp -d "${TMPDIR:-/tmp}/pimflex-signing.XXXXXX")"
INSTALLED_PROFILE=''
cleanup() {
  if [[ -n "$INSTALLED_PROFILE" ]]; then rm -f "$INSTALLED_PROFILE"; fi
  rm -rf "$WORK_DIR"
}
trap cleanup EXIT

security find-identity -v -p codesigning > "$WORK_DIR/identities.txt"
python3 - "$WORK_DIR/identities.txt" "$IDENTITY" <<'PY'
import re, sys
from pathlib import Path
identities = re.findall(r'\b([0-9A-F]{40})\s+"Apple Distribution:', Path(sys.argv[1]).read_text())
if sys.argv[2] not in identities:
    raise SystemExit('The selected Apple Distribution identity/private key is not usable in the current keychain.')
PY
security cms -D -i "$PIMFLEX_PROFILE_PATH" > "$WORK_DIR/profile.plist"
PROFILE_UUID="$(python3 "$SOURCE_DIR/scripts/signing_profile.py" "$WORK_DIR/profile.plist" "$WORK_DIR/ExportOptions.plist" "$IDENTITY")"
XCODE_MAJOR="$(xcodebuild -version | python3 -c 'import re,sys; print(int(re.search(r"Xcode ([0-9]+)", sys.stdin.read()).group(1)))')"
if [[ "$XCODE_MAJOR" -ge 16 ]]; then
  PROFILE_DIR="$HOME/Library/Developer/Xcode/UserData/Provisioning Profiles"
else
  PROFILE_DIR="$HOME/Library/MobileDevice/Provisioning Profiles"
fi
mkdir -p "$PROFILE_DIR"
PROFILE_TARGET="$PROFILE_DIR/$PROFILE_UUID.mobileprovision"
if [[ -e "$PROFILE_TARGET" ]]; then
  cmp -s "$PIMFLEX_PROFILE_PATH" "$PROFILE_TARGET" || { echo 'A different profile with this UUID is already installed.' >&2; exit 1; }
else
  cp "$PIMFLEX_PROFILE_PATH" "$PROFILE_TARGET"
  INSTALLED_PROFILE="$PROFILE_TARGET"
fi

# Generate the Xcode project in a temporary copy; do not copy signing material.
mkdir "$WORK_DIR/Source"
for item in App Sources Resources Tests UITests Package.swift project.yml; do
  cp -R "$SOURCE_DIR/$item" "$WORK_DIR/Source/"
done
cd "$WORK_DIR/Source"
xcodegen generate
BUILD_OPTIONS=(-project PimflexTV.xcodeproj -scheme PimflexTV -configuration Release
  -destination 'generic/platform=iOS' -archivePath "$WORK_DIR/PimflexTV.xcarchive"
  -derivedDataPath "$WORK_DIR/DerivedData"
  CODE_SIGN_STYLE=Manual DEVELOPMENT_TEAM=U47SH3LZM6 CODE_SIGN_IDENTITY="$IDENTITY"
  PROVISIONING_PROFILE_SPECIFIER="$PROFILE_UUID")
if [[ -n "${PIMFLEX_BUILD_NUMBER:-}" ]]; then
  [[ "$PIMFLEX_BUILD_NUMBER" =~ ^[1-9][0-9]{0,3}$ ]] || { echo 'Use an integer build number from 1 to 9999.' >&2; exit 1; }
  BUILD_OPTIONS+=("CURRENT_PROJECT_VERSION=$PIMFLEX_BUILD_NUMBER")
fi
xcodebuild "${BUILD_OPTIONS[@]}" archive

xcodebuild -exportArchive -archivePath "$WORK_DIR/PimflexTV.xcarchive" \
  -exportOptionsPlist "$WORK_DIR/ExportOptions.plist" -exportPath "$WORK_DIR/Export"
IPA_PATH="$WORK_DIR/Export/PimflexTV.ipa"
[[ -s "$IPA_PATH" ]] || { echo 'Xcode did not export PimflexTV.ipa.' >&2; exit 1; }
ditto -x -k "$IPA_PATH" "$WORK_DIR/Unpacked"
EXPORTED_APP="$WORK_DIR/Unpacked/Payload/PimflexTV.app"
codesign --verify --deep --strict "$EXPORTED_APP"
codesign -d --entitlements :- "$EXPORTED_APP" > "$WORK_DIR/exported-entitlements.plist" 2> "$WORK_DIR/codesign-diagnostics.txt"
security cms -D -i "$EXPORTED_APP/embedded.mobileprovision" > "$WORK_DIR/exported-profile.plist"
python3 "$SOURCE_DIR/scripts/signing_profile.py" "$WORK_DIR/exported-profile.plist" "$WORK_DIR/VerifiedExportOptions.plist" "$IDENTITY" > /dev/null
python3 - "$EXPORTED_APP/Info.plist" "$WORK_DIR/exported-entitlements.plist" "$IPA_PATH" "$WORK_DIR/verification.json" <<'PY'
import hashlib, json, plistlib, re, sys
from pathlib import Path
info = plistlib.loads(Path(sys.argv[1]).read_bytes())
entitlements = plistlib.loads(Path(sys.argv[2]).read_bytes())
sdk = info.get('DTSDKName', '')
sdk_match = re.fullmatch(r'iphoneos([0-9]+)(?:\.[0-9]+)*', sdk)
if sdk_match is None or int(sdk_match.group(1)) < 26:
    raise SystemExit('App Store Connect requires an app built with iOS 26 SDK or later.')
if info.get('CFBundleIdentifier') != 'com.pimflextv.ios' or set(info.get('UIDeviceFamily', [])) != {1, 2}:
    raise SystemExit('Exported app identity/device families do not match the universal PIMFLEX TV app.')
if entitlements.get('application-identifier') != 'U47SH3LZM6.com.pimflextv.ios' or entitlements.get('get-task-allow') is not False:
    raise SystemExit('Exported signing entitlements do not match distribution requirements.')
if entitlements.get('com.apple.developer.team-identifier') != 'U47SH3LZM6':
    raise SystemExit('Exported signing team does not match.')
ipa = Path(sys.argv[3])
digest_state = hashlib.sha256()
with ipa.open('rb') as stream:
    for chunk in iter(lambda: stream.read(1024 * 1024), b''):
        digest_state.update(chunk)
digest = digest_state.hexdigest()
Path(sys.argv[4]).write_text(json.dumps({'bundle_id': info['CFBundleIdentifier'], 'team_id': 'U47SH3LZM6',
    'version': info.get('CFBundleShortVersionString'), 'build': info.get('CFBundleVersion'),
    'device_families': info['UIDeviceFamily'], 'ipa_sha256': digest, 'codesign_verified': True,
    'build_sdk': sdk, 'xcode_version': info.get('DTXcode'),
    'minimum_ios': info.get('MinimumOSVersion'), 'uploaded_to_apple': False}, indent=2) + '\n')
PY
mkdir "$PIMFLEX_EXPORT_DIR"
cp "$IPA_PATH" "$WORK_DIR/verification.json" "$PIMFLEX_EXPORT_DIR/"
echo 'Signed IPA and verification.json exported. No upload or publication was performed.'
