#!/usr/bin/env python3
"""Validate the decoded Apple profile before using an installed signing identity."""
import datetime as dt
import hashlib
import plistlib
import re
import sys
import uuid
from pathlib import Path

TEAM = "U47SH3LZM6"
BUNDLE = "com.pimflextv.ios"


def validate(profile, identity, now=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    if not re.fullmatch(r"[0-9A-Fa-f]{40}", identity):
        raise ValueError("Supply the SHA-1 fingerprint of an installed signing identity.")
    if profile.get("TeamIdentifier") != [TEAM]:
        raise ValueError("The provisioning profile belongs to another Apple team.")
    entitlements = profile.get("Entitlements", {})
    if entitlements.get("application-identifier") != f"{TEAM}.{BUNDLE}":
        raise ValueError("The provisioning profile does not match the explicit PIMFLEX TV App ID.")
    if entitlements.get("com.apple.developer.team-identifier") != TEAM:
        raise ValueError("The entitlement team does not match PIMFLEX TV.")
    if entitlements.get("get-task-allow") is not False:
        raise ValueError("A distribution profile with debugging disabled is required.")
    if profile.get("ProvisionedDevices") is not None or profile.get("ProvisionsAllDevices", False):
        raise ValueError("An App Store Connect profile is required; device/enterprise profiles are rejected.")
    if entitlements.get("beta-reports-active") is not True:
        raise ValueError("The profile is not enabled for App Store Connect beta distribution.")
    if "iOS" not in profile.get("Platform", []):
        raise ValueError("The profile must support iOS and iPadOS.")
    expires = profile.get("ExpirationDate")
    if not isinstance(expires, dt.datetime):
        raise ValueError("The profile has no valid expiration date.")
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=dt.timezone.utc)
    if expires <= now:
        raise ValueError("The provisioning profile has expired.")
    fingerprints = {hashlib.sha1(cert).hexdigest().upper()
                    for cert in profile.get("DeveloperCertificates", []) if isinstance(cert, bytes)}
    if identity.upper() not in fingerprints:
        raise ValueError("The signing identity is not included in the provisioning profile.")
    profile_uuid = str(uuid.UUID(profile.get("UUID", ""))).upper()
    return profile_uuid


def main():
    if len(sys.argv) != 4:
        raise SystemExit("Usage: signing_profile.py decoded-profile.plist ExportOptions.plist IDENTITY_SHA1")
    with Path(sys.argv[1]).open("rb") as stream:
        profile = plistlib.load(stream)
    identity = sys.argv[3].upper()
    profile_uuid = validate(profile, identity)
    options = {
        "method": "app-store-connect", "destination": "export",
        "teamID": TEAM, "signingStyle": "manual", "signingCertificate": identity,
        "provisioningProfiles": {BUNDLE: profile_uuid},
        "manageAppVersionAndBuildNumber": False, "stripSwiftSymbols": True,
    }
    with Path(sys.argv[2]).open("wb") as stream:
        plistlib.dump(options, stream)
    print(profile_uuid)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, TypeError, KeyError, plistlib.InvalidFileException) as error:
        raise SystemExit(str(error)) from None
