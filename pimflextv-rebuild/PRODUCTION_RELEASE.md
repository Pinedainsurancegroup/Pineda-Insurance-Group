# PIMFLEX TV Production Release

Current stable QA build: **v3.1.0**

Production hardening lives on branch:

- `pimflextv-production-hardening`

## Important signing rule

The QA signing material used for device testing was previously tracked in the public repository. It must **not** be used for a public production release.

The production branch therefore:

- removes the tracked QA keystore material from the branch;
- removes hard-coded signing passwords from Gradle;
- ignores keystores and signing files;
- reads production signing credentials only from environment variables / GitHub Actions Secrets;
- deletes the restored production keystore from the GitHub Actions runner after the signed build.

Because the QA key existed in public Git history, deleting it from the current branch does not make that old key private again.

## Required GitHub Actions Secrets

Before running the signed production job, add these repository secrets:

- `PIMFLEX_RELEASE_KEYSTORE_B64`
- `PIMFLEX_RELEASE_STORE_PASSWORD`
- `PIMFLEX_RELEASE_KEY_ALIAS`
- `PIMFLEX_RELEASE_KEY_PASSWORD`

Use a **new production keystore** that has never been committed to Git.

## Build workflow

Workflow: `.github/workflows/build-pimflextv-production.yml`

Every push to the hardening branch performs an **unsigned source validation build**.

A manual `workflow_dispatch` additionally attempts the **signed production build**. It stops immediately when any production signing secret is missing.

## Update compatibility

The existing installed QA app is signed with the QA key. A production build signed with a new secure key cannot update that QA installation in place.

Before public production distribution, choose one path:

1. **Fresh production install:** uninstall the QA build once and install the new production-signed app.
2. **Google Play App Signing:** establish the Play production signing lineage before public rollout.

Do not reuse the exposed QA signing key for a public production release.

## Release validation

Before declaring a production build final:

- APK signature verification must pass.
- APK package/application ID must be confirmed.
- APK and AAB SHA-256 hashes must be recorded.
- Install/login/Live TV/Cine/Series/EPG/audio/subtitles/DVR must be smoke-tested on a real device.
- Android TV / Google TV navigation should be checked with D-pad/remote.
- Production build must contain no IPTV usernames/passwords or signing secrets.
