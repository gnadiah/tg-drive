# Building Installer with Inno Setup

This guide explains how to create a Windows installer for TelegramDrive.

## Prerequisites

- **Inno Setup 6** installed (https://jrsoftware.org/isdl.php)
- Built application in `dist/TelegramDrive/` folder

## Quick Start

### Method 1: Using Inno Setup Compiler (GUI)

1. Open **Inno Setup Compiler**
2. File → Open → Select `installer.iss`
3. Click **Build → Compile** (or press F9)
4. Installer will be created in `installer_output/` folder

### Method 2: Command Line

```bash
# Build installer from command line
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```

### Method 3: Automated Build Script

Run the included PowerShell script:

```powershell
.\build_installer.ps1
```

## Output

After compilation, you'll find:

```
installer_output/
└── TelegramDrive-Setup-1.0.0.exe    (Installer ~50-100MB)
```

## What the Installer Does

### Installation
- ✅ Installs to `C:\Program Files\Telegram Drive\`
- ✅ Creates Start Menu shortcuts
- ✅ Optional Desktop icon
- ✅ Includes README and .env.example
- ✅ Optionally creates .env file with API credentials during install

### Uninstallation
- ✅ Removes application files
- ✅ Removes shortcuts
- ✅ Asks if you want to remove session data
- ✅ Cleans temp folders

## Customization

### Change App Version

Edit `installer.iss`:
```iss
#define MyAppVersion "1.0.0"  ; Change this
```

### Change Publisher Name

```iss
#define MyAppPublisher "Your Name/Company"  ; Change this
```

### Add Application Icon

1. Create or obtain a `.ico` file
2. Place it in project root
3. Edit `installer.iss`:
   ```iss
   SetupIconFile=myicon.ico
   ```

### Change Install Location

```iss
DefaultDirName={autopf}\{#MyAppName}  ; Program Files
; or
DefaultDirName={userpf}\{#MyAppName}  ; User's AppData
```

### Add License Agreement

1. Create `LICENSE.txt`
2. Edit `installer.iss`:
   ```iss
   LicenseFile=LICENSE.txt
   ```

## Advanced Features

### Code Signing the Installer

If you have a code signing certificate:

1. Edit `installer.iss`, add to `[Setup]` section:
   ```iss
   SignTool=signtool
   SignedUninstaller=yes
   ```

2. Configure signtool in Inno Setup:
   - Tools → Configure Sign Tools
   - Add: `signtool=C:\Path\To\signtool.exe sign /f "path\to\cert.pfx" /p "password" /t http://timestamp.digicert.com $f`

### Silent Installation

Users can run:
```bash
TelegramDrive-Setup-1.0.0.exe /SILENT
# or
TelegramDrive-Setup-1.0.0.exe /VERYSILENT
```

### Custom Install Parameters

```bash
# Install to custom directory
Setup.exe /DIR="C:\MyCustomPath"

# Skip desktop icon
Setup.exe /TASKS="!desktopicon"
```

## Distribution

The installer (`TelegramDrive-Setup-1.0.0.exe`) can be distributed as:
- Direct download from website
- GitHub Releases
- Microsoft Store (requires Store approval)

**Note:** Unsigned installers will show Windows SmartScreen warning on first run.

## Troubleshooting

### Compilation Errors

**Error: Source file not found**
- Make sure `dist/TelegramDrive/` exists
- Run `python build.py` first to build the app

**Error: Cannot create output directory**
- Check folder permissions
- Close any file in `installer_output/` that might be open

### Size Optimization

To reduce installer size:

1. Use smaller compression:
   ```iss
   Compression=lzma2/fast
   ```

2. Disable solid compression (faster but larger):
   ```iss
   SolidCompression=no
   ```

## File Structure

After installation, users will have:

```
C:\Program Files\Telegram Drive\
├── TelegramDrive.exe
├── _internal\
│   └── [dependencies]
├── README.txt
├── .env.example
└── [.env - if created during install]
```

Session files stored in:
```
%LOCALAPPDATA%\TelegramDrive\
└── telegram_drive_session.session
```
