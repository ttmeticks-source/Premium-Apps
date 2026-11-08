# Premium Apps

A lightweight macOS app launcher. **No Rust, Cargo, or Xcode is required.**

## Download for macOS

1. Open the repository's **Actions** tab.
2. Select the latest successful **Build macOS app** run.
3. Under **Artifacts**, download `Premium-Apps-macOS`.
4. Unzip it and move **Premium Apps.app** into Applications.
5. Open it from Applications.

The first build starts automatically after changes are pushed to `main`. You can also start one manually from **Actions → Build macOS app → Run workflow**.

> GitHub Actions produces a zipped `.app` bundle. This repository does not currently publish a signed/notarized installer, so macOS may ask you to confirm opening an app downloaded from the internet.

## Build it yourself

Requires macOS 12 or later and Python 3.11.

```bash
python3 -m pip install --upgrade py2app Pillow
python3 scripts/make_icon.py
python3 setup.py py2app
```

The app will be created at `dist/Premium Apps.app`. Drag it into Applications.

## How it works

- Sign in with a local username and password.
- The username `PremiumOwner` shows the local add/remove controls.
- Add files or app bundles with **＋ ADD APP / FILE**.
- Select an item and choose **OPEN SELECTED**.
- Items are stored in `~/Library/Application Support/Premium Apps/Apps`.

**Important:** This version is a local Mac launcher. Its library is stored on the current Mac and is not automatically shared with other users or devices. The `PremiumOwner` name is a local UI role, not secure online account authentication.

## Windows

This build creates a macOS `.app` only. It does not create a Windows `.exe`.

## Repository

https://github.com/ttmeticks-source/Premium-Apps
