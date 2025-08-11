#!/usr/bin/env bash
set -euo pipefail

echo "Installing RealSense udev rules..."
TMP_DIR="/tmp/librealsense"
RULES_SRC=""

if [ -f "$TMP_DIR/config/99-realsense-libusb.rules" ]; then
  RULES_SRC="$TMP_DIR/config/99-realsense-libusb.rules"
else
  mkdir -p "$TMP_DIR"
  echo "Fetching udev rules from upstream..."
  curl -fsSL -o "$TMP_DIR/99-realsense-libusb.rules" \
    https://raw.githubusercontent.com/IntelRealSense/librealsense/master/config/99-realsense-libusb.rules
  RULES_SRC="$TMP_DIR/99-realsense-libusb.rules"
fi

sudo cp "$RULES_SRC" /etc/udev/rules.d/99-realsense-libusb.rules
sudo udevadm control --reload-rules
sudo udevadm trigger

echo "Adding current user to plugdev and video groups (may require re-login)..."
sudo usermod -aG plugdev "$USER" || true
sudo usermod -aG video "$USER" || true

echo "Done. Please replug the RealSense device or reboot if not detected."


