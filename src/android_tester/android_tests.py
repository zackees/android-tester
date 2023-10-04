# pylint: disable=line-too-long
# ruff: noqa: E501
# flake8: noqa: E501

import argparse
import atexit
import os
import subprocess
import sys
import time
import warnings
from dataclasses import dataclass
from subprocess import PIPE, STDOUT, Popen
from typing import Optional

from android_tester.common import (
    APP_PACKAGE_NAME,
    APP_PACKAGE_TEST_NAME,
    PROJECT_ROOT,
    Device,
    exec_cmd,
    get_all_emulators,
    get_live_devices,
    shutdown_all_running_emulators,
)

os.environ["ANDROID_EMULATOR_WAIT_TIME_BEFORE_KILL"] = "0"


r"""
  /usr/bin/sh -c \sudo chown $USER:$USER /usr/local/lib/android/sdk -R
  /usr/bin/sh -c \yes | sdkmanager --licenses > /dev/null
  /usr/bin/sh -c \sdkmanager --install 'build-tools;33.0.2' platform-tools > /dev/null
  /usr/bin/sh -c \sdkmanager --install emulator --channel=0 > /dev/null
  /usr/bin/sh -c \sdkmanager --install 'system-images;android-30;android-tv;x86' --channel=0 > /dev/null
  /usr/bin/sh -c \echo no | avdmanager create avd --force -n test --abi 'android-tv/x86' --package 'system-images;android-30;android-tv;x86' --device 'Nexus 6'
  /usr/bin/sh -c \/usr/local/lib/android/sdk/emulator/emulator -avd test -no-window -gpu swiftshader_indirect -no-snapshot -noaudio -no-boot-anim -accel off &
  
  then in a loop:
   /usr/local/lib/android/sdk/platform-tools/adb shell getprop sys.boot_completed

  """


EMULATOR_TYPE = "system-images;android-30;google_apis_playstore;x86_64"  # "sdkmanager --list | grep system-images"
# LAUNCH_CMD = f"echo no | emulator -avd test -no-window -gpu swiftshader_indirect -no-snapshot -noaudio -no-boot-anim -accel off"
LAUNCH_CMD = "echo no | emulator -avd test -no-window -gpu swiftshader_indirect -no-snapshot -noaudio -no-boot-anim"


@dataclass
class RunningDevice:
    """Represents a fully booted emulator device ready for testing"""

    def __init__(self, device, process: subprocess.Popen):
        self.device = device
        self.process = process

    def __repr__(self):
        return f"RunningDevice(device={self.device}, process={self.process})"

    def kill(self):
        if self.process is not None:
            self.process.kill()
            self.process = None
            exec_cmd(f"adb -s {self.device.serial} emu kill")

            timeout = 60  # Timeout value in seconds
            elapsed_time = 0

            while self.is_emulator_running() and elapsed_time < timeout:
                print("Waiting for emulator to shut down...")
                time.sleep(1)
                elapsed_time += 1

            if elapsed_time >= timeout:
                print("Timeout reached, emulator may still be running.")
            else:
                print("Emulator is shut down")

    def is_emulator_running(self):
        result = os.system(f"adb -s {self.device.serial} shell true 2>/dev/null")
        return result == 0

    def wait_for_device_bootup(self, timeout=60) -> None:
        """Waits for the device to complete its booting process, or until timeout"""

        boot_completed = False
        timeout_time = time.time() + timeout
        while not boot_completed and time.time() < timeout_time:
            cmd = f"adb -s {self.device.serial} shell getprop sys.boot_completed"
            print(f"Running: {cmd}")
            completed_process: subprocess.CompletedProcess = subprocess.run(
                cmd,
                shell=True,
                timeout=60,
                universal_newlines=True,
                capture_output=True,
                check=False,
            )
            output = completed_process.stdout.strip()
            boot_completed = output == "1"

            if not boot_completed:
                print("Waiting for device to boot up...")
                time.sleep(0.5)  # wait for 1/2 a second before the next check

        if boot_completed:
            wait_time_after_boot = 5
            print(
                f"Device has booted up, waiting {wait_time_after_boot} seconds before allow commands to be sent."
            )
            time.sleep(wait_time_after_boot)
        else:
            print("Timeout reached, device may still be booting.")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.kill()

    @property
    def serial(self) -> str:
        return self.device.serial


def bringup_emulator(api: Optional[int] = None) -> RunningDevice:
    """Install emulator"""
    # exec_cmd('sudo chown $USER:$USER /usr/local/lib/android/sdk -R')
    exec_cmd("yes | sdkmanager --licenses")
    exec_cmd('sdkmanager --install "build-tools;33.0.2" platform-tools')
    exec_cmd("sdkmanager --install emulator --channel=0")
    exec_cmd(f'sdkmanager --install "{EMULATOR_TYPE}" --channel=0')

    # proc = subprocess.Popen(LAUNCH_CMD, shell=True, universal_newlines=True)
    # atexit.register(lambda: proc.kill())

    # exec_cmd('adb wait-for-device')

    def bringup(avd_name: str) -> Optional[Popen]:
        """Bring up an Android emulator"""
        try:
            # process = Popen(["emulator", "-avd", AVD_NAME, "-no-snapshot-load", "-no-snapshot-save"], stdout=PIPE, stderr=STDOUT)
            process = Popen(  # pylint: disable=consider-using-with
                [
                    "emulator",
                    "-avd",
                    avd_name,
                    "-no-snapshot-load",
                    "-no-snapshot-save",
                ],
                stdout=PIPE,
                stderr=STDOUT,
            )
            return process
        except Exception as e:
            print(f"Error starting emulator: {e}")
            return None

    def get_first_live_device() -> Optional[Device]:
        """Get the first live device"""
        for _ in range(20):
            for device in get_live_devices():
                print(device)
                if device.emulator:
                    return device
        return None

    found_device: Optional[Device] = get_first_live_device()

    if found_device is None:
        emulators = get_all_emulators(api=api)
        assert len(emulators) > 0
        print(f"Found {len(emulators)} emulators")
        emu = emulators[0]
        proc = bringup(emu)
        time.sleep(10)
        print(proc)
        timeout_time = time.time() + 60
        while time.time() < timeout_time:
            found_device = get_first_live_device()
            if found_device is not None:
                break
            time.sleep(1)

    assert found_device is not None
    serial = found_device.serial if found_device is not None else ""
    atexit.register(lambda: os.system(f"adb -s {serial} emu kill"))

    print("-------> Waiting for device....")
    result = subprocess.run(  # ruff: noqa: F841
        f"adb -s {found_device.serial} wait-for-device",
        shell=True,
        timeout=60,
        universal_newlines=True,
        check=False,
    )
    assert proc is not None
    running_device = RunningDevice(found_device, proc)
    atexit.register(running_device.kill)
    running_device.wait_for_device_bootup()
    if result.returncode != 0:
        warnings.warn(f"Error: {result.stderr}")
    return running_device


def create_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Android tests")
    parser.add_argument(
        "-a",
        "--api",
        help="API Level",
        type=int,
        default=33,
        choices=[28, 29, 30, 31, 32, 33],
    )
    return parser


def has_physical_device() -> bool:
    """Check if there is a physical device connected"""
    result = os.system("adb shell true 2>/dev/null")
    return result == 0


def get_physical_devices() -> list[Device]:
    """Get the list of physical devices"""
    devices = []
    for device in get_live_devices():
        if not device.emulator:
            devices.append(device)
    return devices


def run_connected_test(running_device: RunningDevice | Device) -> None:
    """Run connected tests"""
    # note that RunningDevice means we have a live emulator running.
    # 80 columns of #
    print()
    if isinstance(running_device, RunningDevice):
        print("#" * 80)
        # fill # around the text
        print(f'# Running on "{running_device.device.serial}"')
        print("#" * 80)
        print()
        install_packages = running_device.device.list_packages(APP_PACKAGE_NAME)
        for package in install_packages:
            running_device.device.uninstall(package)
    if isinstance(running_device, Device):
        print("#" * 80)
        # fill # around the text
        print(f'# Running on physical device "{running_device.model}"')
        print("#" * 80)
        print()
    # Really make sure our package is not installed
    # os.system(f'adb uninstall "{APP_PACKAGE_NAME}"')
    # os.system(f'adb uninstall "{APP_PACKAGE_NAME}.test"')
    # task = "connectedExtraActivitiesTestDebugAndroidTest"
    env = os.environ.copy()
    env["ANDROID_SERIAL"] = running_device.serial
    task = "connectedCheck"
    exec_cmd(f"gradle {task}", ignore_errors=True, cwd=PROJECT_ROOT, env=env)


def bringup_emulator_and_run(api: int) -> None:
    running_device: RunningDevice = bringup_emulator(api=api)
    with running_device:
        print("Listing all devices: emulator -list-avds")
        os.system("emulator -list-avds")
        run_connected_test(running_device)


def physical_device_run(device: Device) -> None:
    # remove previous tests
    device.uninstall(APP_PACKAGE_NAME, ignore_errors=True)
    device.uninstall(APP_PACKAGE_TEST_NAME, ignore_errors=True)
    run_connected_test(device)


def stay_awake(devices: list[Device]) -> None:
    """Stay awake"""
    for device in devices:
        cmd_stay_awake_while_plugged_in = f"adb -s {device.serial} shell settings put global stay_on_while_plugged_in 3"
        cmd_screen_timeout = f"adb -s {device.serial} shell settings put system screen_off_timeout 2147483647"
        cmd_disable_lockscreen = (
            f"adb -s {device.serial} shell settings put secure lockscreen.disabled 1"
        )
        for cmd in [
            cmd_stay_awake_while_plugged_in,
            cmd_screen_timeout,
            cmd_disable_lockscreen,
        ]:
            print(f"Running: {cmd}")
            completed_process: subprocess.CompletedProcess = subprocess.run(
                cmd,
                shell=True,
                timeout=60,
                universal_newlines=True,
                capture_output=True,
                check=False,
            )
            if 0 != completed_process.returncode:
                print(f"Error: {completed_process.stderr}")
            output = completed_process.stdout.strip()
            print(output)


def main() -> None:
    os.chdir(PROJECT_ROOT)
    args = create_argparser().parse_args()
    shutdown_all_running_emulators()
    physical_devices = get_physical_devices()
    if not physical_devices:
        print("No physical devices found, running on emulator")
        bringup_emulator_and_run(api=args.api)
    else:
        print("Physical devices found, running on physical device(s)")
        stay_awake(
            physical_devices,
        )
        for device in physical_devices:
            physical_device_run(device)


if __name__ == "__main__":
    try:
        start = time.time()
        main()
        end = time.time()
        print(f"Total time: {end - start:.2f} seconds")
    except KeyboardInterrupt:
        print("\nExiting...")
    sys.exit(0)
