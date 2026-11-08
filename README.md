# Premium Apps

Premium Apps is a desktop app for macOS and Windows. Downloads include the runtime and app dependencies; users do not need to install Python, Rust, Xcode, CustomTkinter, or other build tools.

## macOS — one Terminal command (Intel + Apple Silicon)

Paste this into Terminal. It automatically detects the Mac's processor and downloads the matching app:

```bash
arch="$(uname -m)"; case "$arch" in arm64) asset="Premium-Apps-macOS-AppleSilicon.zip" ;; x86_64) asset="Premium-Apps-macOS-Intel.zip" ;; *) echo "Unsupported Mac architecture: $arch"; exit 1 ;; esac; mkdir -p "$HOME/Applications" && curl -fL "https://github.com/ttmeticks-source/Premium-Apps/releases/download/latest/$asset" -o "$TMPDIR/Premium-Apps.zip" && ditto -x -k "$TMPDIR/Premium-Apps.zip" "$HOME/Applications" && open "$HOME/Applications/Premium Apps.app"
```

## Windows — one PowerShell command

```powershell
$z="$env:TEMP\Premium-Apps-Windows.zip"; $d="$env:LOCALAPPDATA\Programs\Premium Apps"; Invoke-WebRequest "https://github.com/ttmeticks-source/Premium-Apps/releases/download/latest/Premium-Apps-Windows.zip" -OutFile $z; New-Item -ItemType Directory -Force $d | Out-Null; Expand-Archive $z $d -Force; Start-Process "$d\Premium Apps.exe"
```

## Creating an account

1. Open Premium Apps.
2. Select **CREATE ACCOUNT**.
3. Choose your own username and password. Usernames must be 3–24 characters and may contain letters, numbers, dots, underscores, and hyphens.
4. Use **SIGN IN** with that username and password next time.
5. Use **APPS** to download published apps, **PUBLISH** to submit an app for review, **SUPPORT** to contact support, and **NOTIFICATIONS** to read replies.

Every member account has its own password. Passwords are stored as salted PBKDF2 hashes, not as readable text. There is no shared member password.

The owner signs in separately using the private owner password. The owner username is not shown in the sign-in instructions or member-facing screens.

## Owner tools

The owner can use **SUBMISSIONS** to review member uploads and approve or reject them, **REPORTS** to read and reply to support messages, and **MEMBERS** to ban or unban accounts.

## Important account and security limits

**This is a local desktop prototype, not an online account service.** Each computer has its own local database and app library. Creating an account on one computer does not create that account on another person's computer, and accounts, bans, apps, reports, and notifications do not synchronize between devices. A hosted backend with server-side authentication is required for real shared accounts and cross-device access.

The owner credential is checked locally by the desktop app. A public desktop application cannot provide the same protection as server-side authentication; a determined user with access to the app files can inspect or modify local code. Do not use this prototype to protect sensitive information.

Member submissions remain hidden until owner approval. The current file check only gives basic extension warnings; it is not antivirus or an AI malware scan. Manually inspect submissions and use reputable security software before approving them.

## Build information

GitHub Actions builds separate native macOS versions for Intel (`x86_64`) and Apple Silicon (`arm64`), plus a Windows executable. Each download bundles the required app runtime. The macOS workflow checks the executable architecture before publishing.

Repository: https://github.com/ttmeticks-source/Premium-Apps
