import os
import subprocess
import time


def execute_command(cmd) -> str:
    # return subprocess.check_output(cmd, shell=True).decode('utf-8').strip()
    # subprocess.run(cmd, shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return (
        subprocess.run(
            cmd, shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        .stdout.decode("utf-8")
        .strip()
    )


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def run() -> None:
    lines: list[str] = []
    lines.append("List of connected devices:")
    lines.append("---------------------------")
    devices_output = execute_command("adb devices")
    device_lines = devices_output.split("\n")[1:]  # Exclude the first line
    for line in device_lines:
        if (
            "device" in line and "devices" not in line
        ):  # Ensure we're not getting the header or any offline/unauthorized devices
            device = line.split()[0]
            model = execute_command(f"adb -s {device} shell getprop ro.product.model")
            lines.append(model)
    clear_screen()
    print("\n".join(lines))


def main():
    try:
        while True:
            run()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nExiting...")


if __name__ == "__main__":
    main()
