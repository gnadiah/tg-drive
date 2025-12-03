@echo off
REM Build script for TG-Drive on Windows
REM Simple batch file alternative to build.py

echo ============================================================
echo TG-DRIVE BUILD SCRIPT
echo ============================================================

REM Step 1: Build Frontend
echo.
echo === Building Frontend ===
cd frontend
if not exist "node_modules" (
    echo Installing frontend dependencies...
    call npm install
    if errorlevel 1 (
        echo ERROR: Failed to install frontend dependencies
        exit /b 1
    )
)

echo Building frontend...
call npm run build
if errorlevel 1 (
    echo ERROR: Frontend build failed
    exit /b 1
)
cd ..

REM Step 2: Install Python Dependencies
echo.
echo === Installing Python Dependencies ===
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install Python dependencies
    exit /b 1
)

REM Step 3: Clean previous builds
echo.
echo === Cleaning Previous Builds ===
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist

REM Step 4: Build Executable
echo.
echo === Building Executable ===
pyinstaller tg-drive.spec
if errorlevel 1 (
    echo ERROR: PyInstaller build failed
    exit /b 1
)

REM Step 5: Create README
echo.
echo === Creating Distribution Files ===
(
echo TELEGRAM DRIVE - Desktop Application
echo =====================================
echo.
echo SETUP INSTRUCTIONS
echo ------------------
echo.
echo 1. Create a .env file in the same directory as this executable with:
echo.
echo    API_ID=your_api_id
echo    API_HASH=your_api_hash
echo.
echo    Get these from: https://my.telegram.org/apps
echo.
echo 2. Double-click TelegramDrive.exe to run
echo.
echo 3. Login using phone number or QR code
echo.
echo.
echo DATA STORAGE
echo ------------
echo.
echo - Session files: %%LOCALAPPDATA%%\TelegramDrive
echo - Files stored in Telegram's "Saved Messages"
) > dist\TelegramDrive\README.txt

echo API_ID=your_api_id_here> dist\TelegramDrive\.env.example
echo API_HASH=your_api_hash_here>> dist\TelegramDrive\.env.example

echo.
echo ============================================================
echo BUILD SUCCESSFUL!
echo ============================================================
echo.
echo Executable location: dist\TelegramDrive\TelegramDrive.exe
echo.
echo Next steps:
echo 1. Copy dist\TelegramDrive folder to your desired location
echo 2. Run TelegramDrive.exe
echo.
echo ============================================================

pause
