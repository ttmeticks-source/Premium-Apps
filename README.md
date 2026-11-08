# Premium Apps

A desktop app launcher built with Rust and [egui](https://github.com/emilk/egui).

## Download / install

**There are currently no prebuilt Windows or macOS installers in this repository.** The steps below download the source code and build the application on your computer. They produce a locally built app; they do not download an installer from GitHub Releases.

### 🍏 macOS

1. Open **Terminal**.
2. Install Rust (if it is not already installed):

   ```bash
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   ```

   Follow the installer prompts, then load Rust into the current Terminal window:

   ```bash
   source "$HOME/.cargo/env"
   ```

3. Download the project and build it:

   ```bash
   git clone https://github.com/ttmeticks-source/Premium-Apps.git
   cd Premium-Apps
   cargo add base64@0.21.7
   cargo build --release
   ```

4. Run the launcher:

   ```bash
   cargo run --release
   ```

   The compiled executable is created under `target/release/`.

### 🪟 Windows 10 / 11

1. Open **PowerShell**.
2. Download and install Rust:

   ```powershell
   Invoke-WebRequest -Uri "https://win.rustup.rs/x86_64" -OutFile "$env:TEMP\rustup-init.exe"
   Start-Process -FilePath "$env:TEMP\rustup-init.exe" -ArgumentList "-y" -Wait
   ```

3. Close PowerShell and open a **new PowerShell window** so the Rust tools are added to PATH.
4. Download the project and build it:

   ```powershell
   git clone https://github.com/ttmeticks-source/Premium-Apps.git
   Set-Location Premium-Apps
   cargo add base64@0.21.7
   cargo build --release
   ```

   If PowerShell says `git` is not recognized, install [Git for Windows](https://git-scm.com/download/win), then reopen PowerShell.

5. Run the launcher:

   ```powershell
   cargo run --release
   ```

   The compiled executable is created at `target\release\premium-apps.exe`.

## Requirements

- macOS or Windows 10/11
- Rust stable toolchain (installed with rustup)
- Git
- Internet access while downloading dependencies and building

The `base64` dependency is added in the build steps because the current source uses it but does not yet list it in `Cargo.toml`.

## App storage

Files added through the app are stored locally in a folder named `PremiumApps_Storage` inside your user home directory. The current source does not provide a hosted download service that automatically distributes uploaded apps to every user's computer.

## Important security notice

This project is still under development. The current source contains a placeholder GitHub token, and its account data model stores passwords as plain text. Do not put a personal GitHub access token in a public repository, and do not use real or reused passwords with this build. A secure server-side authentication and storage implementation is needed before using real accounts or private data.

## Troubleshooting

- **`cargo` is not recognized:** reopen Terminal/PowerShell after installing Rust. On macOS, run `source "$HOME/.cargo/env"`.
- **`git` is not recognized:** install Git and reopen your terminal.
- **Build errors:** make sure the `base64` dependency step completed, then run `cargo build --release` again.
- **No installer found:** this repository currently provides source code, not published `.dmg` or `.exe` installers.

## Source

[GitHub repository](https://github.com/ttmeticks-source/Premium-Apps)

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
