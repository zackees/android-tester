"""
Common functions shared between scripts. Linted.
"""

# flake8: noqa: E501


import sys
from dataclasses import dataclass
from subprocess import call, check_output
from typing import Optional

from android_tester.env import PROJECT_ROOT


def uninstall_apk(
    package_name: str, device_serial: str, ignore_errors: bool = False
) -> None:
    """Uninstalls the apk"""
    exec_cmd(
        f"adb -s {device_serial} uninstall {package_name}",
        ignore_errors=ignore_errors,
        timeout=60,
    )


@dataclass
class Device:
    """Device representing an avd device"""

    name: str
    online: str
    serial: str
    emulator: bool
    product: str
    model: str
    device: str
    transport_id: str

    def list_packages(self, match_str: Optional[str] = None) -> list[str]:
        """Lists the packages on the device"""
        cmd = f"adb -s {self.serial} shell pm list packages"
        print(f"Running: {cmd}")
        try:
            packages = check_output(cmd, universal_newlines=True, shell=True).strip()
            package_list = packages.splitlines()

            def remove_package_prefix(val):
                if val.startswith("package:"):
                    return val[8:]
                return val

            package_list = [remove_package_prefix(package) for package in package_list]
            if match_str:
                package_list = [
                    package for package in package_list if match_str in package
                ]
            return package_list
        except Exception as exc:
            print(f"Error listing packages: {exc}")
            return []

    def uninstall(self, package_name: str, ignore_errors: bool = False) -> None:
        """Uninstalls the apk"""
        exec_cmd(
            f"adb -s {self.serial} uninstall {package_name}",
            ignore_errors=ignore_errors,
            timeout=60,
        )


def exec_cmd(
    cmd: str,
    cwd: Optional[str] = None,
    ignore_errors=False,
    timeout: Optional[float] = None,
    env=None,
) -> int:
    """Executes a command"""
    cwd = cwd or PROJECT_ROOT or None
    print(f"Executing:\n  {cmd}\n  with cwd={cwd}")
    rtn = call(cmd, cwd=cwd, shell=True, timeout=timeout, env=env)
    if ignore_errors:
        return rtn
    if rtn != 0:
        print(f"Error executing command: {cmd}")
        sys.exit(rtn)
    return rtn


def get_emulator_name(serial_no: str) -> Optional[str]:
    cmd = f"adb -s {serial_no} shell getprop ro.boot.qemu.avd_name"
    print(f"Running: {cmd}")
    try:
        avd_name = check_output(cmd, universal_newlines=True, shell=True).strip()
        return avd_name
    except Exception:
        return None


def query_adb_devices() -> list[str]:
    """Query adb devices, remove the header and empty lines"""
    device_out = check_output("adb devices -l", universal_newlines=True, shell=True)
    lines = device_out.splitlines()[1:]
    lines = [line.strip() for line in lines]
    lines = [line for line in lines if "List of devices attached" not in line]
    lines = [line for line in lines if line]
    return lines


def query_emulator_kill(serial_no: str) -> None:
    """Query adb devices, remove the header and empty lines"""
    check_output(f"adb -s {serial_no} emu kill", universal_newlines=True, shell=True)


# def bringup_emulator() -> Optional[Popen]:
#     """Bring up an Android emulator"""
#     AVD_NAME = "test"  # replace this with your AVD name
#     try:
#         process = Popen(
#             ["emulator", "-avd", AVD_NAME, "-no-snapshot-load", "-no-snapshot-save"],
#             stdout=PIPE,
#             stderr=STDOUT,
#         )
#         return process
#     except Exception as e:
#         print(f"Error starting emulator: {e}")
#         return None


def get_all_emulators(api: Optional[int] = None) -> list[str]:
    data = check_output(
        "emulator -list-avds", universal_newlines=True, shell=True
    ).strip()
    lines = data.splitlines()
    if api is not None:
        lines = [line for line in lines if f"{api}" in line]
    return lines


def get_live_devices() -> list[Device]:
    """Get the active devices"""
    device_infos: list[str] = query_adb_devices()
    out: list[Device] = []
    for dinfo in device_infos:
        print(f"Device info: {dinfo}")
        parts = dinfo.split()
        print(f"Parts: {parts}")
        is_emulator = "emulator" in dinfo
        while len(parts) < 6:
            parts.append("")

        def val(part: str) -> str:
            if ":" in part:
                return part.split(":")[1]
            return part

        product = val(parts[2])
        model = val(parts[3])
        dev = val(parts[4])
        tid = val(parts[5])
        serial_no = parts[0]
        avd_name = get_emulator_name(serial_no) or "unknown"
        device = Device(
            name=avd_name,
            online=parts[1],
            serial=serial_no,
            emulator=is_emulator,
            product=product,
            model=model,
            device=dev,
            transport_id=tid,
        )
        out.append(device)
    return out


def shutdown_all_running_emulators():
    """Shut down all running emulators"""
    for device in get_live_devices():
        if device.emulator:
            try:
                print(f"Shutting down emulator: {device.name}")
                query_emulator_kill(device.serial)
            except Exception as e:
                print(f"Error shutting down emulator: {e}")


if __name__ == "__main__":
    print(get_all_emulators())
