## Installation and Build Guide

This project targets NVIDIA Jetson (Ubuntu 22.04, JetPack r36.x) with Intel RealSense D435i. It also runs on generic x86_64 Linux (CPU-only).

### 1) System prerequisites (Jetson)
- JetPack 6.x (R36.x) with CUDA/cuDNN/TensorRT installed
- Ubuntu 22.04 64-bit
- RealSense D435i (USB3)

Install base packages:
```bash
sudo apt-get update
sudo apt-get install -y \
  python3-venv python3-pip python3-dev \
  python3-opencv libgl1-mesa-glx libglib2.0-0 \
  cmake build-essential pkg-config git curl wget unzip
```

### 2) Project setup
```bash
cd /home/god
git clone https://github.com/anuphongsrinawong/jetson-yolo-realsense-kuka.git
cd jetson-yolo-realsense-kuka
bash scripts/setup_jetson.sh
bash scripts/download_model.sh
```

This creates a Python venv at `.venv`, installs dependencies, RealSense SDK (if available via apt), and downloads YOLOv8n weights.

### 3) RealSense SDK (fallback from source)
If `python3-pyrealsense2` isn’t available via apt, the setup script can build from source. You can also run the build manually:
```bash
sudo apt-get install -y libssl-dev libusb-1.0-0-dev pkg-config libgtk-3-dev libglfw3-dev libgl1-mesa-dev libglu1-mesa-dev
git clone --depth=1 https://github.com/IntelRealSense/librealsense.git /tmp/librealsense
cd /tmp/librealsense && mkdir -p build && cd build
cmake .. -DBUILD_EXAMPLES=OFF -DBUILD_GRAPHICAL_EXAMPLES=OFF -DBUILD_WITH_CUDA=OFF -DFORCE_RSUSB_BACKEND=ON -DBUILD_PYTHON_BINDINGS=ON -DPYTHON_EXECUTABLE=/home/god/jetson-yolo-realsense-kuka/.venv/bin/python
make -j$(nproc)
sudo make install && sudo ldconfig
```

Install udev rules (for non-root access):
```bash
bash scripts/install_realsense_udev.sh
```

### 4) GPU PyTorch on Jetson (JetPack r36.x)
Install Jetson-compatible torch/vision from NVIDIA Jetson AI Lab index (example for JP 6.2, CUDA 12.6):
```bash
source .venv/bin/activate
pip install --upgrade pip
pip install torch torchvision torchaudio --index-url https://pypi.jetson-ai-lab.io/jp6/cu126
python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
```
If connectivity to that index is blocked, download wheel files on another host and copy them over, then install via `pip install /path/to/whl`.

### 5) Verify camera
```bash
rs-enumerate-devices
```
You should see D435 device details and modes.

### 6) Run
```bash
bash scripts/run.sh
```

### 7) Optional: systemd service
```bash
sudo cp systemd/jetson-yolo-realsense-kuka.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now jetson-yolo-realsense-kuka
```


