#!/usr/bin/env python3
"""
Setup Helper - Run this script once to prepare the environment.
This ensures all directories are created and dependencies are checked.
"""
import os
import sys
import subprocess

def main():
    print("=" * 60)
    print("ROM Installer GUI - Setup Helper")
    print("=" * 60)
    
    # Check Python version
    version = sys.version_info
    print(f"\n✓ Python version: {version.major}.{version.minor}.{version.micro}")
    if version < (3, 8):
        print("❌ Python 3.8+ required")
        sys.exit(1)
    
    # Create directories
    print("\n[1/3] Creating directories...")
    dirs = ["core", "gui", "downloads"]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        print(f"  ✓ {d}/")
    
    # Create __init__.py files
    print("\n[2/3] Creating package files...")
    for init_file in ["core/__init__.py", "gui/__init__.py"]:
        if not os.path.exists(init_file):
            with open(init_file, "w") as f:
                f.write('"""Package module."""\n')
        print(f"  ✓ {init_file}")
    
    # Check dependencies
    print("\n[3/3] Checking dependencies...")
    try:
        import PyQt6
        print(f"  ✓ PyQt6 (version: {PyQt6.__version__})")
    except ImportError:
        print("  ❌ PyQt6 not installed")
        print("\n  Run: pip install -r requirements.txt")
        sys.exit(1)
    
    try:
        import requests
        print(f"  ✓ requests")
    except ImportError:
        print("  ❌ requests not installed")
        print("\n  Run: pip install -r requirements.txt")
        sys.exit(1)
    
    # Check adb/fastboot
    print("\n[Extra] Checking adb/fastboot binaries...")
    adb_path = os.path.join("apt", "adb")
    fastboot_path = os.path.join("apt", "fastboot")
    
    adb_exists = os.path.exists(adb_path)
    fastboot_exists = os.path.exists(fastboot_path)
    
    if adb_exists:
        print(f"  ✓ adb found at {adb_path}")
    else:
        print(f"  ⚠️  adb NOT found at {adb_path}")
        print("     Please ensure adb binary is in apt/ directory")
    
    if fastboot_exists:
        print(f"  ✓ fastboot found at {fastboot_path}")
    else:
        print(f"  ⚠️  fastboot NOT found at {fastboot_path}")
        print("     Please ensure fastboot binary is in apt/ directory")
    
    print("\n" + "=" * 60)
    print("✅ Setup complete!")
    print("=" * 60)
    print("\nYou can now run: python main_gui.py")
    print("\nFor quick start, see: QUICKSTART.md")
    print("For full docs, see: GUI_README.md")
    print()

if __name__ == "__main__":
    main()
