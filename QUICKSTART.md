# Quick Start Guide - ROM Installer GUI

## 30-Second Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the GUI
python main_gui.py

# 3. Connect your devices via USB
# 4. The GUI will auto-detect them!
```

## What You Get

| Feature | Description |
|---------|-------------|
| 🔍 **Auto Detection** | Devices appear automatically (every 2 sec) |
| ☑️ **Selective Control** | Check/uncheck devices to target them |
| 📱 **Multi-Device** | Control 1, 5, 10+ devices at once |
| 📊 **Status Tracking** | Real-time log of all operations |
| 🎯 **9 Action Buttons** | Complete installation workflow |
| 🔧 **Customizable** | Add your own installation logic |

## One-Device Flow

```
Connect Device (with USB Debug ON)
    ↓
Device appears in list
    ↓
Select it (checkbox)
    ↓
Click "Update Files" (if needed)
    ↓
Click "Reboot to Bootloader"
    ↓
Wait for fastboot mode, then "Flash Recovery"
    ↓
Manual: Hold Vol Up + Power on device when prompted
    ↓
Device boots to recovery, "Sideload Software"
    ↓
Device installs ROM
    ↓
"Reboot to System" 
    ↓
Done! ✓
```

## Multi-Device Flow

```
Connect 5 devices
    ↓
All appear in list
    ↓
Select all 5 (checkboxes)
    ↓
"Update Files" → downloads once for all
    ↓
"Reboot to Bootloader" → all 5 reboot
    ↓
Wait ~30 sec, all should be in fastboot
    ↓
"Flash Recovery" → flashes all 5 in parallel
    ↓
Manually reboot each device into recovery by holding Vol Up + Power
    ↓
"Sideload Software" → installs ROM on all 5
    ↓
"Reboot to System" → all 5 reboot and finish
    ↓
Done! ✓ (time saved vs doing 1-by-1)
```

## Button Reference

| Button | Action | Device State Required |
|--------|--------|----------------------|
| 📥 Update Files | Download splash.img, recovery.img, software.zip | Any or None |
| 🔄 Reboot to Bootloader | Reboot to fastboot mode | ADB |
| ⚡ Flash Recovery | Flash recovery + splash images | Fastboot |
| ↩️ Reboot to Recovery | Reboot to recovery mode | ADB |
| 📦 Sideload Software | Install software.zip from recovery | Recovery + ADB Sideload |
| 🔌 Reboot to System | Normal reboot to system | Any |
| 🛠️ Manual Install Script | Custom installation (you implement) | Custom |
| 🔍 Refresh Devices | Force rescan for devices | N/A |
| 🗑️ Clear Downloads | Delete downloaded files | N/A |
| ⚠️ Reset All Devices | Emergency reboot all selected | Any |

## Tips & Tricks

### ✨ Pro Tip 1: Select by State
After detection, devices show their current state (ADB, Fastboot, Recovery). Select only devices in the state you need for the operation.

### ✨ Pro Tip 2: Check the Log
The status log at the bottom shows exactly what's happening on each device. Use it to debug issues.

### ✨ Pro Tip 3: Download First
Click "Update Files" once at the start. ROM files will be cached, making subsequent runs faster.

### ✨ Pro Tip 4: Batch Unrelated Devices
You can have devices at different stages and still batch operations. The app handles per-device state automatically.

## Common Issues

| Issue | Solution |
|-------|----------|
| **Devices not showing up** | Enable USB debugging on device, check cable connection, click Refresh |
| **"adb: command not found"** | Ensure apt/adb binary exists in the folder |
| **Files not found during flash** | Click "Update Files" first to download them |
| **Device stuck in fastboot** | Click "Reboot to System" to force normal reboot |

## Next Steps

1. **Read full docs** → See `GUI_README.md`
2. **Customize** → Edit `on_manual_install()` for your ROM
3. **Add buttons** → Copy button pattern to add more actions
4. **Test with 1 device** → Build confidence before mass deployment

Enjoy! 🚀
