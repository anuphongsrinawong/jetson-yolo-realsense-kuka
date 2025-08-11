#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="/home/god/jetson-yolo-realsense-kuka"
UNIT_NAME="jetson-yolo-autopush.service"

echo "Installing inotify-tools..."
sudo apt-get update -y
sudo apt-get install -y inotify-tools

echo "Creating user systemd unit..."
mkdir -p "$HOME/.config/systemd/user"
cat > "$HOME/.config/systemd/user/$UNIT_NAME" << 'UNIT'
[Unit]
Description=Auto-commit and push on file changes (inotify)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/bin/bash -lc '/home/god/jetson-yolo-realsense-kuka/scripts/auto_push.sh'
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
UNIT

echo "Enabling user service..."
systemctl --user daemon-reload
systemctl --user enable --now "$UNIT_NAME"

echo "Done. Configure your Git remote if not set:"
echo "  cd $REPO_DIR && git remote add origin <git@github.com:USER/REPO.git> && git push -u origin main"


