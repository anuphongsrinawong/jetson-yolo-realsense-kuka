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

ภาพรวมโปรเจค
ระบบบน Jetson สำหรับจับภาพจาก Intel RealSense D435i (สี+ลึก), รัน YOLOv8 ตรวจวัตถุ (GPU ได้ ถ้าไม่มีจะตกลงไป CPU), แล้วส่งผลลัพธ์ออกทางเครือข่ายเพื่อเชื่อมต่อ KUKA
รองรับเอาต์พุต 3 แบบ: UDP JSON (หลัก), TCP JSON, และ KUKA EKI (XML-over-TCP)
มีสคริปต์ติดตั้ง, ดาวน์โหลดโมเดล, รัน และไฟล์ systemd เพื่อให้รันอัตโนมัติเมื่อบูต
โฟลว์การทำงาน
RealSense D435i → จับภาพสี/ลึก + intrinsics
YOLOv8 → ตรวจวัตถุบนภาพสี
ผูกข้อมูลลึกเพื่อคำนวณ xyz ต่อกล่องตรวจจับ (และแปลงไปพิกัดหุ่นยนต์ถ้ามีเมทริกซ์แคลิเบรต)
ส่งผลลัพธ์ผ่าน UDP/TCP/EKI และแสดงภาพพรีวิว (ถ้ามี DISPLAY)
เทคโนโลยี/ไลบรารีที่ใช้
Python 3, ultralytics (YOLOv8), numpy, PyYAML
OpenCV (แนะนำติดตั้งผ่าน apt: python3-opencv บน Jetson)
Intel RealSense SDK (librealsense + pyrealsense2)
PyTorch (มีรองรับ Jetson GPU; ถ้าไม่ติดตั้งจะรัน CPU ได้)
ระบบบริการ: systemd (ออปชัน)
โครงสร้างสำคัญ
src/camera/realsense_camera.py: อ่านสี/ลึก + คำนวณ xyz จาก depth
src/detector/yolo_detector.py: โหลด/รัน YOLOv8 (รองรับ FP16 บน CUDA)
src/output/{udp_sender.py,tcp_sender.py,eki_sender.py}: ส่งผลลัพธ์
src/main.py: รวมทุกส่วน, จำกัด FPS, พรีวิว, สร้าง payload
config/config.yaml: ตั้งค่าโมเดล/กล้อง/เอาต์พุต/แคลิเบรชัน/ล็อก
scripts/{setup_jetson.sh,download_model.sh,run.sh}: ติดตั้ง/ดาวน์โหลด/รัน
systemd/jetson-yolo-realsense-kuka.service: รันเป็นบริการ
สิ่งที่ต้องมี/รองรับ
ฮาร์ดแวร์: NVIDIA Jetson (JetPack 6.x แนะนำ), Intel RealSense D435i (USB3)
OS: Ubuntu 22.04 64-bit
CUDA/cuDNN (ถ้าจะใช้ GPU)
เครือข่ายสำหรับส่ง UDP/TCP ไปยังฝั่ง KUKA/ตัวรับ


ติดตั้งแบบย่อ (บน Jetson)
Apply to README.md
Run
```bash
cd /home/god/jetson-yolo-realsense-kuka
bash scripts/setup_jetson.sh
bash scripts/download_model.sh
```

สคริปต์จะ: ติดตั้งแพ็กเกจระบบ, librealsense/pyrealsense2, สร้าง venv (พร้อม system site-packages), อัปเดต pip, ลง requirements.txt และตรวจเช็ค pyrealsense2


ติดตั้ง PyTorch GPU บน Jetson (ถ้าต้องการ)
Apply to README.md
```bash
source .venv/bin/activate
pip install --upgrade pip
pip install torch torchvision torchaudio --index-url https://pypi.jetson-ai-lab.io/jp6/cu126
python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
```

รัน
Apply to README.md
Run
เปิด venv ให้เองและตั้ง PYTHONPATH ให้เห็น pyrealsense2/OpenCV จากระบบ
ตั้งค่าแก้ใน config/config.yaml ก่อนรันถ้าต้องการ
ตั้งค่าที่ควรรู้ (config/config.yaml)
model.path: ไฟล์ .pt ของ YOLOv8 (ดีฟอลต์ใช้ models/yolov8n.pt)
runtime.device: "auto"/"cpu"/ดัชนี CUDA เช่น "0", half: true ใช้ FP16 ถ้า CUDA
camera: ความละเอียด/เฟรมเรต สี/ลึก, align_to_color: true
output.udp: enabled, host, port, send_depth_xyz, max_detections
output.tcp / output.eki: เปิดใช้งานและกำหนด host/port
calibration.T_cam_to_robot: เมทริกซ์ 4x4 สำหรับได้ xyz_robot
รันเป็นบริการ (ออปชัน)
Apply to README.md
Run
ปัญหาที่พบบ่อย (สั้นๆ)
pyrealsense2 หาไม่เจอ: ติดตั้งผ่าน apt หรือคอมไพล์จากซอร์ส (มีขั้นตอนใน scripts/setup_jetson.sh)
OpenCV GUI ไม่มี DISPLAY: จะปิดพรีวิวอัตโนมัติ หรือกำหนด output.preview_window: false
Torch ไม่ใช้ GPU: ตรวจเวอร์ชันล้อและ CUDA ให้ตรง JetPack แล้วเช็ค torch.cuda.is_available()
สรุปสั้น
โปรเจคนี้จับภาพ RealSense, รัน YOLOv8, ส่งผลลัพธ์ทาง UDP/TCP/EKI ให้ KUKA
ติดตั้งด้วย scripts/setup_jetson.sh และโหลดโมเดลด้วย scripts/download_model.sh
รันด้วย scripts/run.sh และปรับพฤติกรรมผ่าน config/config.yaml
ต้องมี: Jetson + Ubuntu 22.04 + RealSense SDK + OpenCV (apt) + PyTorch (ล้อ Jetson ถ้าจะใช้ GPU)


