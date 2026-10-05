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

case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*)
    pyinstaller --onefile --name "$EXE_NAME" --distpath "$DIST_DIR" --workpath "$BUILD_DIR" --specpath "$BUILD_DIR" migrate.py
    echo "Build complete. Check $DIST_DIR/$EXE_NAME.exe."
    ;;
  *)
    echo "This helper must run in Windows Git Bash. Use build_windows_exe.ps1 on Windows PowerShell."
    exit 1
    ;;
  esac
