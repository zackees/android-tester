"""
Main entry point.
"""

import argparse
import shutil
import sys

from android_tester.android_tests import main

if shutil.which("adb") is None:
    try:
        # Attempt to reload the environment.
        from setenvironment import reload_environment

        reload_environment()
        if shutil.which("adb") is None:
            raise RuntimeError("Android SDK not found.")
    except ImportError:
        pass


def this_main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser()
    _ = parser.parse_args()
    return main()


if __name__ == "__main__":
    sys.exit(this_main())
