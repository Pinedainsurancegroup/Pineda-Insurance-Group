#!/usr/bin/env python3
"""Select an installed simulator by family; fail instead of silently skipping iPad."""
import json
import sys

family = sys.argv[1]
devices = [device for runtime, entries in json.load(sys.stdin)["devices"].items()
           if "iOS" in runtime for device in entries if device.get("isAvailable", True)]
if family == "iphone":
    matches = [d for d in devices if "iPhone" in d["name"]]
elif family == "ipad-compact":
    matches = [d for d in devices if "iPad mini" in d["name"]]
elif family == "ipad-large":
    matches = [d for d in devices if "iPad Pro 13-inch" in d["name"] or "iPad Pro (12.9-inch)" in d["name"]]
else:
    raise SystemExit(f"Unknown simulator family: {family}")
if not matches:
    raise SystemExit(f"Required simulator unavailable: {family}; installed: {[d['name'] for d in devices]}")
print(matches[0]["udid"])
print(f"Selected {family}: {matches[0]['name']}", file=sys.stderr)
