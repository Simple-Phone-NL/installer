# Customization Guide - ROM Installer GUI

This guide walks you through customizing the GUI to implement your specific ROM installation process.

## Overview

The GUI provides the multi-device framework and UI. You'll customize three main areas:

1. **File Downloads** - `on_update_files()`
2. **Manual Installation Script** - `on_manual_install()`
3. **Additional Buttons** (optional) - Add custom actions

## 1. Implementing File Downloads

### Find the Method
In `main_gui.py`, locate:
```python
def on_update_files(self):
    """Download update files."""
    if not self.selected_devices:
        QMessageBox.warning(self, "No Device", "Please select at least one device")
        return
    
    self.log("⏳ Downloading files...")
    # Placeholder - implement file download logic here
    self.log("✓ File download feature not yet implemented")
```

### Add Download Logic

#### Option A: Simple HTTP Download (Recommended)
```python
def on_update_files(self):
    """Download update files."""
    if not self.selected_devices:
        QMessageBox.warning(self, "No Device", "Please select at least one device")
        return
    
    import requests
    
    files_to_download = {
        "splash.img": "https://updates.simplephone.nl/builds/parts/splash.img",
        "recovery.img": "https://updates.simplephone.nl/builds/parts/recovery.img",
        "software.zip": "https://updates.simplephone.nl/builds/parts/software.zip",
    }
    
    for filename, url in files_to_download.items():
        self.log(f"⏳ Downloading {filename}...")
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            filepath = os.path.join("downloads", filename)
            
            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded * 100) // total_size
                            self.log(f"  {filename}: {percent}%")
            
            self.log(f"✓ Downloaded {filename}")
        except Exception as e:
            self.log(f"✗ Failed to download {filename}: {e}")
```

#### Option B: Using Your Custom API
```python
def on_update_files(self):
    """Download update files from custom API."""
    if not self.selected_devices:
        QMessageBox.warning(self, "No Device", "Please select at least one device")
        return
    
    import requests
    
    self.log("⏳ Fetching ROM metadata from server...")
    try:
        # Call your API to get latest ROM info
        response = requests.get("https://your-rom-server.com/api/latest")
        response.raise_for_status()
        rom_info = response.json()
        
        download_urls = {
            "splash.img": rom_info["splash_url"],
            "recovery.img": rom_info["recovery_url"],
            "software.zip": rom_info["software_url"],
        }
        
        for filename, url in download_urls.items():
            self.log(f"⏳ Downloading {filename} from {url[:50]}...")
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            filepath = os.path.join("downloads", filename)
            with open(filepath, "wb") as f:
                f.write(response.content)
            
            self.log(f"✓ {filename} downloaded")
    except Exception as e:
        self.log(f"✗ Error: {e}")
```

## 2. Implementing Manual Installation Script

### Find the Method
In `main_gui.py`, locate:
```python
def on_manual_install(self):
    """Run manual install script on selected devices."""
    if not self.selected_devices:
        QMessageBox.warning(self, "No Device", "Please select at least one device")
        return
    
    self.log("⏳ Manual install not yet implemented - customize this function")
    QMessageBox.information(self, "Manual Install", "Customize on_manual_install() to add your installation logic")
```

### Add Your Installation Logic

#### Example 1: Full Installation Workflow
```python
def on_manual_install(self):
    """Execute full ROM installation workflow."""
    if not self.selected_devices:
        QMessageBox.warning(self, "No Device", "Please select at least one device")
        return
    
    for serial in self.selected_devices:
        self.log(f"⏳ Starting installation on {serial}...")
        
        try:
            # Step 1: Ensure in ADB mode
            state = self.device_manager.get_device_state(serial)
            if state == "Offline":
                self.log(f"✗ {serial}: Device offline")
                continue
            
            if state == "ADB":
                self.log(f"✓ {serial}: In ADB mode")
                # Proceed to bootloader
                success, output = self.device_manager.reboot_bootloader(serial)
                if not success:
                    self.log(f"✗ {serial}: Failed to reboot - {output}")
                    continue
                self.log(f"⏳ {serial}: Rebooting to bootloader (wait 10s)...")
                import time
                time.sleep(10)
            
            # Step 2: Flash recovery
            success, output = self.device_manager.flash_recovery(serial)
            if success:
                self.log(f"✓ {serial}: Recovery flashed")
            else:
                self.log(f"✗ {serial}: Flash failed - {output}")
                continue
            
            # Step 3: Wait for recovery boot
            self.log(f"⏳ {serial}: Waiting for recovery (manual: hold Vol+Power)...")
            import time
            time.sleep(30)
            
            # Step 4: Sideload software
            success, output = self.device_manager.sideload_software(serial)
            if success:
                self.log(f"✓ {serial}: Software sideloaded")
            else:
                self.log(f"✗ {serial}: Sideload failed - {output}")
                continue
            
            # Step 5: Reboot to system
            self.log(f"⏳ {serial}: Rebooting to system...")
            success, output = self.device_manager.reboot_system(serial)
            if success:
                self.log(f"✓ {serial}: Installation complete!")
            else:
                self.log(f"✗ {serial}: Final reboot failed - {output}")
        
        except Exception as e:
            self.log(f"✗ {serial}: Unexpected error - {e}")
```

#### Example 2: Run External Script
```python
def on_manual_install(self):
    """Run external installation script per device."""
    if not self.selected_devices:
        QMessageBox.warning(self, "No Device", "Please select at least one device")
        return
    
    import subprocess
    
    for serial in self.selected_devices:
        self.log(f"⏳ Running custom install for {serial}...")
        
        try:
            # Call external script with serial number
            result = subprocess.run(
                ["python", "install_rom.py", serial],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                self.log(f"✓ {serial}: Installation complete")
                if result.stdout:
                    for line in result.stdout.split('\n'):
                        if line.strip():
                            self.log(f"  {line}")
            else:
                self.log(f"✗ {serial}: Installation failed")
                if result.stderr:
                    self.log(f"  Error: {result.stderr}")
        except Exception as e:
            self.log(f"✗ {serial}: Failed to run script - {e}")
```

#### Example 3: Check and Verify
```python
def on_manual_install(self):
    """Install with verification steps."""
    if not self.selected_devices:
        QMessageBox.warning(self, "No Device", "Please select at least one device")
        return
    
    for serial in self.selected_devices:
        self.log(f"⏳ Installing ROM on {serial}...")
        
        # Check device state
        state = self.device_manager.get_device_state(serial)
        self.log(f"  Device state: {state}")
        
        # Verify files exist
        required_files = ["recovery.img", "splash.img", "software.zip"]
        for filename in required_files:
            filepath = self.device_manager.get_file_path(filename)
            if os.path.exists(filepath):
                size_mb = os.path.getsize(filepath) / (1024 * 1024)
                self.log(f"  ✓ {filename} ({size_mb:.1f} MB)")
            else:
                self.log(f"  ✗ {filename} missing - run Update Files first")
                break
        
        # Run installation
        try:
            # Your custom install logic here
            self.log(f"✓ {serial}: Installation successful")
        except Exception as e:
            self.log(f"✗ {serial}: {e}")
```

## 3. Adding Custom Buttons

### Add Button to UI
In the `setup_ui()` method, find the button section and add:

```python
# In setup_ui(), after existing buttons:
self.btn_my_custom_action = QPushButton("🎯 My Custom Action")
self.btn_my_custom_action.setStyleSheet(button_style)
self.btn_my_custom_action.clicked.connect(self.on_my_custom_action)
right_layout.addWidget(self.btn_my_custom_action)
```

### Add Handler Method
```python
def on_my_custom_action(self):
    """Handle custom action on selected devices."""
    if not self.selected_devices:
        QMessageBox.warning(self, "No Device", "Please select at least one device")
        return
    
    for serial in self.selected_devices:
        self.log(f"⏳ Custom action on {serial}...")
        try:
            # Your logic here
            success, output = self.device_manager.run_command(
                f"{self.device_manager.adb} shell your_command",
                serial
            )
            if success:
                self.log(f"✓ {serial}: Action succeeded")
            else:
                self.log(f"✗ {serial}: Action failed - {output}")
        except Exception as e:
            self.log(f"✗ {serial}: Error - {e}")
```

## 4. Adding Per-Device Actions

### Create Context Menu
```python
def setup_ui(self):
    # ... existing code ...
    
    # Add context menu to device table
    self.device_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    self.device_table.customContextMenuRequested.connect(self.show_device_context_menu)

def show_device_context_menu(self, pos):
    """Show context menu for device operations."""
    index = self.device_table.indexAt(pos)
    if not index.isValid():
        return
    
    serial = self.device_table.item(index.row(), 1).text()
    
    menu = QMenu()
    
    action_reboot = menu.addAction("Reboot to System")
    action_reboot.triggered.connect(lambda: self.reboot_device_to_system(serial))
    
    action_fastboot = menu.addAction("Reboot to Bootloader")
    action_fastboot.triggered.connect(lambda: self.reboot_device_to_bootloader(serial))
    
    menu.exec(self.device_table.mapToGlobal(pos))

def reboot_device_to_system(self, serial):
    """Reboot specific device."""
    self.log(f"⏳ Rebooting {serial}...")
    success, output = self.device_manager.reboot_system(serial)
    if success:
        self.log(f"✓ {serial} rebooting")
    else:
        self.log(f"✗ Failed: {output}")
```

## 5. Testing Your Customizations

### Test with One Device
```bash
# 1. Connect single test device
# 2. Run GUI
python main_gui.py

# 3. Click button and verify behavior
# 4. Check log for errors
```

### Test with Multiple Devices
```bash
# 1. Connect 2-3 test devices
# 2. Select all devices
# 3. Click button and verify batch operation
# 4. Check each device's log output
```

### Debug Helper
Add this to any method to get detailed info:
```python
self.log(f"DEBUG: Device state = {self.device_manager.get_device_state(serial)}")
self.log(f"DEBUG: Selected devices = {self.selected_devices}")
self.log(f"DEBUG: Files exist = {os.path.exists(self.device_manager.get_file_path('software.zip'))}")
```

## Common Patterns

### Pattern 1: Run Command on Device
```python
success, output = self.device_manager.run_command(
    f"{self.device_manager.adb} shell your_command",
    serial
)
```

### Pattern 2: Check Device State
```python
state = self.device_manager.get_device_state(serial)
if state == "ADB":
    # Device is in ADB mode
    pass
elif state == "Fastboot":
    # Device is in bootloader
    pass
```

### Pattern 3: Log and Continue
```python
for serial in self.selected_devices:
    try:
        # Your operation
        pass
    except Exception as e:
        self.log(f"✗ {serial}: {e}")
        continue  # Skip to next device
```

## Full Customization Example

Here's a complete example you can paste to replace `on_manual_install()`:

```python
def on_manual_install(self):
    """Complete ROM installation workflow."""
    if not self.selected_devices:
        QMessageBox.warning(self, "No Device", "Please select at least one device")
        return
    
    import time
    
    self.log("=" * 50)
    self.log(f"Starting installation on {len(self.selected_devices)} device(s)")
    self.log("=" * 50)
    
    for serial in self.selected_devices:
        self.log(f"\n[DEVICE: {serial}]")
        
        try:
            # Check device state
            state = self.device_manager.get_device_state(serial)
            self.log(f"Current state: {state}")
            
            # Download files if needed
            if not os.path.exists(self.device_manager.get_file_path("software.zip")):
                self.log("ROM files not found, downloading...")
                # Run update first
                self.on_update_files()
            
            # Proceed with installation
            self.log("Starting ROM installation...")
            
            # ... Add your steps here ...
            
            self.log(f"✓ {serial}: Installation complete!")
        
        except Exception as e:
            self.log(f"✗ {serial}: {type(e).__name__}: {e}")
    
    self.log("\n" + "=" * 50)
    self.log("Installation batch completed")
    self.log("=" * 50)
```

---

**Remember**: The GUI framework handles multi-device coordination. You just need to implement the per-device logic, and the GUI will handle running it on all selected devices!

Good luck! 🚀
