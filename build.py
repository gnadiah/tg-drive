#!/usr/bin/env python3
"""
Build script for TG-Drive executable
Automates the process of building the frontend and packaging the Python app
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a command and print output"""
    print(f"\n>>> Running: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.returncode != 0:
        print(f"ERROR: {result.stderr}")
        return False
    return True

def check_frontend_built():
    """Check if frontend is built"""
    dist_path = Path("frontend/dist/index.html")
    return dist_path.exists()

def build_frontend():
    """Build the frontend using npm"""
    print("\n=== Building Frontend ===")
    frontend_dir = Path("frontend")
    
    if not frontend_dir.exists():
        print("ERROR: Frontend directory not found!")
        return False
    
    # Check if node_modules exists
    if not (frontend_dir / "node_modules").exists():
        print("Installing frontend dependencies...")
        if not run_command("npm install", cwd=str(frontend_dir)):
            return False
    
    # Build frontend
    print("Building frontend...")
    if not run_command("npm run build", cwd=str(frontend_dir)):
        return False
    
    # Verify build output
    if not check_frontend_built():
        print("ERROR: Frontend build failed - dist/index.html not found!")
        return False
    
    print("✓ Frontend built successfully")
    return True

def install_python_deps():
    """Install Python dependencies"""
    print("\n=== Installing Python Dependencies ===")
    if not run_command(f"{sys.executable} -m pip install -r requirements.txt"):
        return False
    print("✓ Python dependencies installed")
    return True

def build_exe():
    """Build the executable using PyInstaller"""
    print("\n=== Building Executable ===")
    
    # Clean previous builds
    for path in ["build", "dist"]:
        if Path(path).exists():
            print(f"Cleaning {path}/...")
            shutil.rmtree(path)
    
    # Run PyInstaller
    if not run_command("pyinstaller tg-drive.spec"):
        return False
    
    print("✓ Executable built successfully")
    return True

def create_readme():
    """Create README for distribution"""
    print("\n=== Creating Distribution README ===")
    
#!/usr/bin/env python3
"""
Build script for TG-Drive executable
Automates the process of building the frontend and packaging the Python app
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a command and print output"""
    print(f"\n>>> Running: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.returncode != 0:
        print(f"ERROR: {result.stderr}")
        return False
    return True

def check_frontend_built():
    """Check if frontend is built"""
    dist_path = Path("frontend/dist/index.html")
    return dist_path.exists()

def build_frontend():
    """Build the frontend using npm"""
    print("\n=== Building Frontend ===")
    frontend_dir = Path("frontend")
    
    if not frontend_dir.exists():
        print("ERROR: Frontend directory not found!")
        return False
    
    # Check if node_modules exists
    if not (frontend_dir / "node_modules").exists():
        print("Installing frontend dependencies...")
        if not run_command("npm install", cwd=str(frontend_dir)):
            return False
    
    # Build frontend
    print("Building frontend...")
    if not run_command("npm run build", cwd=str(frontend_dir)):
        return False
    
    # Verify build output
    if not check_frontend_built():
        print("ERROR: Frontend build failed - dist/index.html not found!")
        return False
    
    print("✓ Frontend built successfully")
    return True

def install_python_deps():
    """Install Python dependencies"""
    print("\n=== Installing Python Dependencies ===")
    if not run_command(f"{sys.executable} -m pip install -r requirements.txt"):
        return False
    print("✓ Python dependencies installed")
    return True

def build_exe():
    """Build the executable using PyInstaller"""
    print("\n=== Building Executable ===")
    
    # Clean previous builds
    for path in ["build", "dist"]:
        if Path(path).exists():
            print(f"Cleaning {path}/...")
            shutil.rmtree(path)
    
    # Run PyInstaller
    if not run_command("pyinstaller tg-drive.spec"):
        return False
    
    print("✓ Executable built successfully")
    return True

def create_readme():
    """Create README for distribution"""
    print("\n=== Creating Distribution README ===")
    
    readme_content = """TELEGRAM DRIVE - Desktop Application
=====================================

SETUP INSTRUCTIONS
------------------

1. Double-click TelegramDrive.exe to run the application

2. Login using phone number or QR code


DATA STORAGE
------------

- Session files are stored in: %LOCALAPPDATA%\\TelegramDrive
- Your files are stored in Telegram's "Saved Messages"


TROUBLESHOOTING
---------------

- If antivirus blocks the exe, add it to exclusions
- Session files are in AppData/Local/TelegramDrive


SUPPORT
-------

For issues, please check the project repository
"""
    
    dist_dir = Path("dist/TelegramDrive")
    if dist_dir.exists():
        readme_path = dist_dir / "README.txt"
        readme_path.write_text(readme_content, encoding='utf-8')
        print(f"✓ Created {readme_path}")
        

    
    return True

def main():
    """Main build process"""
    print("=" * 60)
    print("TG-DRIVE BUILD SCRIPT")
    print("=" * 60)
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Step 1: Build frontend if needed
    if not check_frontend_built():
        print("\nFrontend not built, building now...")
        if not build_frontend():
            print("\n✗ Build FAILED at frontend build stage")
            return 1
    else:
        print("\n✓ Frontend already built")
    
    # Step 2: Install Python dependencies
    if not install_python_deps():
        print("\n✗ Build FAILED at dependency installation stage")
        return 1
    
    # Step 3: Build executable
    if not build_exe():
        print("\n✗ Build FAILED at executable build stage")
        return 1
    
    # Step 4: Create distribution files
    create_readme()
    
    # Success!
    print("\n" + "=" * 60)
    print("BUILD SUCCESSFUL!")
    print("=" * 60)
    print(f"\nExecutable location: dist/TelegramDrive/TelegramDrive.exe")
    print("\nNext steps:")
    print("1. Copy dist/TelegramDrive folder to your desired location")
    print("2. Run TelegramDrive.exe")
    print("\n" + "=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
