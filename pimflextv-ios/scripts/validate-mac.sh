#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
command -v xcodebuild >/dev/null || { echo 'Se necesita macOS con Xcode.'; exit 1; }
command -v xcodegen >/dev/null || { echo 'Instala XcodeGen: brew install xcodegen'; exit 1; }
swift test
xcodegen generate
xcodebuild -project PimflexTV.xcodeproj -scheme PimflexTV -configuration Debug \
  -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' \
  -derivedDataPath DerivedData CODE_SIGNING_ALLOWED=NO build
xcodebuild -project PimflexTV.xcodeproj -scheme PimflexTV -configuration Release \
  -sdk iphoneos -destination 'generic/platform=iOS' \
  -derivedDataPath DeviceBuild CODE_SIGNING_ALLOWED=NO build
