## Development Guide

### Code structure
- `src/camera/realsense_camera.py`: RealSense capture, depth→XYZ
- `src/detector/yolo_detector.py`: YOLOv8 detector (Ultralytics), GPU/FP16 if available
- `src/output/{udp_sender.py,tcp_sender.py,eki_sender.py}`: Outputs
- `src/utils/{logger.py,draw.py,geometry.py}`: Helpers
- `src/main.py`: Orchestration

### Environment
```bash
cd /home/god/jetson-yolo-realsense-kuka
python3 -m venv --system-site-packages .venv  # already created by setup script
source .venv/bin/activate
pip install -r requirements.txt
```

### Lint/test
You can add flake8/mypy/pytest as needed. For now, run the app and observe logs.

### Adding new outputs (e.g., MQTT)
Create a new module under `src/output/` with a class exposing `send(payload: dict) -> None` and wire it in `src/main.py` similarly to UDP/TCP/EKI.

### Calibration
Provide `calibration.T_cam_to_robot` (4x4 homogeneous) in `config/config.yaml` to publish `xyz_robot` coordinates.

### Git auto-push
We run a user-level systemd service `jetson-yolo-autopush.service` that watches the repo and auto-commits/pushes. Configure your remote:
```bash
git remote set-url origin <https://github.com/USER/REPO.git>
git push -u origin main
```


