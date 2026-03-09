import subprocess
import sys
import os
import requests
import time

def remove_old_file(filename):
    path = os.path.join(DOWNLOAD_DIR, filename)
    if os.path.exists(path):
        print(f"Removing old file: {filename}")
        os.remove(path)

def download_file(filename, url):
    path = os.path.join(DOWNLOAD_DIR, filename)

    print(f"Downloading {filename}...")
    response = requests.get(url, stream=True)
    response.raise_for_status()

    total_size = int(response.headers.get('content-length', 0))
    downloaded = 0

    with open(path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)

                if total_size > 0:
                    percent = downloaded * 100 // total_size
                    print(f"\r{percent}% downloaded", end="")

    print(f"\nFinished downloading {filename}")

def update_files():
    for filename, url in files.items():
        remove_old_file(filename)
        download_file(filename, url)


def run(cmd):
    print(f"\n> {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print("Command failed!")
        sys.exit(1)

def check_adb():
    print("Checking for connected device...")
    try:
        result = subprocess.check_output(f"{ADB} devices", shell=True).decode()
    except subprocess.CalledProcessError as e:
        raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))
    lines = result.strip().split("\n")[1:]
    devices = [l for l in lines if "device" in l]

    if not devices:
        print("No device detected.")
        sys.exit(1)

    print("Device detected:", devices[0])

def reboot_bootloader():
    run(f"{ADB} reboot bootloader")

def check_fastboot():
    result = subprocess.check_output(f"{FASTBOOT} devices", shell=True).decode()

    if not result.strip():
        print("No fastboot device detected.")
        sys.exit(1)

    print("Fastboot device detected.")

def flash_recovery():
    try:
        run(f"{FASTBOOT} flash recovery {DOWNLOADS}/recovery.img")
        run(f"{FASTBOOT} flash splash {DOWNLOADS}/splash.img")
    except:
        sys.exit(1)


files = {
    "splash.img": "https://updates.simplephone.nl/builds/parts/splash.img",
    "recovery.img": "https://updates.simplephone.nl/builds/parts/recovery.img",
    "software.zip": "https://updates.simplephone.nl/builds/parts/software.zip",
    "addons.zip": "https://updates.simplephone.nl/builds/parts/addons.zip"
}

ADB = os.path.join("apt", "adb")
FASTBOOT = os.path.join("apt", "fastboot")
DOWNLOAD_DIR = "downloads"
DOWNLOADS = os.path.join("downloads")

if(input("Is this your first time running this software, or has it been a while since the last time? Please enter Y in order to update the files (Y/N) "))=="Y":
    update_files()
else:
    print("Did not detect Y, so not updating / downloading files")

check_adb()
reboot_bootloader()
# Sleeping 30 seconds to allow the device to boot into fastboot before checking
print("Waiting for the device to boot into fastboot")
time.sleep(30)
check_fastboot()
flash_recovery()

if(input("Please now hold the volume up button (the one far away from the power button) and the power button until the boot logo appears, press enter when you are done ")):
    print("You should now be in a recovery menu")
