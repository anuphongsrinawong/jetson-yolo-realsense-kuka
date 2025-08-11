## Usage Guide

### Quick run
```bash
cd /home/god/jetson-yolo-realsense-kuka
source .venv/bin/activate
bash scripts/download_model.sh  # one-time
bash scripts/run.sh
```

### Configuration
Edit `config/config.yaml` to adjust:
- `model.path`: `.pt` model path
- `runtime.device`: `auto`, `cpu`, or CUDA index like `0`
- `runtime.half`: use FP16 on CUDA
- `camera`: color/depth resolution and FPS
- `output.udp`/`output.tcp`/`output.eki`: enable and set host/port
- `calibration.T_cam_to_robot`: 4x4 transform camera→robot (homogeneous)

### Headless mode
If no DISPLAY is detected, preview window is disabled automatically. Logs go to stdout and optional file (see `logging.file`).

### UDP/TCP/EKI outputs
- UDP JSON: set `output.udp.enabled: true` and target `host`/`port`
- TCP JSON: set `output.tcp.enabled: true` and configure `host`/`port`
- KUKA EKI XML: set `output.eki.enabled: true` and match XML schema in `src/output/eki_sender.py`

### Coordinate frames
If `output.udp.send_depth_xyz: true`, each detection may include `xyz` (camera frame meters). If `calibration.T_cam_to_robot` provided, `xyz_robot` is also included.

### Run as a service
```bash
sudo cp systemd/jetson-yolo-realsense-kuka.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now jetson-yolo-realsense-kuka
sudo systemctl status jetson-yolo-realsense-kuka
```


