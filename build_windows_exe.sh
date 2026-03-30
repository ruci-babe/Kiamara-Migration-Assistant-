#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

if ! command -v pyinstaller >/dev/null 2>&1; then
  echo "PyInstaller is not installed."
  echo "Install it with: python3 -m pip install pyinstaller"
  echo "Or run this helper from a Windows environment where PyInstaller is available."
  exit 1
fi

EXE_NAME="Kiamara"
DIST_DIR="dist/windows"
BUILD_DIR="build"

rm -rf "$DIST_DIR" "$BUILD_DIR"
mkdir -p "$DIST_DIR" "$BUILD_DIR"

if command -v wine >/dev/null 2>&1; then
  echo "Wine is installed. Attempting Windows executable build via PyInstaller."
  WINEPATH=$(which wine)
  pyinstaller --onefile --name "$EXE_NAME" --distpath "$DIST_DIR" --workpath "$BUILD_DIR" --specpath "$BUILD_DIR" migrate.py
else
  echo "Wine is not installed."
  echo "This script can still run on Windows directly, or you can install Wine to try cross-building from Linux."
  pyinstaller --onefile --name "$EXE_NAME" --distpath "$DIST_DIR" --workpath "$BUILD_DIR" --specpath "$BUILD_DIR" migrate.py
fi

echo "Build complete. Check $DIST_DIR/$EXE_NAME.exe or the generated output for your platform."
