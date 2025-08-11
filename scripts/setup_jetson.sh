#!/usr/bin/env bash
set -euo pipefail

# This script prepares a Jetson (Ubuntu 22.04) for YOLOv8 + RealSense + UDP output.
# - Installs system packages (OpenCV via apt, RealSense SDK, venv tools)
# - Creates Python venv and installs Python deps
# - Installs Jetson-compatible Torch if missing

PROJECT_ROOT="/home/god/jetson-yolo-realsense-kuka"
PYTHON_BIN="python3"
VENV_DIR="$PROJECT_ROOT/.venv"

echo "[1/5] Installing system packages..."
sudo apt-get update
sudo apt-get install -y \
  python3-venv python3-pip python3-dev \
  python3-opencv \
  libgl1-mesa-glx libglib2.0-0 \
  git curl wget unzip \
  cmake build-essential pkg-config

echo "[2/5] Installing Intel RealSense SDK (librealsense + pyrealsense2) via apt..."
# Modern apt repo add (signed-by)
if ! grep -R "librealsense" /etc/apt/sources.list /etc/apt/sources.list.d 2>/dev/null | grep -q apt-repo; then
  echo "Adding librealsense apt repository..."
  sudo mkdir -p /usr/share/keyrings
  curl -fsSL https://librealsense.intel.com/Debian/librealsense.pgp | sudo gpg --dearmor -o /usr/share/keyrings/librealsense-archive-keyring.gpg || true
  echo "deb [signed-by=/usr/share/keyrings/librealsense-archive-keyring.gpg] http://librealsense.intel.com/Debian/apt-repo $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/librealsense.list >/dev/null || true
  sudo apt-get update || true
fi
sudo apt-get install -y librealsense2-utils librealsense2-dev librealsense2-dkms || true
sudo apt-get install -y python3-pyrealsense2 || true

echo "[3/5] Creating Python venv (with system site-packages for pyrealsense2/opencv)..."
if [ ! -d "$VENV_DIR" ]; then
  $PYTHON_BIN -m venv --system-site-packages "$VENV_DIR"
else
  # If venv already exists and was created without system-site-packages, you may need to recreate it.
  echo "Venv exists at $VENV_DIR. If pyrealsense2 import fails, recreate venv with --system-site-packages."
fi
source "$VENV_DIR/bin/activate"
pip install --upgrade pip wheel setuptools

echo "[4/5] Installing Jetson-compatible Torch (if needed)..."
python - <<'PY'
import sys
try:
    import torch
    print("Torch already installed:", torch.__version__)
except Exception:
    print("Torch missing; please install Jetson-specific wheel manually.")
    print("See: https://forums.developer.nvidia.com/c/agx-autonomous-machines/jetson-ecosystem/70")
    sys.exit(0)
PY

echo "[5/5] Installing Python requirements..."
pip install -r "$PROJECT_ROOT/requirements.txt"

echo "[Post-check] Verifying pyrealsense2 availability..."
python - <<'PY'
try:
    import pyrealsense2  # type: ignore
    print("pyrealsense2 import OK")
except Exception as e:
    print("pyrealsense2 NOT available in venv. If installed via apt, recreate venv with --system-site-packages.")
    print("Error:", e)
PY

if ! python - <<'PY'
try:
    import pyrealsense2  # type: ignore
    print('OK')
    raise SystemExit(0)
except Exception:
    raise SystemExit(1)
PY
then
  echo "[Fallback] Building librealsense from source with Python bindings... (this may take a while)"
  sudo apt-get install -y libssl-dev libusb-1.0-0-dev pkg-config libgtk-3-dev libglfw3-dev libgl1-mesa-dev libglu1-mesa-dev
  rm -rf /tmp/librealsense
  git clone --depth=1 https://github.com/IntelRealSense/librealsense.git /tmp/librealsense
  cd /tmp/librealsense
  mkdir -p build && cd build
  cmake .. \
    -DBUILD_EXAMPLES=OFF \
    -DBUILD_GRAPHICAL_EXAMPLES=OFF \
    -DBUILD_WITH_CUDA=OFF \
    -DFORCE_RSUSB_BACKEND=ON \
    -DBUILD_PYTHON_BINDINGS=ON \
    -DPYTHON_EXECUTABLE="$VENV_DIR/bin/python"
  make -j"$(nproc)"
  sudo make install
  sudo ldconfig
  echo "[Fallback] Verifying pyrealsense2 after source build..."
  "$VENV_DIR/bin/python" - <<'PY'
try:
    import pyrealsense2  # type: ignore
    print("pyrealsense2 import OK (from source build)")
except Exception as e:
    print("pyrealsense2 still not importable:", e)
    raise SystemExit(1)
PY
fi

echo "Done. To run: source $VENV_DIR/bin/activate && python -m pip show torch && bash scripts/download_model.sh && bash scripts/run.sh"


