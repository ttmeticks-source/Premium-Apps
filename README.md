# Premium Apps

Premium Apps is a self-contained desktop app for macOS and Windows. Downloads include the runtime and app dependencies; users do not need to install Python, Rust, Xcode, CustomTkinter, or other build tools.

## macOS — one Terminal command (Intel + Apple Silicon)

Paste this into Terminal. It automatically detects the Mac's processor and downloads the matching app:

```bash
arch="$(uname -m)"; case "$arch" in arm64) asset="Premium-Apps-macOS-AppleSilicon.zip" ;; x86_64) asset="Premium-Apps-macOS-Intel.zip" ;; *) echo "Unsupported Mac architecture: $arch"; exit 1 ;; esac; mkdir -p "$HOME/Applications" && curl -fL "https://github.com/ttmeticks-source/Premium-Apps/releases/download/latest/$asset" -o "$TMPDIR/Premium-Apps.zip" && ditto -x -k "$TMPDIR/Premium-Apps.zip" "$HOME/Applications" && open "$HOME/Applications/Premium Apps.app"
```

## Windows — one PowerShell command

```powershell
$z="$env:TEMP\Premium-Apps-Windows.zip"; $d="$env:LOCALAPPDATA\Programs\Premium Apps"; Invoke-WebRequest "https://github.com/ttmeticks-source/Premium-Apps/releases/download/latest/Premium-Apps-Windows.zip" -OutFile $z; New-Item -ItemType Directory -Force $d | Out-Null; Expand-Archive $z $d -Force; Start-Process "$d\Premium Apps.exe"
```

## Simple tutorial

1. Open Premium Apps. The first launch shows a setup screen.
2. Create the owner password and the one shared member password.
3. Sign in as `PremiumOwner` with the owner password.
4. Use **SUBMISSIONS** to check member uploads and approve or reject them.
5. Use **REPORTS** to read support messages and reply with notifications.
6. Use **MEMBERS** to view member accounts and ban or unban accounts.
7. Members sign in with their own username and the shared member password. They cannot change it.
8. Members use **APPS** for approved downloads, **PUBLISH** to submit apps for review, and **SUPPORT** to contact the owner.

## Security and account notes

The owner account has a separate password. All member accounts use one shared password. Passwords are stored as salted PBKDF2 hashes, not displayed in the member list.

**This is still a local prototype.** Accounts, bans, apps, reports, and notifications are stored on the individual computer and do not synchronize between different members' computers. A shared backend is required for a real multi-user service.

Member submissions remain hidden until owner approval. The current file check is only a basic extension warning; it is not an antivirus or AI malware scan. A warning-free file is not proof that it is safe. Manually inspect submissions and use reputable security software before approving them.

## Build information

GitHub Actions builds separate native macOS versions for Intel (`x86_64`) and Apple Silicon (`arm64`), plus a Windows executable. Each download bundles the required app runtime. The macOS workflow checks the executable architecture before publishing.

The build process is intended for maintainers. End users only need the install commands above.

Repository: https://github.com/ttmeticks-source/Premium-Apps
