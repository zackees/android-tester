"""
Installs the release APK on the emulator and launches it.
"""

# flake8: noqa: E501
# pylint: disable=wrong-import-position

import os
import sys

from android_tester.common import (
    APP_PACKAGE_NAME,
    PROJECT_ROOT,
    RELEASE_APK,
    Device,
    exec_cmd,
    get_live_devices,
)

os.chdir(PROJECT_ROOT)


def install_apk(apk: str, package_nam: str, device_serial: str) -> None:
    """Installs the apk"""
    exec_cmd(f"adb -s {device_serial} uninstall {package_nam}", ignore_errors=True)
    exec_cmd(f"adb -s {device_serial} install -r {apk}")
    # check that it's installed
    exec_cmd(
        f"adb -s {device_serial} shell pm list packages {package_nam}",
        ignore_errors=False,
    )


def start_app(package_name: str, device: Device) -> None:
    """Starts the app"""
    exec_cmd(
        f"adb -s {device.name} shell am force-stop {package_name}",
        ignore_errors=True,
    )
    exec_cmd(f"adb -s {device.serial} shell monkey -p {package_name} 1")


def main() -> int:
    """Main"""
    devices: list[Device] = get_live_devices()
    if len(devices) == 0:
        print("No emulators found, please launch one then try again.")
        return 1
    print("Emulators found:")
    for i, device in enumerate(devices):
        print(f"  {i}: {device.name} {device.serial}")
    if len(devices) > 1:
        which = int(input("Which emulator to launch on? "))
        if which < 0 or which >= len(devices):
            print("Invalid emulator index")
            return 1
    else:
        which = 0
    device = devices[which]
    # Launch emulator
    install_apk(RELEASE_APK, APP_PACKAGE_NAME, device.serial)
    # Launch emulator
    start_app(APP_PACKAGE_NAME, device)
    print("Done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
