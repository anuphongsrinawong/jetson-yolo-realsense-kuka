#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="/home/god/jetson-yolo-realsense-kuka"
VENV_DIR="$PROJECT_ROOT/.venv"

source "$VENV_DIR/bin/activate"
# Ensure system dist-packages are visible (for pyrealsense2/opencv on Jetson)
export PYTHONPATH="/usr/lib/python3/dist-packages:/usr/local/lib/python3.10/dist-packages:/usr/local/lib/python3/dist-packages:$PROJECT_ROOT/src:${PYTHONPATH:-}"

python "$PROJECT_ROOT/src/main.py" --config "$PROJECT_ROOT/config/config.yaml"


