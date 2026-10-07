# PIMFLEX TV: reference 4.0.2 review and isolated preview

Review date: 2026-10-07. Stable baseline: commit `f5071a187011987c4b7b51f6e0bc548192724313`, after `apply_release_patches.sh` (v3.1.0).

The supplied reference APK and AAB both identify as `com.pimflextv.pimflextviptvbox`, v4.0.2 / code 102, minSdk 21, targetSdk 34. ZIP CRC validation passes on both. Their three application DEX files, 47 native libraries and 17 assets are byte-identical. The APK verifies with v1/v2 signatures. `jarsigner -verify` verifies the AAB; its certificate is self-signed. `bundletool validate` accepts the bundle. Both use certificate SHA-256 `f3e08ab62195091ae0afc123401b236029f3092e872cc5b4da587f990a852fab`.

Only original presentation code is included here. No extracted reference code, resources, server credentials, signing keys or binaries are committed.

## Changes in this preview

- Original native home screen with Live TV, Movies, Series, EPG, recordings, catch-up and multiscreen routing to existing code.
- Working overflow menu and direct shortcuts for search, downloads, radio and favorites.
- Original vector-style icons, visible D-pad focus and compact sizing.
- Live clock using the saved 12/24-hour format.
- Category timestamps recorded after a successful category request; no invented "updated now" label.
- Accurate labels for external VPN and customer portal integrations.
- Debug application ID `com.pimflextv.next.reference`, label `PIMFLEX TV Prueba`, version `3.2.0-reference.1`. Installs alongside stable v3.1.0 and starts with separate account storage.

## Reproduce

Use a fresh checkout. Java 17, Gradle 8.13, Android platform 36 and build-tools 36.0.0 are required.

```sh
cd pimflextv-rebuild
bash apply_release_patches.sh
cp app/src/main/java/com/pimflextv/next/MainActivity.java /tmp/pimflex-stable.java
python3 patch_v32_reference_home.py
python3 verify_reference_scope.py /tmp/pimflex-stable.java
gradle :app:assembleDebug :app:bundleDebug --no-daemon
```

The production workflow and stable patch chain are unchanged. The reference workflow builds a debug preview only; it does not sign or publish a production release. Debug keys from hosted runners may differ between runs. Preview builds are disposable, not an update channel.

## Scope and remaining gaps

Static references establish that code/resources exist, not that every feature is reachable or configured for this branded variant. No authenticated reference server was contacted. No device playback equivalence is claimed.

| Feature | Current implementation | Remaining validation / gap |
|---|---|---|
| Xtream, M3U, live TV, VOD, series | Existing native code | Device and authorized account smoke test |
| EPG, catch-up | Existing native code | Depends on provider EPG/archive data |
| Multiscreen | Existing ExoPlayer implementation | Provider connection allowance and device load |
| Audio, subtitles, resume, favorites | Existing code | Device regression test |
| Recording, downloads, local media | Existing code | Android background behavior and file access |
| Cast | Lazy Cast integration | Real Chromecast and supported streams |
| VPN | Opens an installed VPN app | Not equivalent to reference's embedded OpenVPN |
| Customer billing / tickets | Configurable external portal | Not reference's integrated WHMCS flow |
| Announcements | Configurable JSON feed | Own feed required; not full reference push system |
| TV code pairing | Not implemented | Own pairing service and expiry/revocation flow required |
| Production release | Existing draft PR #4 | Signed workflow and device release approval still separate |

Reference includes 42 declared permissions, advertising/analytics SDKs and five native ABIs. SDK presence does not prove runtime tracking. Of 22 arm64-v8a/x86_64 shared libraries, 19 have at least one ELF LOAD alignment below 16 KB. Do not copy those binaries into the app; current Android compatibility needs separate review. The existing v3.1.0 player dependencies were intentionally preserved.

Backup note: the stable export filters secret-like preference keys, but URL-valued preferences can contain embedded provider credentials. A future hardening change should explicitly redact sensitive URL query/path data, with migration tests. This preview does not alter account storage or backup behavior.

## Validation gate

`verify_reference_scope.py` compares all stable method regions and rejects any change outside the eight reviewed presentation regions. Playback/authentication/stream URLs/recording/account storage remain unchanged. Compilation and binary verification are additional checks; actual phone and TV operation require device testing.

Primary technical references:
- https://developer.android.com/studio/publish/app-signing
- https://developer.android.com/guide/practices/page-sizes
- https://developer.android.com/tools/bundletool

Reference file hashes:
- APK: `c1fa614b2e2aec9399bbde9ca91491b8a4f03e010bd47a4074e57d7b0f6f6a36`
- AAB: `852be7a751dfb44264deccb2f85aa0b2a2375f7d1146ca1a71d5d4d410ef6fe9`
