#!/usr/bin/env python3
"""Initialize project structure and create necessary directories."""
import os
import sys

def create_project_structure():
    """Create the required directory structure and files."""
    
    # Create directories
    dirs = ["core", "gui"]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        print(f"Created directory: {d}")
    
    # Create __init__.py files
    inits = {
        "core/__init__.py": '"""Core module for device management and detection."""\n',
        "gui/__init__.py": '"""GUI module for PyQt6 interface."""\n',
    }
    
    for path, content in inits.items():
        with open(path, "w") as f:
            f.write(content)
        print(f"Created: {path}")
    
    print("\nProject structure initialized successfully!")

if __name__ == "__main__":
    create_project_structure()
