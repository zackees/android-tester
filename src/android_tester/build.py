import os

from android_tester.common import exec_cmd
from android_tester.env import PROJECT_ROOT


def main():
    os.chdir(PROJECT_ROOT)
    exec_cmd("gradle assembleDebugUnitTest")
    exec_cmd("gradle assembleDebug")


if __name__ == "__main__":
    main()
