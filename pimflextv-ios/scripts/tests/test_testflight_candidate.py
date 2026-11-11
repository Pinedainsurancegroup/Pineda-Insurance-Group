"""Offline orchestration/metadata tests; fixtures are not signed or installable."""
import importlib.util
import json
import os
from pathlib import Path
import plistlib
import subprocess
import tempfile
import unittest
from unittest import mock
import zipfile

spec = importlib.util.spec_from_file_location("testflight_candidate", Path(__file__).resolve().parents[1] / "testflight_candidate.py")
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)


class TestFlightCandidateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.project = self.repo / "pimflextv-ios"
        self.project.mkdir(parents=True)
        self.plan_path = self.root / "candidate.json"
        self.export_dir = self.root / "export with spaces"
        (self.project / "project.yml").write_text("""settings:
  MARKETING_VERSION: '5.0.0'
  CURRENT_PROJECT_VERSION: '8'
  DEVELOPMENT_TEAM: FIXTURETEAM
  PRODUCT_BUNDLE_IDENTIFIER: com.example.fixture
  EXCLUDED_SOURCE_FILE_NAMES: 'PlaybackFixture.mkv PlaybackFixture.mp4 TrackSelectionFixture.mp4'
""")
        for name, content in {
            "App/App.swift": "// Fixture source\n", "Sources/Core.swift": "// Fixture core\n",
            "scripts/archive-signed.sh": "#!/bin/bash\nexit 99\n",
            "scripts/signing_profile.py": "# Fixture profile validator\n",
            "Resources/PlaybackTests/PlaybackFixture.mkv": "DEBUG fixture",
            "Resources/PlaybackTests/PlaybackFixture.mp4": "DEBUG fixture",
            "Resources/PlaybackTests/TrackSelectionFixture.mp4": "DEBUG track fixture",
            "README.md": "Fixture documentation\n", ".gitignore": "DerivedData/\n*.p8\nGemfile.lock\nfastlane/report.xml\n",
            "Gemfile": "# Fixture dependency manifest\n", "fastlane/Fastfile": "# Fixture lane\n",
        }.items():
            path = self.project / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        self.git("init", "-q")
        self.git("config", "user.name", "Fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        self.commit()
        candidate.prepare(self.project, self.plan_path)
        self.plan = json.loads(self.plan_path.read_text())

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.repo, text=True, capture_output=True, check=True).stdout.strip()

    def commit(self):
        self.git("add", ".")
        self.git("commit", "-qm", "Fixture snapshot")

    def make_export(self, info_changes=None, report_changes=None, extra=None):
        self.export_dir.mkdir(exist_ok=True)
        info = {"CFBundleIdentifier": self.plan["bundle_id"], "CFBundleShortVersionString": "5.0.0",
                "CFBundleVersion": "8", "CFBundlePackageType": "APPL", "CFBundleExecutable": "PimflexTV",
                "CFBundleSupportedPlatforms": ["iPhoneOS"], "UIDeviceFamily": [1, 2], "DTSDKName": "iphoneos26.2"}
        info.update(info_changes or {})
        ipa = self.export_dir / candidate.IPA_NAME
        with zipfile.ZipFile(ipa, "w") as archive:
            for name, data in {
                "Payload/PimflexTV.app/Info.plist": plistlib.dumps(info),
                "Payload/PimflexTV.app/PimflexTV": b"NOT A REAL EXECUTABLE",
                "Payload/PimflexTV.app/embedded.mobileprovision": b"NOT A REAL PROFILE",
                "Payload/PimflexTV.app/_CodeSignature/CodeResources": b"NOT A REAL SIGNATURE",
                **(extra or {}),
            }.items():
                archive.writestr(name, data)
        report = {key: self.plan[key] for key in ["bundle_id", "team_id", "version", "build", "device_families"]}
        report.update(ipa_sha256=candidate.sha256(ipa), codesign_verified=True, build_sdk=info["DTSDKName"],
                      uploaded_to_apple=False)
        report.update(report_changes or {})
        (self.export_dir / candidate.REPORT_NAME).write_text(json.dumps(report))
        return report

    def bind_export(self):
        report = self.make_export()
        report.update(source_commit=self.plan["source_commit"], release_inputs_sha256=self.plan["release_inputs_sha256"],
                      plan_sha256=candidate.sha256(self.plan_path))
        (self.export_dir / candidate.REPORT_NAME).write_text(json.dumps(report))
        return report

    def test_default_prepare_is_offline_private_and_cannot_replace_a_plan(self):
        new_plan = self.root / "another plan.json"
        with mock.patch.object(candidate, "PROJECT", self.project), mock.patch.object(candidate, "command", wraps=candidate.command) as commands:
            candidate.main(["--plan", str(new_plan)])
        self.assertTrue(all(call.args[0][0] == "git" for call in commands.call_args_list))
        self.assertEqual(new_plan.stat().st_mode & 0o777, 0o600)
        self.assertEqual(json.loads(new_plan.read_text())["build"], "8")
        with self.assertRaises(FileExistsError):
            candidate.prepare(self.project, new_plan)
        with self.assertRaisesRegex(ValueError, "outside the repository"):
            candidate.prepare(self.project, self.project / "private-plan.json")

    def test_dirty_source_and_different_commits_are_rejected(self):
        (self.project / "App/App.swift").write_text("// Changed source\n")
        with self.assertRaisesRegex(ValueError, "clean committed"):
            candidate.read_plan(self.project, self.plan_path)
        self.commit()
        with self.assertRaisesRegex(ValueError, "differs"):
            candidate.read_plan(self.project, self.plan_path)

    def test_digest_tracks_release_scripts_and_lanes_but_excludes_docs_debug_and_build_output(self):
        original = candidate.source_snapshot(self.project)
        (self.project / "README.md").write_text("Updated documentation")
        (self.project / "Resources/PlaybackTests/PlaybackFixture.mp4").write_text("Updated DEBUG media")
        (self.project / "Resources/PlaybackTests/TrackSelectionFixture.mp4").write_text("Updated DEBUG tracks")
        generated = self.project / "DerivedData/anything"
        generated.parent.mkdir()
        generated.write_text("Build output")
        self.commit()
        changed = candidate.source_snapshot(self.project)
        self.assertEqual(original["release_inputs_sha256"], changed["release_inputs_sha256"])
        (self.project / "fastlane/Fastfile").write_text("# Changed upload lane\n")
        self.commit()
        self.assertNotEqual(changed["release_inputs_sha256"], candidate.source_snapshot(self.project)["release_inputs_sha256"])
        paths = {entry["path"] for entry in changed["release_inputs"]}
        self.assertIn("scripts/archive-signed.sh", paths)

    def test_ignored_private_file_in_copied_resources_is_rejected(self):
        (self.project / "Resources/secret.p8").write_text("PRIVATE TEST FIXTURE")
        self.assertEqual(self.git("status", "--porcelain"), "")
        with self.assertRaisesRegex(ValueError, "Untracked file in archived"):
            candidate.source_snapshot(self.project)

    def test_ignored_bundle_lock_binds_plan_but_fastlane_report_does_not(self):
        before = candidate.source_snapshot(self.project)
        (self.project / "fastlane/report.xml").write_text("<testsuites/>")
        self.assertEqual(candidate.source_snapshot(self.project), before)
        (self.project / "Gemfile.lock").write_text("GEM\n  specs:\n    fixture (1.0)\n")
        after = candidate.source_snapshot(self.project)
        self.assertNotEqual(after["release_inputs_sha256"], before["release_inputs_sha256"])
        self.assertIn("Gemfile.lock", {entry["path"] for entry in after["release_inputs"]})
        with self.assertRaisesRegex(ValueError, "differs"):
            candidate.read_plan(self.project, self.plan_path)

    def test_export_prepare_needs_no_credentials_and_linux_execution_is_rejected(self):
        with mock.patch.object(candidate, "require_mac_export_tools", side_effect=AssertionError("must not inspect tools")):
            message = candidate.export_candidate(self.project, self.plan_path, self.export_dir)
            self.assertIn("Prepared export only", message)
        self.assertFalse(self.export_dir.exists())
        with mock.patch.object(candidate.platform, "system", return_value="Linux"):
            with self.assertRaisesRegex(ValueError, "macOS"):
                candidate.export_candidate(self.project, self.plan_path, self.export_dir, execute=True)
        self.assertFalse(self.export_dir.exists())

    def test_simulator_wrong_version_build_family_and_debug_fixtures_are_rejected(self):
        changes = [{"CFBundleSupportedPlatforms": ["iPhoneSimulator"], "DTSDKName": "iphonesimulator26.2"},
                   {"CFBundleVersion": "7"}, {"CFBundleShortVersionString": "0.4.0"},
                   {"CFBundleIdentifier": "com.other.app"}, {"UIDeviceFamily": [1]}, {"DTSDKName": "iphoneos18.5"}]
        for change in changes:
            with self.subTest(change=change):
                report = self.make_export(info_changes=change)
                with self.assertRaises(ValueError):
                    candidate.validate_ipa(self.export_dir / candidate.IPA_NAME, report, self.plan)
        for name in ["PlaybackFixture.mkv", "PlaybackFixture.mp4", "TrackSelectionFixture.mp4"]:
            with self.subTest(debug_fixture=name):
                report = self.make_export(extra={f"Payload/PimflexTV.app/{name}": b"DEBUG"})
                with self.assertRaisesRegex(ValueError, "DEBUG"):
                    candidate.validate_ipa(self.export_dir / candidate.IPA_NAME, report, self.plan)

    def test_release_cannot_omit_track_fixture_exclusion(self):
        project = self.project / "project.yml"
        project.write_text(project.read_text().replace(" TrackSelectionFixture.mp4", ""))
        with self.assertRaisesRegex(ValueError, "All local playback fixtures"):
            candidate.project_settings(self.project)

    def test_tampered_ipa_unbound_report_and_wrong_plan_hash_are_rejected(self):
        self.make_export()
        with self.assertRaisesRegex(ValueError, "not bound"):
            candidate.verify_export(self.project, self.plan_path, self.export_dir)
        self.bind_export()
        with (self.export_dir / candidate.IPA_NAME).open("ab") as stream:
            stream.write(b"tampering")
        with self.assertRaisesRegex(ValueError, "hash"):
            candidate.verify_export(self.project, self.plan_path, self.export_dir)
        self.bind_export()
        self.plan_path.write_text(self.plan_path.read_text() + "\n")
        with self.assertRaisesRegex(ValueError, "not bound"):
            candidate.verify_export(self.project, self.plan_path, self.export_dir)

    def test_export_reuses_existing_exporter_and_binds_verified_output(self):
        real_command = candidate.command
        calls = []
        profile = self.root / "fixture profile.mobileprovision"
        profile.write_bytes(b"fixture only")

        def simulated(args, **kwargs):
            calls.append((args, kwargs))
            if args[0] == "git":
                return real_command(args, **kwargs)
            if args[0] == "xcodebuild":
                return "26.2" if "SDKVersion" in args else "Xcode 26.3\nBuild version fixture"
            if args[0] == "ruby":
                return str(self.root / "ruby user gems")
            if args[0] == "pod":
                return "1.16.2"
            if args[0] == "bash":
                self.make_export()
                return "Fixture exporter completed"
            self.fail("Unexpected external command")

        with mock.patch.object(candidate, "command", side_effect=simulated), mock.patch.object(candidate.platform, "system", return_value="Darwin"), mock.patch.object(candidate.shutil, "which", return_value="/fixture/tool"), mock.patch.dict(os.environ, {"PIMFLEX_PROFILE_PATH": str(profile), "PIMFLEX_SIGNING_IDENTITY": "A" * 40}):
            candidate.export_candidate(self.project, self.plan_path, self.export_dir, execute=True)
        archive_calls = [call for call in calls if call[0][0] == "bash"]
        self.assertEqual(len(archive_calls), 1)
        self.assertEqual(archive_calls[0][0][1], str(self.project / "scripts/archive-signed.sh"))
        self.assertEqual(archive_calls[0][1]["env"]["PIMFLEX_BUILD_NUMBER"], "8")
        # macOS temporary paths may enter through /var and resolve to /private/var.
        self.assertEqual(archive_calls[0][1]["env"]["PIMFLEX_EXPORT_DIR"], str(self.export_dir.resolve()))
        self.assertTrue(archive_calls[0][1]["env"]["PATH"].startswith(str(self.root / "ruby user gems/bin") + os.pathsep))
        pod_calls = [call for call in calls if call[0][0] == "pod"]
        self.assertEqual(pod_calls[0][0], ["pod", "_1.16.2_", "--version"])
        self.assertEqual(pod_calls[0][1]["env"]["PATH"], archive_calls[0][1]["env"]["PATH"])
        report = candidate.verify_export(self.project, self.plan_path, self.export_dir)
        self.assertEqual(report["source_commit"], self.git("rev-parse", "HEAD"))
        self.assertFalse((self.export_dir / candidate.RECEIPT_NAME).exists())

    def test_export_cannot_bind_inputs_changed_during_archive(self):
        real_command = candidate.command
        profile = self.root / "fixture.mobileprovision"
        profile.write_bytes(b"fixture")

        def simulated(args, **kwargs):
            if args[0] == "bash":
                self.make_export()
                (self.project / "App/App.swift").write_text("// Concurrent change")
                return ""
            return real_command(args, **kwargs)

        with mock.patch.object(candidate, "command", side_effect=simulated), mock.patch.object(candidate, "require_mac_export_tools", return_value=os.environ.copy()), mock.patch.dict(os.environ, {"PIMFLEX_PROFILE_PATH": str(profile), "PIMFLEX_SIGNING_IDENTITY": "A" * 40}):
            with self.assertRaisesRegex(ValueError, "clean committed"):
                candidate.export_candidate(self.project, self.plan_path, self.export_dir, execute=True)
        report = json.loads((self.export_dir / candidate.REPORT_NAME).read_text())
        self.assertNotIn("source_commit", report)

    def test_upload_prepare_is_offline_and_does_not_require_or_read_key(self):
        self.bind_export()
        with mock.patch.object(candidate, "command", wraps=candidate.command) as commands, mock.patch.dict(os.environ, {}, clear=True):
            message = candidate.upload_candidate(self.project, self.plan_path, self.export_dir)
        self.assertIn("preparation only", message)
        self.assertTrue(all(call.args[0][0] == "git" for call in commands.call_args_list))
        self.assertFalse((self.export_dir / candidate.RECEIPT_NAME).exists())

    def test_upload_uses_separate_external_key_and_no_implicit_retry_after_uncertain_result(self):
        self.bind_export()
        key = self.root / "fixture key.p8"
        key.write_text("PRIVATE FIXTURE NOT A VALID KEY")
        real_command = candidate.command
        calls = []

        def simulated(args, **kwargs):
            if args[0] == "bundle":
                calls.append((args, kwargs))
                raise ValueError("Fixture connection failed after upload may have been accepted")
            return real_command(args, **kwargs)

        env = {"PIMFLEX_ASC_KEY_PATH": str(key), "PIMFLEX_ASC_KEY_ID": "FIXTURE", "PIMFLEX_ASC_ISSUER_ID": "fixture-issuer"}
        with mock.patch.object(candidate, "command", side_effect=simulated), mock.patch.object(candidate.platform, "system", return_value="Darwin"), mock.patch.object(candidate.shutil, "which", return_value="/fixture/bundle"), mock.patch.dict(os.environ, env):
            with self.assertRaisesRegex(ValueError, "Fixture connection"):
                candidate.upload_candidate(self.project, self.plan_path, self.export_dir, execute=True)
            with self.assertRaises(FileExistsError):
                candidate.upload_candidate(self.project, self.plan_path, self.export_dir, execute=True)
        self.assertEqual(len(calls), 1)
        self.assertIn("execute:true", calls[0][0])
        self.assertIn("ipa:" + str((self.export_dir / candidate.IPA_NAME).resolve()), calls[0][0])
        self.assertNotIn(key.read_text(), repr(calls[0][0]))
        receipt = json.loads((self.export_dir / candidate.RECEIPT_NAME).read_text())
        self.assertEqual(receipt["state"], "outcome_unknown_check_apple_before_retry")


if __name__ == "__main__":
    unittest.main()
