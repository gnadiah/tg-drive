# PowerShell script to build TelegramDrive installer
# Requires Inno Setup to be installed

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "TELEGRAM DRIVE - INSTALLER BUILD SCRIPT" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Inno Setup is installed
$InnoSetupPath = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if (-not (Test-Path $InnoSetupPath)) {
    Write-Host "ERROR: Inno Setup not found at $InnoSetupPath" -ForegroundColor Red
    Write-Host "Please install Inno Setup 6 from: https://jrsoftware.org/isdl.php" -ForegroundColor Yellow
    exit 1
}

# Check if dist folder exists
if (-not (Test-Path "dist\TelegramDrive\TelegramDrive.exe")) {
    Write-Host "ERROR: Built application not found in dist\TelegramDrive\" -ForegroundColor Red
    Write-Host "Please run 'python build.py' first to build the application" -ForegroundColor Yellow
    exit 1
}

Write-Host "Step 1: Verifying application build..." -ForegroundColor Green
$exeSize = (Get-Item "dist\TelegramDrive\TelegramDrive.exe").Length / 1MB
Write-Host "  - TelegramDrive.exe found ($($exeSize.ToString('0.00')) MB)" -ForegroundColor White

Write-Host ""
Write-Host "Step 2: Compiling installer with Inno Setup..." -ForegroundColor Green

# Run Inno Setup compiler
try {
    & $InnoSetupPath "installer.iss"
    if ($LASTEXITCODE -ne 0) {
        throw "Inno Setup compilation failed with exit code $LASTEXITCODE"
    }
} catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Step 3: Verifying output..." -ForegroundColor Green

# Check if installer was created
$installerFiles = Get-ChildItem "installer_output\*.exe" -ErrorAction SilentlyContinue
if ($installerFiles) {
    $installer = $installerFiles[0]
    $installerSize = $installer.Length / 1MB
    Write-Host "  - Installer created: $($installer.Name)" -ForegroundColor White
    Write-Host "  - Size: $($installerSize.ToString('0.00')) MB" -ForegroundColor White
} else {
    Write-Host "WARNING: Installer file not found in installer_output\" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "BUILD SUCCESSFUL!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Installer location: installer_output\TelegramDrive-Setup-*.exe" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Test the installer on a clean Windows machine" -ForegroundColor White
Write-Host "2. (Optional) Sign the installer with a code signing certificate" -ForegroundColor White
Write-Host "3. Distribute to users" -ForegroundColor White
Write-Host ""
