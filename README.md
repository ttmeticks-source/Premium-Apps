# Premium Apps

Simple desktop app launcher for **macOS and Windows**. No Rust, Cargo, or Xcode.

## macOS — install with one command

Open Terminal and paste:

```bash
mkdir -p "$HOME/Applications" && curl -fL "https://github.com/ttmeticks-source/Premium-Apps/releases/download/latest/Premium-Apps-macOS.zip" -o "$TMPDIR/Premium-Apps-macOS.zip" && ditto -x -k "$TMPDIR/Premium-Apps-macOS.zip" "$HOME/Applications" && open "$HOME/Applications/Premium Apps.app"
```

## Windows — install with PowerShell

Open PowerShell and paste:

```powershell
$zip = "$env:TEMP\Premium-Apps-Windows.zip"; $dest = "$env:LOCALAPPDATA\Programs\Premium Apps"; Invoke-WebRequest "https://github.com/ttmeticks-source/Premium-Apps/releases/download/latest/Premium-Apps-Windows.zip" -OutFile $zip; New-Item -ItemType Directory -Force -Path $dest | Out-Null; Expand-Archive -Path $zip -DestinationPath $dest -Force; Start-Process "$dest\Premium Apps.exe"
```

## What it does

- Sign in with a username and password.
- The username `PremiumOwner` displays local controls for adding and removing apps.
- Select an app or file and open it from the library.
- Stores imported items on the current computer.

**Note:** This is a local launcher. The app library and login are not shared or synchronized between computers. The `PremiumOwner` name is a local UI role, not secure online authentication.

## Build downloads

GitHub Actions builds both platforms and publishes the ZIP files to the [latest release](https://github.com/ttmeticks-source/Premium-Apps/releases/tag/latest). The first build runs after this update is pushed; wait for the workflow to finish before using the commands above.

Repository: https://github.com/ttmeticks-source/Premium-Apps
