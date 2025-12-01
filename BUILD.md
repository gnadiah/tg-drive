# Building TG-Drive Executable

This guide explains how to build a standalone Windows executable for TG-Drive.

## Prerequisites

- **Python 3.8+** installed and in PATH
- **Node.js 16+** and npm installed
- **Windows OS** (for building Windows exe)

## Quick Build

### Option 1: Using Python Script (Recommended)

```bash
python build.py
```

This script will:
1. Build the Svelte frontend (if not already built)
2. Install Python dependencies
3. Run PyInstaller to create the executable
4. Generate distribution files

### Option 2: Using Batch Script

```bash
build.bat
```

Double-click `build.bat` or run it from command prompt.

### Option 3: Manual Build

1. **Build Frontend:**
   ```bash
   cd frontend
   npm install
   npm run build
   cd ..
   ```

2. **Install Python Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Build Executable:**
   ```bash
   pyinstaller tg-drive.spec
   ```

## Build Output

After successful build, you'll find:

```
dist/
└── TelegramDrive/
    ├── TelegramDrive.exe    # Main executable
    ├── README.txt           # User instructions
    ├── .env.example         # Environment template
    └── [various DLLs and dependencies]
```

## Distribution

To distribute the application:

1. Copy the entire `dist/TelegramDrive` folder
2. Users need to create a `.env` file with their Telegram API credentials:
   ```
   API_ID=your_api_id
   API_HASH=your_api_hash
   ```
3. Users can get API credentials from https://my.telegram.org/apps

## Customizing the Build

### Changing Application Icon

1. Create or obtain an `.ico` file
2. Edit `tg-drive.spec`
3. Set `icon='path/to/your/icon.ico'` in the `EXE()` section

### Creating Single-File Executable

Edit `tg-drive.spec` and change:

```python
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,      # Add this
    a.zipfiles,      # Add this
    a.datas,         # Add this
    [],
    name='TelegramDrive',
    debug=False,
    # ... other options
)
```

Remove the `COLLECT()` section.

**Note:** Single-file builds are larger, slower to start, and may trigger more antivirus warnings.

### Hiding Console Window

In `tg-drive.spec`, change:
```python
console=True  # Change to False
```

**Warning:** This will hide error messages. Only do this for production builds.

## Troubleshooting

### Build Fails: "Frontend not found"

Make sure `frontend/dist/index.html` exists:
```bash
cd frontend
npm run build
cd ..
```

### Build Fails: "Module not found"

Install all dependencies:
```bash
pip install -r requirements.txt
```

### Executable Doesn't Run

1. Check if `.env` file exists with valid credentials
2. Run from command prompt to see error messages
3. Check Windows Event Viewer for details

### Antivirus Flags Executable

This is a common false positive with PyInstaller:
- **For personal use:** Add exclusion in your antivirus
- **For distribution:** Consider code signing with a certificate
- **Alternative:** Distribute as Python app with instructions to install dependencies

### Missing DLLs

If exe fails with missing DLL errors:
1. Install Visual C++ Redistributable
2. Check PyInstaller warnings during build
3. Manually add DLLs to spec file:
   ```python
   binaries=[('path/to/missing.dll', '.')],
   ```

### Session File Issues

Session files are stored in `%LOCALAPPDATA%\TelegramDrive` by default. If users experience login issues:
1. Delete session files to force fresh login
2. Check folder permissions
3. Verify .env has correct API credentials

## Build Optimization

### Reducing Size

1. **Exclude unused modules** in spec file:
   ```python
   excludes=['tkinter', 'matplotlib', ...],
   ```

2. **Use UPX compression** (enabled by default):
   - Download UPX from https://upx.github.io/
   - Place in PATH
   - PyInstaller will use it automatically

3. **Remove debug symbols:**
   ```python
   strip=True  # Linux/Mac only
   ```

### Improving Startup Time

- Use one-folder build instead of one-file
- Disable UPX (faster startup, larger size):
  ```python
  upx=False
  ```

## Security Notes

- **Never include .env in distribution**
- Session files contain auth tokens - treat as sensitive
- Consider implementing credential encryption
- Code signing recommended for production distribution

## CI/CD Integration

To automate builds:

```yaml
# Example GitHub Actions workflow
steps:
  - uses: actions/checkout@v2
  - uses: actions/setup-python@v2
    with:
      python-version: '3.10'
  - uses: actions/setup-node@v2
    with:
      node-version: '18'
  - run: python build.py
  - uses: actions/upload-artifact@v2
    with:
      name: TelegramDrive
      path: dist/TelegramDrive
```

## Additional Resources

- [PyInstaller Documentation](https://pyinstaller.org/en/stable/)
- [Telegram API Documentation](https://core.telegram.org/api)
- [pywebview Documentation](https://pywebview.flowrl.com/)
