# flake8: noqa: E501

import os
import sys

from android_tester.common import PROJECT_ROOT

os.chdir(PROJECT_ROOT)

os.system("python -m pip install -U pip")
os.system("python -m pip install -U pyflutterinstall")
os.system("pyflutterinstall --skip-ant")

if sys.platform == "linux":
    os.system("sudo apt-get install -y ninja-build")

print(
    "Done installing dependencies. Try running test. "
    "You may need to restart your terminal command window."
)
