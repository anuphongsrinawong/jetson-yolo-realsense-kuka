#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="/home/god/jetson-yolo-realsense-kuka"
MODEL_DIR="$PROJECT_ROOT/models"
MODEL_PATH="$MODEL_DIR/yolov8n.pt"

mkdir -p "$MODEL_DIR"

if [ ! -f "$MODEL_PATH" ]; then
  echo "Downloading YOLOv8n weights..."
  wget -O "$MODEL_PATH" https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt
else
  echo "Model already exists at $MODEL_PATH"
fi

echo "Model ready: $MODEL_PATH"


