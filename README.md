## Jetson YOLOv8 + RealSense D435i → KUKA (UDP)

Production-oriented pipeline for NVIDIA Jetson running Ubuntu 22.04 with GPU acceleration:
- RealSense D435i color + depth capture
- YOLOv8n detection on GPU (falls back to CPU)
- UDP JSON output for downstream KUKA integration
- TCP JSON and KUKA EKI (XML-over-TCP) output options
- Systemd service for autorestart on boot

### Hardware/OS assumptions
- Jetson with CUDA/cuDNN (JetPack 5.x, kernel 5.15-tegra)
- Ubuntu 22.04 64-bit
- Intel RealSense D435i (USB3)

### Project layout
```
src/
  camera/realsense_camera.py
  detector/yolo_detector.py
  output/udp_sender.py
  output/tcp_sender.py
  output/eki_sender.py
  utils/{logger.py,draw.py,geometry.py}
  main.py
config/config.yaml
scripts/{setup_jetson.sh,run.sh,download_model.sh}
systemd/jetson-yolo-realsense-kuka.service
```

### Quick start
1) One-time setup (creates venv, installs CUDA-enabled torch, OpenCV via apt, RealSense SDK, ultralytics, etc.)
```bash
bash scripts/setup_jetson.sh
```

2) Download model weights (default: YOLOv8n COCO)
```bash
bash scripts/download_model.sh
```

3) Run
```bash
bash scripts/run.sh
```

### Configure
Edit `config/config.yaml`:
- `model.path`: path to the `.pt` file
- `runtime.device`: `auto` (default), `0` for GPU, or `cpu`
- `camera`: color/depth resolutions and FPS
- `output.udp`: UDP JSON target host/port and payload options
- `output.tcp`: TCP JSON target host/port (optional)
- `output.eki`: KUKA EKI XML-over-TCP target and XML shaping options

### Documentation
- Build/Install: docs/INSTALL.md
- Usage: docs/USAGE.md
- Development: docs/DEVELOPMENT.md
- Troubleshooting: docs/TROUBLESHOOTING.md

### Systemd service (optional)
```
sudo cp systemd/jetson-yolo-realsense-kuka.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now jetson-yolo-realsense-kuka
```

### KUKA integration notes
- This app emits per-frame data via UDP JSON, TCP JSON, or EKI XML-over-TCP.
- For EKI, ensure the XML structure matches your controller's EKI config. Adjust tags or structure in `output/eki_sender.py` or via `config/config.yaml`.

### Troubleshooting
- If torch isn’t using GPU: check `nvidia-smi` availability (not always present on Jetson) and `python -c "import torch; print(torch.cuda.is_available())"`.
- If `pyrealsense2` is missing: re-run setup, or install librealsense from source matching your kernel.
- For OpenCV on Jetson, prefer `python3-opencv` via apt, not `opencv-python` wheels.


