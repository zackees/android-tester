"""
Main entry point.
"""

import argparse
import sys

from android_tester.android_tests import main


def this_main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser()
    _ = parser.parse_args()
    return main()


if __name__ == "__main__":
    sys.exit(this_main())
