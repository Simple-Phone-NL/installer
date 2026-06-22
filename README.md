## Installation

### 1. Install Python (only if its not already installed)
Download Python 3.8+ from https://www.python.org/downloads/ and install. 

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

## Usage

### Starting the GUI
```bash
python main_gui.py
```

### Custom CLI Feature
The GUI includes a CLI for running custom adb and fastboot commands:

1. **Open CLI dialog**: Click the "⚙️ Custom CLI" button on the right panel
2. **Run commands**: 
   - Type `adb logcat` (will use full path to adb.exe from apt folder)
   - Type `fastboot devices` (will use full path to fastboot.exe from apt folder)
   - Type any adb/fastboot command as you would normally
3. **Select device**: Use the device dropdown to target a specific device (for adb commands)
4. **View output**: Results appear in the output area with success/error feedback

**Command examples:**
- `adb logcat` - View device logs
- `adb shell pm list packages` - List installed packages
- `adb shell getprop ro.build.version.release` - Get Android version
- `fastboot devices` - List devices in fastboot mode
- `adb shell reboot` - Reboot device
