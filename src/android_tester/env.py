import os

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(HERE))

APK_PATH = "app/build/outputs/apk/release/app-release.apk"
APP_PACKAGE_NAME = "org.internetwatchdogs.androidmonitor"
APP_PACKAGE_TEST_NAME = "org.internetwatchdogs.androidmonitor.test"
MAIN_ACTIVITY = "MainActivity"

RELEASE_APK = os.path.join(PROJECT_ROOT, "app", "release", "app-release.apk")
