#!/bin/bash
set -euo pipefail
export COCOAPODS_DISABLE_STATS=true
PIMFLEX_GEM_BIN="$(ruby -r rubygems -e 'puts Gem.user_dir')/bin"
export PATH="$PIMFLEX_GEM_BIN:$PATH"
if ! gem list --installed cocoapods --version 1.16.2 >/dev/null; then
  gem install --user-install cocoapods --version 1.16.2 --no-document
fi
xcodegen generate
pod _1.16.2_ install
