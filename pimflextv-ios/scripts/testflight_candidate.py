#!/usr/bin/env python3
"""Prepare a source-bound TestFlight candidate; export/upload require --execute.

Uses the existing local signing exporter. It never creates identities, profiles,
API keys, testers or App Store submissions. Preparation and verification are
offline and do not read signing or App Store Connect credentials.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import platform
import plistlib
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath

FORMAT = "pimflex-testflight-plan-v1"
VERSION, BUILD = "5.0.0", "8"
IPA_NAME = "PimflexTV.ipa"
REPORT_NAME = "verification.json"
RECEIPT_NAME = "upload-attempt.json"
DEBUG_PLAYBACK_FIXTURES = {"PlaybackFixture.mkv", "PlaybackFixture.mp4", "TrackSelectionFixture.mp4"}
PROJECT = Path(__file__).resolve().parents[1]


def command(args, *, cwd=None, env=None):
    result = subprocess.run(args, cwd=cwd, env=env, text=True, capture_output=True)
    if result.returncode:
        # A subprocess may print credentials: never echo its output on failure.
        raise ValueError(f"Command failed: {Path(args[0]).name}; no later step was run.")
    return result.stdout.strip()


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def repository(project):
    return Path(command(["git", "rev-parse", "--show-toplevel"], cwd=project)).resolve()


def external_path(path, repo):
    supplied = Path(path).expanduser()
    if supplied.is_symlink():
        raise ValueError("Private output/credential paths must not be symlinks.")
    resolved = supplied.resolve()
    if resolved == repo or repo in resolved.parents:
        raise ValueError("Keep private plans, exports and credentials outside the repository.")
    return resolved


def write_new_json(path, value):
    # O_EXCL also prevents replacing an existing symlink or prior export receipt.
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


def replace_json(path, value):
    temporary = path.with_name(path.name + ".new")
    write_new_json(temporary, value)
    os.replace(temporary, path)


def project_settings(project):
    text = (project / "project.yml").read_text()

    def setting(name):
        matches = re.findall(r"^\s*" + re.escape(name) + r":\s*['\"]?([^'\"\s]+)['\"]?\s*$", text, re.M)
        if len(matches) != 1:
            raise ValueError(f"Expected one explicit {name} setting in project.yml.")
        return matches[0]

    version, build = setting("MARKETING_VERSION"), setting("CURRENT_PROJECT_VERSION")
    if (version, build) != (VERSION, BUILD):
        raise ValueError(f"This preparation targets version {VERSION}, build {BUILD} only.")
    # Read the established identity; do not introduce or replace signing details.
    bundles = re.findall(r"^\s*PRODUCT_BUNDLE_IDENTIFIER:\s*([^\s]+)\s*$", text, re.M)
    apps = [value for value in bundles if not value.endswith(".uitests")]
    if len(apps) != 1:
        raise ValueError("Expected one explicit application bundle identifier.")
    excluded = re.findall(r"EXCLUDED_SOURCE_FILE_NAMES:\s*['\"]([^'\"]+)['\"]", text)
    if not any(DEBUG_PLAYBACK_FIXTURES <= set(value.split()) for value in excluded):
        raise ValueError("All local playback fixtures must be excluded from Release.")
    return {"version": version, "build": build, "bundle_id": apps[0],
            "team_id": setting("DEVELOPMENT_TEAM"), "device_families": [1, 2]}


def source_snapshot(project):
    """Bind committed build inputs, excluding docs, DEBUG fixtures and output."""
    project = project.resolve()
    if command(["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=project):
        raise ValueError("Prepare/export from a clean committed checkout; do not sign uncommitted changes.")
    tracked = set(command(["git", "ls-files", "-z"], cwd=project).split("\0"))
    inputs = []
    archived_roots = {"App", "Sources", "Resources", "Vendor"}
    roots = archived_roots | {"scripts", "fastlane"}
    singles = ["Package.swift", "project.yml", "Podfile", "Podfile.lock", "Gemfile", "Gemfile.lock"]
    # The exporter copies these complete directories. Reject even gitignored
    # private files: a clean git status alone cannot establish safe archive inputs.
    for name in archived_roots:
        folder = project / name
        if folder.is_symlink():
            raise ValueError("Symlinks are not supported in candidate inputs.")
        if folder.exists():
            for path in folder.rglob("*"):
                if path.is_symlink():
                    raise ValueError("Symlinks are not supported in candidate inputs.")
                if path.is_file() and path.relative_to(project).as_posix() not in tracked:
                    raise ValueError("Untracked file in archived source inputs, including ignored files; remove it before preparing/exporting.")
    paths = []
    for name in tracked:
        relative = PurePosixPath(name)
        if name and (relative.parts[0] in roots or name in singles):
            paths.append(project / name)
    # Bundler resolves this locally on the Mac before preparation. It may be
    # deliberately ignored, but its exact bytes must still bind the plan.
    if (project / "Gemfile.lock").is_file():
        paths.append(project / "Gemfile.lock")
    for path in sorted(set(paths)):
        relative = path.relative_to(project)
        if relative.parts[:2] == ("scripts", "tests"):
            continue
        if relative.parts[0] not in archived_roots and path.suffix.lower() in {".md", ".pyc"}:
            continue
        if relative.parent.as_posix() == "Resources/PlaybackTests" and relative.name in DEBUG_PLAYBACK_FIXTURES:
            continue
        if path.is_symlink():
            raise ValueError("Symlinks are not supported in candidate inputs.")
        if path.is_file():
            inputs.append({"path": relative.as_posix(), "sha256": sha256(path)})
    payload = json.dumps(inputs, sort_keys=True, separators=(",", ":")).encode()
    commit = command(["git", "rev-parse", "HEAD"], cwd=project)
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("A full Git commit SHA is required.")
    return {"source_commit": commit, "release_inputs_sha256": hashlib.sha256(payload).hexdigest(),
            "release_inputs": inputs}


def prepare(project, plan_path):
    repo = repository(project)
    plan_path = external_path(plan_path, repo)
    plan = {"format": FORMAT, "configuration": "Release", "workspace": "PimflexTV.xcworkspace",
            "scheme": "PimflexTV", "destination": "generic/platform=iOS", "sdk": "iphoneos",
            "minimum_xcode_major": 26, "minimum_sdk_major": 26,
            **project_settings(project), **source_snapshot(project)}
    write_new_json(plan_path, plan)
    return plan_path


def read_plan(project, plan_path):
    plan_path = external_path(plan_path, repository(project))
    plan = json.loads(plan_path.read_text())
    if plan.get("format") != FORMAT:
        raise ValueError("Unsupported candidate plan.")
    expected = {"configuration": "Release", "workspace": "PimflexTV.xcworkspace",
                "scheme": "PimflexTV", "destination": "generic/platform=iOS", "sdk": "iphoneos",
                "minimum_xcode_major": 26, "minimum_sdk_major": 26,
                **project_settings(project), **source_snapshot(project)}
    if any(plan.get(key) != value for key, value in expected.items()):
        raise ValueError("Candidate source, identity or build differs from the prepared plan; prepare a new plan.")
    return plan, plan_path


def validate_ipa(ipa, report, plan):
    """Inspect the actual IPA metadata; this does not substitute for codesign."""
    digest = sha256(ipa)
    if report.get("ipa_sha256") != digest or report.get("codesign_verified") is not True:
        raise ValueError("IPA hash or exporter's signature-verification report does not match.")
    with zipfile.ZipFile(ipa) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Duplicate entries in IPA.")
        for entry in archive.infolist():
            path = PurePosixPath(entry.filename)
            if path.is_absolute() or ".." in path.parts or "\\" in entry.filename:
                raise ValueError("Unsafe IPA path.")
            if path.name in DEBUG_PLAYBACK_FIXTURES:
                raise ValueError("Release IPA contains a DEBUG playback fixture.")
        app_infos = [name for name in names if re.fullmatch(r"Payload/[^/]+\.app/Info\.plist", name)]
        if len(app_infos) != 1:
            raise ValueError("Expected one iOS application in IPA.")
        info = plistlib.loads(archive.read(app_infos[0]))
        app_dir = app_infos[0].rsplit("/", 1)[0]
        for required in [app_dir + "/embedded.mobileprovision", app_dir + "/_CodeSignature/CodeResources"]:
            if required not in names:
                raise ValueError("IPA lacks distribution profile/signature resources.")
        executable = info.get("CFBundleExecutable")
        if not isinstance(executable, str) or PurePosixPath(executable).name != executable or app_dir + "/" + executable not in names:
            raise ValueError("IPA lacks its application executable.")
    expected = {"CFBundleIdentifier": plan["bundle_id"], "CFBundleShortVersionString": plan["version"],
                "CFBundleVersion": plan["build"], "CFBundlePackageType": "APPL",
                "CFBundleSupportedPlatforms": ["iPhoneOS"]}
    if any(info.get(key) != value for key, value in expected.items()) or set(info.get("UIDeviceFamily", [])) != {1, 2}:
        raise ValueError("IPA platform, version/build or universal app identity does not match the candidate.")
    sdk = info.get("DTSDKName", "")
    match = re.fullmatch(r"iphoneos([0-9]+)(?:\.[0-9]+)*", sdk)
    if match is None or int(match.group(1)) < 26:
        raise ValueError("An iPhoneOS 26 or later SDK export is required; simulator archives are not accepted.")
    for key in ["bundle_id", "team_id", "version", "build", "device_families"]:
        if report.get(key) != plan[key]:
            raise ValueError("Export verification report does not match the prepared candidate.")
    if report.get("build_sdk") != sdk:
        raise ValueError("Export report SDK differs from IPA.")
    return digest


def verify_export(project, plan_path, export_dir):
    plan, plan_path = read_plan(project, plan_path)
    export_dir = external_path(export_dir, repository(project))
    report_path, ipa = export_dir / REPORT_NAME, export_dir / IPA_NAME
    if report_path.is_symlink() or ipa.is_symlink():
        raise ValueError("Export artifacts must not be symlinks.")
    report = json.loads(report_path.read_text())
    validate_ipa(ipa, report, plan)
    binding = {"source_commit": plan["source_commit"], "release_inputs_sha256": plan["release_inputs_sha256"],
               "plan_sha256": sha256(plan_path)}
    if any(report.get(key) != value for key, value in binding.items()):
        raise ValueError("Export is not bound to this plan/source snapshot.")
    return report


def require_mac_export_tools():
    if platform.system() != "Darwin":
        raise ValueError("Signed export requires macOS; prepare/verify can run on Linux.")
    for name in ["xcodebuild", "xcodegen", "security", "codesign", "python3", "ditto", "ruby"]:
        if shutil.which(name) is None:
            raise ValueError(f"Missing export executable: {name}")
    xcode = re.search(r"Xcode ([0-9]+)", command(["xcodebuild", "-version"]))
    sdk = re.fullmatch(r"([0-9]+)(?:\.[0-9]+)*", command(["xcodebuild", "-version", "-sdk", "iphoneos", "SDKVersion"]))
    if xcode is None or sdk is None or int(xcode.group(1)) < 26 or int(sdk.group(1)) < 26:
        raise ValueError("Select Xcode 26 or later with iPhoneOS SDK 26 or later.")
    # Match archive-signed.sh: user-installed CocoaPods need not already be in
    # the interactive shell's PATH. Resolve the same Ruby/Gem directory first.
    gem_directory = command(["ruby", "-r", "rubygems", "-e", "puts Gem.user_dir"])
    if not Path(gem_directory).is_absolute():
        raise ValueError("Ruby did not return an absolute user gem directory.")
    environment = os.environ.copy()
    environment["PATH"] = str(Path(gem_directory) / "bin") + os.pathsep + environment.get("PATH", os.defpath)
    environment["COCOAPODS_DISABLE_STATS"] = "true"
    if shutil.which("pod", path=environment["PATH"]) is None:
        raise ValueError("Install CocoaPods 1.16.2 for the selected Ruby before export.")
    if command(["pod", "_1.16.2_", "--version"], env=environment) != "1.16.2":
        raise ValueError("CocoaPods 1.16.2 is required by the existing exporter.")
    return environment


def export_candidate(project, plan_path, export_dir, execute=False):
    plan, plan_path = read_plan(project, plan_path)
    repo = repository(project)
    export_dir = external_path(export_dir, repo)
    if export_dir.exists():
        raise ValueError("Export directory must be new; refusing to replace an existing export.")
    if not execute:
        return "Prepared export only. Add --execute on the signing Mac to run the existing exporter."
    environment = require_mac_export_tools()
    profile = external_path(os.environ.get("PIMFLEX_PROFILE_PATH", ""), repo)
    identity = os.environ.get("PIMFLEX_SIGNING_IDENTITY", "")
    if not profile.is_file() or not re.fullmatch(r"[0-9A-Fa-f]{40}", identity):
        raise ValueError("Set an existing external profile path and installed Apple Distribution fingerprint.")
    environment.update(PIMFLEX_PROFILE_PATH=str(profile), PIMFLEX_SIGNING_IDENTITY=identity,
                       PIMFLEX_EXPORT_DIR=str(export_dir), PIMFLEX_BUILD_NUMBER=plan["build"])
    command(["bash", str(project / "scripts/archive-signed.sh")], cwd=project, env=environment)
    # The build must not be certified against inputs that changed during export.
    read_plan(project, plan_path)
    report_path = export_dir / REPORT_NAME
    report = json.loads(report_path.read_text())
    validate_ipa(export_dir / IPA_NAME, report, plan)
    report.update(source_commit=plan["source_commit"], release_inputs_sha256=plan["release_inputs_sha256"],
                  plan_sha256=sha256(plan_path))
    replace_json(report_path, report)
    verify_export(project, plan_path, export_dir)
    return "Signed export verified and source-bound. No upload was performed."


def upload_candidate(project, plan_path, export_dir, execute=False):
    report = verify_export(project, plan_path, export_dir)
    repo = repository(project)
    plan_path, export_dir = external_path(plan_path, repo), external_path(export_dir, repo)
    if not execute:
        return "Verified upload preparation only. Add --execute on the upload Mac to send to TestFlight."
    if platform.system() != "Darwin" or shutil.which("bundle") is None:
        raise ValueError("Upload execution requires macOS and the project's bundled Fastlane.")
    key_path = external_path(os.environ.get("PIMFLEX_ASC_KEY_PATH", ""), repo)
    key_id = os.environ.get("PIMFLEX_ASC_KEY_ID", "").strip()
    issuer_id = os.environ.get("PIMFLEX_ASC_ISSUER_ID", "").strip()
    if not key_path.is_file() or key_path.suffix != ".p8" or not key_id or not issuer_id:
        raise ValueError("Set the existing external ASC API key path, key ID and issuer ID for upload only.")
    receipt_path = export_dir / RECEIPT_NAME
    receipt = {"state": "attempt_started", "started_at": dt.datetime.now(dt.timezone.utc).isoformat(),
               "ipa_sha256": report["ipa_sha256"], "source_commit": report["source_commit"],
               "version": report["version"], "build": report["build"]}
    # Refuse implicit retries, even after an uncertain transport result. A prior
    # attempt must be reconciled with Apple before a deliberate subsequent action.
    write_new_json(receipt_path, receipt)
    environment = os.environ.copy()
    environment.update(PIMFLEX_ASC_KEY_PATH=str(key_path), PIMFLEX_ASC_KEY_ID=key_id,
                       PIMFLEX_ASC_ISSUER_ID=issuer_id, BUNDLE_FROZEN="true", FASTLANE_SKIP_UPDATE_CHECK="1",
                       FASTLANE_HIDE_CHANGELOG="1", FASTLANE_OPT_OUT_USAGE="1")
    try:
        command(["bundle", "exec", "fastlane", "ios", "upload_verified", "execute:true",
                 "plan:" + str(plan_path), "export_dir:" + str(export_dir),
                 "ipa:" + str(export_dir / IPA_NAME)], cwd=project, env=environment)
    except (ValueError, OSError):
        receipt["state"] = "outcome_unknown_check_apple_before_retry"
        replace_json(receipt_path, receipt)
        raise
    receipt["state"] = "upload_tool_completed_processing_not_verified"
    replace_json(receipt_path, receipt)
    return "Upload tool completed. Apple processing and TestFlight availability remain to be checked."


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", nargs="?", default="prepare", choices=["prepare", "export", "verify", "upload"])
    parser.add_argument("--plan", required=True, help="New/private JSON plan outside the repository")
    parser.add_argument("--export-dir", help="Private export directory outside the repository")
    parser.add_argument("--execute", action="store_true", help="Actually export or upload; never implied")
    args = parser.parse_args(argv)
    if args.action == "prepare":
        if args.execute:
            parser.error("prepare does not execute signing or upload")
        prepare(PROJECT, args.plan)
        print("Private candidate plan prepared. No signing credentials or Apple service were accessed.")
    elif args.action == "verify":
        if args.execute or not args.export_dir:
            parser.error("verify requires --export-dir and does not accept --execute")
        verify_export(PROJECT, args.plan, args.export_dir)
        print("IPA metadata/hash and export source binding verified; Apple status was not queried.")
    else:
        if not args.export_dir:
            parser.error("--export-dir is required")
        operation = export_candidate if args.action == "export" else upload_candidate
        print(operation(PROJECT, args.plan, args.export_dir, args.execute))


if __name__ == "__main__":
    os.umask(0o077)
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError, zipfile.BadZipFile, plistlib.InvalidFileException) as error:
        # Never dump subprocess output or environment/credential values.
        raise SystemExit(str(error)) from None
