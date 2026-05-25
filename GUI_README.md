# Custom ROM Multi-Device Installer - GUI

A PyQt6-based graphical interface for installing custom ROMs on multiple Android devices simultaneously.

## Features

### Device Management
- **Multi-device support**: Detect and manage multiple connected devices
- **Real-time detection**: Devices are automatically detected and listed (updates every 2 seconds)
- **Device information**: Shows serial number, device name, current state, and progress per device
- **Device states**: Automatically identifies devices in ADB, Fastboot, or Recovery mode

### Control & Automation
- **Selective targeting**: Use checkboxes to select which devices to apply actions to
- **Batch operations**: Execute same action on multiple devices at once
- **9 automation buttons** for complete workflow:
  - 📥 **Update Files**: Download latest ROM files (splash.img, recovery.img, software.zip)
  - 🔄 **Reboot to Bootloader**: Reboot selected devices to fastboot mode
  - ⚡ **Flash Recovery**: Flash recovery and splash images to bootloader devices
  - ↩️ **Reboot to Recovery**: Reboot devices to recovery mode
  - 📦 **Sideload Software**: Sideload software.zip in recovery mode
  - 🔌 **Reboot to System**: Reboot devices to normal system
  - 🛠️ **Manual Install Script**: Custom installation logic (implement as needed)
  - 🔍 **Refresh Devices**: Force rescan for connected devices
  - 🗑️ **Clear Downloads**: Delete downloaded ROM files
  - ⚠️ **Reset All Devices**: Emergency reboot all selected devices

### User Experience
- **Status log**: Real-time logging of all operations
- **Progress tracking**: Per-device progress bars for visual feedback
- **Error handling**: Graceful error messages without application crashes
- **Responsive UI**: Background threads prevent UI freezing during operations

## Installation

### 1. Install Python
Download Python 3.8+ from https://www.python.org/downloads/ and install.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

This installs:
- **PyQt6**: GUI framework
- **requests**: File downloading

### 3. Verify Setup
Ensure your ROM files are placed in the `downloads/` directory, or use the "Update Files" button to download them.

## Usage

### Starting the GUI
```bash
python main_gui.py
```

The application will:
1. Create necessary directories (`core/`, `gui/`, `downloads/`)
2. Start the device detector in the background
3. Display the main window

### Basic Workflow

#### For First-Time Installation (Update Files + Install)
1. **Connect devices** to your computer via USB
2. **Click "Update Files"** to download splash.img, recovery.img, and software.zip
3. **Select devices** using checkboxes
4. **Click "Reboot to Bootloader"** (devices must be powered on with ADB access)
5. **Click "Flash Recovery"** when devices appear in fastboot mode
6. Follow on-device prompts to enter recovery
7. **Click "Sideload Software"** to flash the custom ROM
8. **Click "Reboot to System"** to complete installation

#### For Already-In-Fastboot Devices
1. Ensure devices are in fastboot mode
2. Select devices
3. Click "Flash Recovery"
4. Continue from step 5 above

#### For Already-In-Recovery Devices
1. Ensure devices are in recovery mode with ADB sideload enabled
2. Select devices
3. Click "Sideload Software"
4. Click "Reboot to System"

## Customization

### Adding Custom Installation Logic

Edit `main_gui.py` and modify the `on_manual_install()` method:

```python
def on_manual_install(self):
    """Run custom install script on selected devices."""
    if not self.selected_devices:
        QMessageBox.warning(self, "No Device", "Please select at least one device")
        return
    
    for serial in self.selected_devices:
        self.log(f"⏳ Custom install on {serial}...")
        # Add your custom logic here
        success, output = your_custom_function(serial)
        if success:
            self.log(f"✓ {serial} custom install completed")
        else:
            self.log(f"✗ Failed on {serial}: {output}")
```

### Adding New Buttons

1. In `setup_ui()`, create a new button:
```python
self.btn_my_action = QPushButton("🎯 My Custom Action")
self.btn_my_action.clicked.connect(self.on_my_action)
right_layout.addWidget(self.btn_my_action)
```

2. Add the handler method:
```python
def on_my_action(self):
    """Handle custom action."""
    if not self.selected_devices:
        QMessageBox.warning(self, "No Device", "Please select at least one device")
        return
    
    for serial in self.selected_devices:
        # Your logic here
        self.log(f"Action executed on {serial}")
```

### Adjusting Device Detection Interval

In `DeviceDetectorThread.run()`, modify the sleep time:
```python
time.sleep(2)  # Change 2 to your desired seconds (e.g., 1 or 5)
```

## File Structure

```
.
├── main_gui.py                 # Main PyQt6 GUI application
├── requirements.txt            # Python dependencies
├── README.md                   # Original CLI documentation
├── GUI_README.md              # This file
├── installer.py               # Original CLI installer (kept for reference)
├── apt/                        # ADB and Fastboot binaries
│   ├── adb
│   └── fastboot
├── downloads/                  # Downloaded ROM files (auto-created)
│   ├── splash.img
│   ├── recovery.img
│   └── software.zip
├── core/                       # Core modules (auto-created)
│   └── __init__.py
└── gui/                        # GUI modules (auto-created)
    └── __init__.py
```

## Troubleshooting

### Devices Not Detected
1. Ensure USB debugging is enabled on the device
2. Click "Refresh Devices" button
3. Check that `apt/adb` and `apt/fastboot` binaries exist
4. Run `apt/adb devices` from command line to verify

### Permission Denied Errors (Linux/Mac)
```bash
chmod +x apt/adb apt/fastboot
```

### PyQt6 Installation Issues
```bash
pip install --upgrade pip
pip install PyQt6 --no-cache-dir
```

### Files Not Found During Flash/Sideload
1. Click "Update Files" to download them
2. Verify they exist in `downloads/` directory
3. Check file permissions

## Advanced Features

### Progress Tracking
Each device has a progress bar showing operation status (0-100%).

### Real-time Status Log
All operations are logged with timestamps:
- ✓ Green checkmarks indicate successful operations
- ✗ Red X marks indicate failures
- ⏳ Hourglass indicates operations in progress

### Multi-threading
All device operations run in background threads, preventing UI freezing.

## Support

For issues or feature requests, refer to the repository's issue tracker.

## License

Same as parent project (see LICENSE file in repository root).
