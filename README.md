# Premium Apps

Premium Apps is a dark-and-gold desktop app library for macOS and Windows. Buttons are rounded and use black labels for readability.

## Install

### macOS — Terminal

```bash
mkdir -p "$HOME/Applications" && curl -fL "https://github.com/ttmeticks-source/Premium-Apps/releases/download/latest/Premium-Apps-macOS.zip" -o "$TMPDIR/Premium-Apps-macOS.zip" && ditto -x -k "$TMPDIR/Premium-Apps-macOS.zip" "$HOME/Applications" && open "$HOME/Applications/Premium Apps.app"
```

### Windows — PowerShell

```powershell
$z="$env:TEMP\Premium-Apps-Windows.zip"; $d="$env:LOCALAPPDATA\Programs\Premium Apps"; Invoke-WebRequest "https://github.com/ttmeticks-source/Premium-Apps/releases/download/latest/Premium-Apps-Windows.zip" -OutFile $z; New-Item -ItemType Directory -Force $d | Out-Null; Expand-Archive $z $d -Force; Start-Process "$d\Premium Apps.exe"
```

## Simple tutorial

1. Open Premium Apps. The first launch shows a setup screen.
2. Create an **owner password** and one **shared member password**. Use long passwords.
3. Sign in as **PremiumOwner** with the owner password.
4. Open **SUBMISSIONS** to review apps submitted by members. Check the actual file before approving it.
5. Use **REPORTS** to read support messages. Press **REPLY & NOTIFY** to send a reply.
6. Use **MEMBERS** to see accounts and ban or unban members.
7. Members sign in using their own username and the one shared member password. They cannot change the password.
8. Members download approved apps from **APPS**, submit apps in **PUBLISH**, and contact the owner in **SUPPORT**. Replies show up in **NOTIFICATIONS**.

## Password behavior

There is one shared password for every member account; it is not a per-user password and there is no member password-change screen. The owner account is named `PremiumOwner` and has its own password. Passwords are stored as salted PBKDF2 hashes in the local database, not shown in the member list.

The passwords are created on first launch and stored on that computer. This current build is a **local prototype**: its database, members, app files, reports and notifications are not synchronized to other computers. Choosing the same shared member password on multiple installs does not make their data shared. A hosted backend (for example, Supabase) is required before accounts, bans, published apps and support notifications can work across different users' devices.

## App review and malware safety

Member submissions remain **pending** until the owner approves them. The app performs only basic file-type warnings and records metadata; it does **not** contain an AI malware detector or antivirus engine. A warning-free file is not proof that an app is safe. Scan files with reputable security software and inspect the source before approving them. Do not run unknown programs just because they have been approved in this launcher.

## Build from source (developers only)

End users do **not** need to install Python, CustomTkinter, Tcl/Tk, or any other dependency. The downloaded app/executable bundles its runtime and libraries.

To rebuild on macOS:

```bash
python3 -m pip install --upgrade pyinstaller Pillow customtkinter typing_extensions
python3 scripts/make_icon.py
pyinstaller --clean --noconfirm --windowed --name "Premium Apps" --icon PremiumApps.icns --osx-bundle-identifier com.ttmeticks.premiumapps --collect-all customtkinter --collect-all darkdetect --collect-all typing_extensions --collect-all packaging launcher.py
```

The app bundle is created at `dist/Premium Apps.app`.

To rebuild on Windows:

```powershell
py -m pip install --upgrade pyinstaller Pillow customtkinter typing_extensions
py scripts/make_icon.py
py -m PyInstaller --clean --noconfirm --onefile --windowed --collect-all customtkinter --collect-all darkdetect --collect-all typing_extensions --collect-all packaging --name "Premium Apps" --icon PremiumApps.ico launcher.py
```

