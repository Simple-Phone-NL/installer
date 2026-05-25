#!/usr/bin/env python3
import os
import sys

# Create directory structure
os.makedirs("core", exist_ok=True)
os.makedirs("gui", exist_ok=True)
os.makedirs("downloads", exist_ok=True)

# Create __init__.py files
open("core/__init__.py", "w").write('"""Core module for device management and detection."""\n')
open("gui/__init__.py", "w").write('"""GUI module for PyQt6 interface."""\n')

print("Directories created successfully")
print(f"Created: core/, gui/, downloads/")
