#!/usr/bin/env python3
"""Custom ROM Multi-Device Installer GUI - Main Application."""
import sys
import os

# Bootstrap: Ensure directory structure exists
def bootstrap_directories():
    """Create required directories if they don't exist."""
    os.makedirs("core", exist_ok=True)
    os.makedirs("gui", exist_ok=True)
    os.makedirs("downloads", exist_ok=True)
    
    # Create __init__.py files
    for init_file in ["core/__init__.py", "gui/__init__.py"]:
        if not os.path.exists(init_file):
            with open(init_file, "w") as f:
                f.write(f'"""Package initialized."""\n')

bootstrap_directories()

# Now import PyQt6 and our modules
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QTextEdit, QCheckBox,
    QHeaderView, QSplitter, QLabel, QProgressBar, QMessageBox, QComboBox, QGroupBox,
    QDialog, QLineEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QColor, QFont, QIcon
import subprocess
import re
from typing import Dict, List, Tuple, Callable, Optional
import time


# Device Manager class
class DeviceManager:
    """Manages adb/fastboot operations."""
    
    def __init__(self, download_dir: str = "downloads"):
        self.adb = os.path.join("apt", "adb")
        self.fastboot = os.path.join("apt", "fastboot")
        self.download_dir = download_dir
        
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
    
    def run_command(self, cmd: str, device_serial=None) -> Tuple[bool, str]:
        """Run a command and return (success, output)."""
        try:
            if device_serial:
                device_serial = device_serial.strip()
            if device_serial and not cmd.startswith(self.fastboot) and " -s " not in cmd:
                if cmd.startswith(self.adb):
                    cmd = cmd.replace(self.adb, f"{self.adb} -s {device_serial}", 1)
                else:
                    cmd = f"{cmd} -s {device_serial}"
            
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            output = result.stdout + result.stderr
            success = result.returncode == 0
            return success, output
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            return False, str(e)

    def run_command_stream(
        self,
        cmd: str,
        device_serial=None,
        progress_callback: Optional[Callable[[int], None]] = None,
        line_parser: Optional[Callable[[str], Optional[int]]] = None,
    ) -> Tuple[bool, str]:
        """Run a command, streaming output; optionally report progress from lines."""
        try:
            if device_serial:
                device_serial = device_serial.strip()
            if device_serial and not cmd.startswith(self.fastboot) and " -s " not in cmd:
                if cmd.startswith(self.adb):
                    cmd = cmd.replace(self.adb, f"{self.adb} -s {device_serial}", 1)
                else:
                    cmd = f"{cmd} -s {device_serial}"

            proc = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            output_lines = []
            last_percent = -1

            while proc.stdout is not None:
                line = proc.stdout.readline()
                if line:
                    output_lines.append(line)
                    if line_parser and progress_callback:
                        percent = line_parser(line)
                        if percent is not None and percent != last_percent:
                            last_percent = percent
                            progress_callback(percent)
                elif proc.poll() is not None:
                    break

            if proc.stdout is not None:
                remaining = proc.stdout.read()
                if remaining:
                    output_lines.append(remaining)
                    if line_parser and progress_callback:
                        for rem_line in remaining.splitlines(keepends=True):
                            percent = line_parser(rem_line)
                            if percent is not None and percent != last_percent:
                                last_percent = percent
                                progress_callback(percent)

            output = "".join(output_lines)
            return proc.returncode == 0, output
        except Exception as e:
            return False, str(e)

    @staticmethod
    def _parse_sideload_percent(line: str) -> Optional[int]:
        match = re.search(r"\(~?(\d+)%\)", line)
        return int(match.group(1)) if match else None
    
    def get_adb_device_states(self) -> Dict[str, str]:
        """Get connected ADB devices and their states."""
        try:
            result = subprocess.check_output(f"{self.adb} devices", shell=True).decode()
            lines = result.strip().split("\n")[1:]
            devices = {}
            for l in lines:
                if not l.strip() or l.startswith("*"):
                    continue
                parts = l.split()
                if len(parts) >= 2 and parts[1].strip():
                    devices[parts[0]] = parts[1].strip()
            return devices
        except Exception:
            return {}

    def get_adb_devices(self) -> List[str]:
        """Get list of connected ADB devices."""
        return list(self.get_adb_device_states().keys())

    def get_fastboot_devices(self) -> List[str]:
        """Get list of devices in fastboot mode."""
        try:
            result = subprocess.check_output(f"{self.fastboot} devices", shell=True, timeout=5).decode()
            lines = result.strip().split("\n")
            devices = [l.split()[0] for l in lines if l.strip() and ("fastboot" in l or l[0] not in [" ", "*"])]
            return [d for d in devices if d]
        except subprocess.TimeoutExpired:
            return []
        except Exception:
            return []
    
    def get_device_name(self, device_serial: str) -> str:
        """Get device model name via adb shell getprop."""
        success, output = self.run_command(f'{self.adb} shell getprop ro.product.model', device_serial)
        if success:
            return output.strip()
        return "Unknown"
    
    def get_device_state(self, device_serial: str) -> str:
        """Determine device state: ADB, Fastboot, or Recovery."""
        adb_states = self.get_adb_device_states()
        fastboot_devices = self.get_fastboot_devices()
        
        if device_serial in fastboot_devices:
            return "Fastboot"
        elif device_serial in adb_states:
            status = adb_states[device_serial].lower()
            if status in ("unauthorized", "recovery"):
                return "Recovery"
            return "ADB"
        return "Offline"
    
    def reboot_bootloader(self, device_serial: str) -> Tuple[bool, str]:
        """Reboot device to bootloader."""
        return self.run_command(f"{self.adb} reboot bootloader", device_serial)
    
    def reboot_recovery(self, device_serial: str) -> Tuple[bool, str]:
        """Reboot device to recovery mode."""
        return self.run_command(f"{self.adb} reboot recovery", device_serial)

    def reboot_recovery(self, device_serial: str) -> Tuple[bool, str]:
        """Reboot device to recovery mode."""

        cmd1 = f'{self.fastboot} -s {device_serial} reboot recovery"'
        success, output = self.run_command(cmd1)
        if not success:
            return False, f"Failed to reboot recovery: {output}"
        
        cmd2 = f'{self.adb} wait-for-device'
        success, output = self.run_command(cmd2, device_serial)
        if not success:
            return False, f"Failed to reboot recovery: {output}"
        
        cmd3 = f'{self.adb} reboot recovery'
        success, output = self.run_command(cmd3, device_serial)
        return success, output



    def reboot_system(self, device_serial: str) -> Tuple[bool, str]:
        """Reboot device to system (fastboot)."""
        return self.run_command(f"{self.fastboot} -s {device_serial} reboot", None) 
    
    def fastboot_reboot_system(self, device_serial: str) -> Tuple[bool, str]:
        """Reboot device to system from fastboot mode."""
        return self.run_command(f"{self.fastboot} -s {device_serial} reboot", None)
    
    def flash_recovery(
        self,
        device_serial: str,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> Tuple[bool, str]:
        """Flash recovery and splash images."""
        recovery_path = os.path.join(self.download_dir, "recovery.img")
        splash_path = os.path.join(self.download_dir, "splash.img")
        
        if not os.path.exists(recovery_path) or not os.path.exists(splash_path):
            return False, "recovery.img or splash.img not found"

        if progress_callback:
            progress_callback(0)
        
        cmd1 = f'{self.fastboot} -s {device_serial} flash recovery "{recovery_path}"'
        success, output = self.run_command_stream(cmd1)
        if not success:
            return False, f"Failed to flash recovery: {output}"

        if progress_callback:
            progress_callback(50)
        
        cmd2 = f'{self.fastboot} -s {device_serial} flash splash "{splash_path}"'
        success, output2 = self.run_command_stream(cmd2)
        if success and progress_callback:
            progress_callback(100)
        return success, output + output2
    
    def sideload_software(
        self,
        device_serial: str,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> Tuple[bool, str]:
        """Sideload software.zip."""
        software_path = os.path.join(self.download_dir, "software.zip")
        
        if not os.path.exists(software_path):
            return False, "software.zip not found"

        if progress_callback:
            progress_callback(0)
        
        cmd = f'{self.adb} -s {device_serial} sideload "{software_path}"'
        return self.run_command_stream(
            cmd,
            progress_callback=progress_callback,
            line_parser=self._parse_sideload_percent,
        )


# Device Detector Thread
class DeviceDetectorThread(QThread):
    """Background thread for device detection."""
    
    devices_changed = pyqtSignal(dict)  # Emits {serial: (name, state)}
    
    def __init__(self, device_manager: DeviceManager):
        super().__init__()
        self.device_manager = device_manager
        self.running = True
        self.detected_devices = {}
    
    def run(self):
        """Continuously scan for devices."""
        while self.running:
            current_devices = {}
            
            # Scan ADB devices
            for serial in self.device_manager.get_adb_devices():
                name = self.device_manager.get_device_name(serial)
                state = "ADB"
                current_devices[serial] = (name, state)
            
            # Scan Fastboot devices
            for serial in self.device_manager.get_fastboot_devices():
                if serial not in current_devices:
                    current_devices[serial] = ("Unknown", "Fastboot")
            
            # Emit if changes detected
            if current_devices != self.detected_devices:
                self.detected_devices = current_devices
                self.devices_changed.emit(current_devices)
            
            time.sleep(2)  # Scan every 2 seconds
    
    def stop(self):
        """Stop the detector thread."""
        self.running = False
        self.wait()


class FlashRecoveryWorker(QThread):
    """Background thread for flashing recovery on one device."""

    progress = pyqtSignal(str, int)
    finished_op = pyqtSignal(str, bool, str)

    def __init__(self, device_manager: DeviceManager, serial: str):
        super().__init__()
        self.device_manager = device_manager
        self.serial = serial

    def run(self):
        def on_progress(percent: int):
            self.progress.emit(self.serial, percent)

        success, output = self.device_manager.flash_recovery(
            self.serial, progress_callback=on_progress
        )
        self.finished_op.emit(self.serial, success, output)


class SideloadWorker(QThread):
    """Background thread for sideloading software on one device."""

    progress = pyqtSignal(str, int)
    finished_op = pyqtSignal(str, bool, str)

    def __init__(self, device_manager: DeviceManager, serial: str):
        super().__init__()
        self.device_manager = device_manager
        self.serial = serial

    def run(self):
        def on_progress(percent: int):
            self.progress.emit(self.serial, percent)

        success, output = self.device_manager.sideload_software(
            self.serial, progress_callback=on_progress
        )
        self.finished_op.emit(self.serial, success, output)


# Command worker for streaming subprocess output
class CommandWorker(QThread):
    """Run a shell command in a background thread and stream stdout lines via signal."""
    output_line = pyqtSignal(str)
    finished = pyqtSignal(int)

    def __init__(self, command: str):
        super().__init__()
        self.command = command
        self._proc = None

    def run(self):
        try:
            # Start process and stream lines as they arrive
            self._proc = subprocess.Popen(
                self.command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            if self._proc.stdout is not None:
                for line in self._proc.stdout:
                    # Emit each line to be appended by the GUI
                    self.output_line.emit(line.rstrip("\n"))
            self._proc.wait()
            code = self._proc.returncode if self._proc.returncode is not None else -1
            self.finished.emit(code)
        except Exception as e:
            self.output_line.emit(f"❌ Error: {e}")
            self.finished.emit(-1)


# CLI Dialog
class CLIDialog(QDialog):
    """Dialog for executing custom CLI commands with adb/fastboot."""
    
    def __init__(self, parent=None, device_manager: DeviceManager = None):
        super().__init__(parent)
        self.device_manager = device_manager
        self.setWindowTitle("Custom CLI")
        self.setGeometry(200, 200, 900, 600)
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the CLI dialog interface."""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Custom CLI Commands")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Info text
        info = QLabel("Enter custom adb or fastboot commands. Use 'adb' or 'fastboot' keywords directly.")
        layout.addWidget(info)
        
        # Command input
        input_layout = QHBoxLayout()
        input_label = QLabel("Command:")
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("e.g., adb logcat | e.g., fastboot devices | e.g., adb shell pm list packages")
        self.command_input.returnPressed.connect(self.execute_command)
        input_layout.addWidget(input_label)
        input_layout.addWidget(self.command_input)
        layout.addLayout(input_layout)
        
        # Device selection
        device_layout = QHBoxLayout()
        device_label = QLabel("Device (optional for adb):")
        self.device_combo = QComboBox()
        self.device_combo.addItem("All/None")
        device_layout.addWidget(device_label)
        device_layout.addWidget(self.device_combo)
        layout.addLayout(device_layout)
        
        # Output area
        output_label = QLabel("Output:")
        layout.addWidget(output_label)
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setStyleSheet("background-color: #1e1e1e; color: #00ff00; font-family: Courier; font-size: 10px;")
        layout.addWidget(self.output_text)
        
        # Buttons layout
        button_layout = QHBoxLayout()
        
        self.execute_btn = QPushButton("Execute")
        self.execute_btn.clicked.connect(self.execute_command)
        button_layout.addWidget(self.execute_btn)
        
        self.clear_btn = QPushButton("Clear Output")
        self.clear_btn.clicked.connect(self.output_text.clear)
        button_layout.addWidget(self.clear_btn)
        
        button_layout.addStretch()
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        self.refresh_device_list()
    
    def refresh_device_list(self):
        """Refresh the device combo box."""
        if not self.device_manager:
            return
        
        current_text = self.device_combo.currentText()
        self.device_combo.clear()
        self.device_combo.addItem("All/None")
        
        devices = self.device_manager.get_adb_devices()
        for device in devices:
            device_name = self.device_manager.get_device_name(device)
            display_text = f"{device} ({device_name})"
            self.device_combo.addItem(display_text, device)
        
        # Restore previous selection
        idx = self.device_combo.findText(current_text)
        if idx >= 0:
            self.device_combo.setCurrentIndex(idx)
    
    def execute_command(self):
        """Execute the entered command asynchronously and stream output."""
        command = self.command_input.text().strip()
        if not command:
            self.output_text.append("⚠️ Please enter a command")
            return

        device_text = self.device_combo.currentData()

        self.output_text.append(f"\n$ {command}\n{'='*80}")

        # Replace keywords with full paths
        if command.startswith("adb "):
            command = command.replace("adb ", f"{self.device_manager.adb} ", 1)
            if device_text:
                command = command.replace(f"{self.device_manager.adb} ", f"{self.device_manager.adb} -s {device_text} ", 1)
        elif command.startswith("fastboot "):
            command = command.replace("fastboot ", f"{self.device_manager.fastboot} ", 1)
            if device_text:
                command = command.replace(f"{self.device_manager.fastboot} ", f"{self.device_manager.fastboot} -s {device_text} ", 1)

        # Prevent multiple concurrent executions
        if hasattr(self, 'cmd_worker') and getattr(self, 'cmd_worker') is not None:
            self.output_text.append("⚠️ A command is already running")
            return

        # Disable controls while running
        self.execute_btn.setEnabled(False)
        self.command_input.setEnabled(False)

        # Start background worker to stream output
        self.cmd_worker = CommandWorker(command)
        self.cmd_worker.output_line.connect(lambda line: self.output_text.append(line))
        self.cmd_worker.finished.connect(self._on_command_finished)
        self.cmd_worker.start()

    def _on_command_finished(self, code: int):
        if code == 0:
            self.output_text.append("✓ Command finished (exit code 0)")
        else:
            self.output_text.append(f"❌ Command finished (exit code {code})")
        self.output_text.append("="*80)
        # Re-enable controls
        self.execute_btn.setEnabled(True)
        self.command_input.setEnabled(True)
        # Scroll to bottom
        self.output_text.verticalScrollBar().setValue(self.output_text.verticalScrollBar().maximum())
        # Clear worker
        self.cmd_worker = None


# Main GUI Application
class ROMInstallerGUI(QMainWindow):
    """Main GUI window for multi-device ROM installer."""
    
    # Class-level signal definition
    log_signal = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Custom ROM Multi-Device Installer")
        self.setGeometry(100, 100, 1200, 800)
        
        self.device_manager = DeviceManager()
        self.selected_devices = set()
        self.device_progress = {}  # Track progress per device
        self._operation_workers: List[QThread] = []
        self._progress_log_last: Dict[str, int] = {}
        
        # Connect logging signal
        self.log_signal.connect(self.append_log)
        
        self.setup_ui()
        self.start_device_detector()
    
    def setup_ui(self):
        """Set up the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout()
        
        # Left panel: Device list
        left_layout = QVBoxLayout()
        left_label = QLabel("Connected Devices")
        left_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        left_label.mouseDoubleClickEvent = lambda event: self.toggle_cli_button()
        left_layout.addWidget(left_label)
        
        self.device_table = QTableWidget()
        self.device_table.setColumnCount(4)
        self.device_table.setHorizontalHeaderLabels(["Select", "Serial", "State", "Progress"])
        self.device_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.device_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.device_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.device_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.device_table.setMaximumWidth(600)
        
        left_layout.addWidget(self.device_table)
        
        # Right panel: Action buttons
        right_layout = QVBoxLayout()
        right_label = QLabel("Actions for Selected Devices")
        right_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        right_layout.addWidget(right_label)
        
        # Action buttons
        button_style = "padding: 8px; font-size: 11px; min-height: 30px; max-width: 220px;"
        
        self.btn_reboot_bootloader = QPushButton("🔄 Reboot to Bootloader")
        self.btn_reboot_bootloader.setStyleSheet(button_style)
        self.btn_reboot_bootloader.clicked.connect(self.on_reboot_bootloader)
        self.btn_reboot_bootloader.setMaximumWidth(220)
        right_layout.addWidget(self.btn_reboot_bootloader)
        
        self.btn_flash_recovery = QPushButton("⚡ Flash Recovery")
        self.btn_flash_recovery.setStyleSheet(button_style)
        self.btn_flash_recovery.clicked.connect(self.on_flash_recovery)
        right_layout.addWidget(self.btn_flash_recovery)
        
        self.btn_reboot_recovery = QPushButton("↩️ Reboot to Recovery")
        self.btn_reboot_recovery.setStyleSheet(button_style)
        self.btn_reboot_recovery.clicked.connect(self.on_reboot_recovery)
        right_layout.addWidget(self.btn_reboot_recovery)
        
        self.btn_sideload = QPushButton("📦 Sideload Software")
        self.btn_sideload.setStyleSheet(button_style)
        self.btn_sideload.clicked.connect(self.on_sideload)
        right_layout.addWidget(self.btn_sideload)
        
        #self.btn_reboot_system = QPushButton("🔌 Reboot to System")
        #self.btn_reboot_system.setStyleSheet(button_style)
        #self.btn_reboot_system.clicked.connect(self.on_reboot_system)
        #right_layout.addWidget(self.btn_reboot_system)
        
        #self.btn_manual_install = QPushButton("🛠️ Manual Install Script")
        #self.btn_manual_install.setStyleSheet(button_style)
        #self.btn_manual_install.clicked.connect(self.on_manual_install)
        #right_layout.addWidget(self.btn_manual_install)
        
        right_layout.addSpacing(20)
        
        self.btn_refresh = QPushButton("🔍 Refresh Devices")
        self.btn_refresh.setStyleSheet(button_style)
        self.btn_refresh.clicked.connect(self.on_refresh_devices)
        right_layout.addWidget(self.btn_refresh)
        
        #self.btn_clear_downloads = QPushButton("🗑️ Clear Downloads")
        #self.btn_clear_downloads.setStyleSheet(button_style)
        #self.btn_clear_downloads.clicked.connect(self.on_clear_downloads)
        #right_layout.addWidget(self.btn_clear_downloads)
        
        self.btn_update_files = QPushButton("📥 Update Files")
        self.btn_update_files.setStyleSheet(button_style)
        self.btn_update_files.clicked.connect(self.on_update_files)
        self.btn_update_files.setMaximumWidth(220)
        right_layout.addWidget(self.btn_update_files)
        
        # CLI button
        self.btn_cli = QPushButton("⚙️ Custom CLI")
        self.btn_cli.setStyleSheet(button_style)
        self.btn_cli.clicked.connect(self.on_open_cli)
        self.btn_cli.setMaximumWidth(220)
        right_layout.addWidget(self.btn_cli)
        
        right_layout.addStretch()
        
        # Bottom: Log viewer
        log_label = QLabel("Status Log")
        log_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        
        # Main layout assembly
        left_panel = QWidget()
        left_panel.setLayout(left_layout)
        
        right_panel = QWidget()
        right_panel.setLayout(right_layout)
        right_panel.setMaximumWidth(240)
        
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel)
        
        # Add bottom log to main layout
        bottom_layout = QVBoxLayout()
        bottom_layout.addWidget(log_label)
        bottom_layout.addWidget(self.log_text)
        
        full_layout = QVBoxLayout(central_widget)
        full_layout.addLayout(main_layout, 1)
        full_layout.addLayout(bottom_layout, 0)
    
    def start_device_detector(self):
        """Start the background device detector thread."""
        self.detector_thread = DeviceDetectorThread(self.device_manager)
        self.detector_thread.devices_changed.connect(self.update_device_table)
        self.detector_thread.start()
    
    def update_device_table(self, devices: Dict[str, Tuple[str, str]]):
        """Update device table with current devices."""
        current_serials = set(devices.keys())
        table_serials = set()
        
        # Collect existing serials
        for row in range(self.device_table.rowCount()):
            item = self.device_table.item(row, 1)
            if item:
                table_serials.add(item.text())
        
        # Remove rows for disconnected devices
        for row in range(self.device_table.rowCount() - 1, -1, -1):
            item = self.device_table.item(row, 1)
            if item:
                serial = item.text()
                if serial not in current_serials:
                    self.device_table.removeRow(row)
                    if serial in self.selected_devices:
                        self.selected_devices.discard(serial)
                    self.device_progress.pop(serial, None)
                    self._progress_log_last.pop(serial, None)
        
        # Add or update rows for current devices
        for serial, (_, state) in devices.items():
            found = False
            for row in range(self.device_table.rowCount()):
                item = self.device_table.item(row, 1)
                if item and item.text() == serial:
                    found = True
                    self.device_table.item(row, 2).setText(state)
                    break
            
            if not found:
                row = self.device_table.rowCount()
                self.device_table.insertRow(row)
                
                # Checkbox
                checkbox = QCheckBox()
                checkbox.stateChanged.connect(lambda state, s=serial: self.on_device_selected(s, state))
                self.device_table.setCellWidget(row, 0, checkbox)
                
                # Serial
                serial_item = QTableWidgetItem(serial)
                serial_item.setFlags(serial_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.device_table.setItem(row, 1, serial_item)
                
                # State
                state_item = QTableWidgetItem(state)
                state_item.setFlags(state_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.device_table.setItem(row, 2, state_item)
                
                # Progress bar
                progress_bar = QProgressBar()
                progress_bar.setValue(0)
                self.device_table.setCellWidget(row, 3, progress_bar)
                self.device_progress[serial] = progress_bar
    
    def on_device_selected(self, serial: str, state: int):
        """Handle device selection."""
        if state == Qt.CheckState.Checked.value:
            self.selected_devices.add(serial)
            self.log(f"✓ Selected device: {serial}")
        else:
            self.selected_devices.discard(serial)
            self.log(f"✗ Deselected device: {serial}")

    def set_device_progress(self, serial: str, percent: int, log_label: str = ""):
        """Update per-device progress bar and optionally log percent changes."""
        bar = self.device_progress.get(serial)
        if bar:
            bar.setValue(min(100, max(0, percent)))
        if log_label:
            last = self._progress_log_last.get(serial, -1)
            if percent != last:
                self._progress_log_last[serial] = percent
                self.log(f"  {serial} ({log_label}): {percent}%")

    def _track_worker(self, worker: QThread):
        self._operation_workers.append(worker)
        worker.finished.connect(lambda: self._operation_workers.remove(worker) if worker in self._operation_workers else None)

    def on_update_files(self):
        """Download update files."""
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
                last_percent = -1
                filepath = os.path.join("downloads", filename)
                
                with open(filepath, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0:
                                percent = (downloaded * 100) // total_size
                                if percent != last_percent:
                                    last_percent = percent
                                    self.log(f"  {filename}: {percent}%")
                                    QApplication.processEvents()
                self.log(f"✓ Downloaded {filename}")
            except Exception as e:
                self.log(f"✗ Failed to download {filename}: {e}")

    def on_reboot_bootloader(self):
        """Reboot selected devices to bootloader."""
        if not self.selected_devices:
            QMessageBox.warning(self, "No Device", "Please select at least one device")
            return
        
        for serial in self.selected_devices:
            adb_states = self.device_manager.get_adb_device_states()
            if serial not in adb_states:
                self.log(f"✗ Device {serial} is not connected (offline)")
                continue
            self.log(f"⏳ Rebooting {serial} to bootloader...")
            success, output = self.device_manager.reboot_bootloader(serial)
            if success:
                self.log(f"✓ {serial} rebooting to bootloader")
            else:
                self.log(f"✗ Failed to reboot {serial}: {output}")

    def on_flash_recovery(self):
        """Flash recovery on selected devices."""
        if not self.selected_devices:
            QMessageBox.warning(self, "No Device", "Please select at least one device")
            return
        
        for serial in self.selected_devices:
            self._progress_log_last[serial] = -1
            self.set_device_progress(serial, 0)
            self.log(f"⏳ Flashing recovery on {serial}...")
            worker = FlashRecoveryWorker(self.device_manager, serial)
            worker.progress.connect(
                lambda percent, s=serial: self.set_device_progress(s, percent, "flash")
            )
            worker.finished_op.connect(self._on_flash_recovery_finished)
            self._track_worker(worker)
            worker.start()

    def _on_flash_recovery_finished(self, serial: str, success: bool, output: str):
        if success:
            self.set_device_progress(serial, 100)
            self.log(f"✓ {serial} recovery flashed successfully")
        else:
            self.set_device_progress(serial, 0)
            self.log(f"✗ Failed to flash {serial}: {output}")

    def on_reboot_recovery(self):
        """Reboot selected devices to recovery."""
        if not self.selected_devices:
            QMessageBox.warning(self, "No Device", "Please select at least one device")
            return
        
        for serial in self.selected_devices:
            self.log(f"⏳ Rebooting {serial} to recovery...")
            success, output = self.device_manager.reboot_recovery(serial)
            if success:
                self.log(f"✓ {serial} rebooting to recovery")
            else:
                self.log(f"✗ Failed to reboot {serial}: {output}")

    def on_sideload(self):
        """Sideload software on selected devices."""
        if not self.selected_devices:
            QMessageBox.warning(self, "No Device", "Please select at least one device")
            return
        QMessageBox.warning(self, "Please confirm", "I have factory reset the device and I have selected 'Apply from ADB' on each device")
        adb_states = self.device_manager.get_adb_device_states()
        for serial in self.selected_devices:
            if serial not in adb_states:
                self.log(f"✗ Device {serial} is not connected (offline)")
                continue
            self._progress_log_last[serial] = -1
            self.set_device_progress(serial, 0)
            self.log(f"⏳ Sideloading software to {serial}...")
            worker = SideloadWorker(self.device_manager, serial)
            worker.progress.connect(
                lambda percent, s=serial: self.set_device_progress(s, percent, "sideload")
            )
            worker.finished_op.connect(self._on_sideload_finished)
            self._track_worker(worker)
            worker.start()

    def _on_sideload_finished(self, serial: str, success: bool, output: str):
        if success:
            self.set_device_progress(serial, 100)
            self.log(f"✓ {serial} sideload completed")
        else:
            self.set_device_progress(serial, 0)
            self.log(f"✗ Failed to sideload to {serial}: {output}")

    def on_reboot_system(self):
        """Reboot selected devices to system (fastboot)."""
        if not self.selected_devices:
            QMessageBox.warning(self, "No Device", "Please select at least one device")
            return
        
        for serial in self.selected_devices:
            self.log(f"⏳ Rebooting {serial} to system...")
            success, output = self.device_manager.fastboot_reboot_system(serial)
            if success:
                self.log(f"✓ {serial} rebooting to system")
            else:
                self.log(f"✗ Failed to reboot {serial}: {output}")

    def on_manual_install(self):
        """Run manual install script on selected devices."""
        if not self.selected_devices:
            QMessageBox.warning(self, "No Device", "Please select at least one device")
            return
        
        self.log("⏳ Manual install not yet implemented - customize this function")
        QMessageBox.information(self, "Manual Install", "Customize on_manual_install() to add your installation logic")

    def on_refresh_devices(self):
        """Force refresh device list."""
        self.log("🔍 Refreshing device list...")
    
    def on_update_files(self):
        """Update/download files (placeholder for custom implementation)."""
        self.log("📥 Update files functionality can be customized here")
        QMessageBox.information(self, "Update Files", "Customize on_update_files() to add your file download/update logic")

    def on_clear_downloads(self):
        """Clear downloaded files."""
        self.log("🗑️ Clearing downloads...")
        import shutil
        try:
            if os.path.exists("downloads"):
                for file in os.listdir("downloads"):
                    file_path = os.path.join("downloads", file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        self.log(f"Deleted: {file}")
            self.log("✓ Downloads cleared")
        except Exception as e:
            self.log(f"✗ Error clearing downloads: {e}")

    def log(self, message: str):
        """Add message to log."""
        self.log_text.append(message)
        # Auto-scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def append_log(self, message: str):
        """Append to log (signal handler)."""
        self.log(message)

    def toggle_cli_button(self):
       """Toggle CLI button visibility (double-click on title)."""
       self.btn_cli.setVisible(not self.btn_cli.isVisible())
    
    def on_open_cli(self):
       """Open the custom CLI dialog."""
       cli_dialog = CLIDialog(self, self.device_manager)
       cli_dialog.exec()

    def closeEvent(self, event):
        """Handle window close event."""
        self.detector_thread.stop()
        for worker in list(self._operation_workers):
            worker.wait(5000)
        event.accept()


def main():
    """Run the application."""
    app = QApplication(sys.argv)
    window = ROMInstallerGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
