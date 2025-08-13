from __future__ import annotations

import argparse
import os
import json
import signal
import sys
import time
from pathlib import Path

import cv2
import numpy as np
import yaml

from utils.logger import setup_logger
from utils.draw import draw_detections
from camera.realsense_camera import RealSenseCamera
from detector.yolo_detector import YoloV8Detector
from output.udp_sender import UdpSender
from output.tcp_sender import TcpSender
from output.eki_sender import EkiXmlSender
from utils.geometry import transform_point_homogeneous


def load_config(path: str) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(Path(__file__).resolve().parents[1] / "config" / "config.yaml"))
    parser.add_argument("--mode", choices=["realtime", "single"], help="Run mode: realtime loop or single-shot")
    args = parser.parse_args()

    config = load_config(args.config)

    logger = setup_logger(
        name="app",
        level=config.get("logging", {}).get("level", "INFO"),
        logfile=config.get("logging", {}).get("file"),
    )

    # Camera setup
    cam_cfg = config["camera"]
    camera = RealSenseCamera(
        serial=cam_cfg.get("serial") or None,
        color_width=cam_cfg["color"]["width"],
        color_height=cam_cfg["color"]["height"],
        color_fps=cam_cfg["color"]["fps"],
        depth_width=cam_cfg["depth"]["width"],
        depth_height=cam_cfg["depth"]["height"],
        depth_fps=cam_cfg["depth"]["fps"],
        align_to_color=cam_cfg.get("align_to_color", True),
        logger=logger,
    )

    # Detector setup
    det_cfg = config["model"]
    run_cfg = config["runtime"]
    mode = (args.mode or run_cfg.get("mode", "realtime")).strip().lower()
    warmup_frames = int(run_cfg.get("warmup_frames", 3))
    detector = YoloV8Detector(
        model_path=det_cfg["path"],
        device=run_cfg.get("device", "auto"),
        half=run_cfg.get("half", True),
        conf_threshold=det_cfg.get("conf_threshold", 0.25),
        iou_threshold=det_cfg.get("iou_threshold", 0.45),
        classes=det_cfg.get("classes") or None,
        logger=logger,
    )

    # UDP setup
    udp_cfg = config["output"]["udp"]
    udp_sender = None
    if udp_cfg.get("enabled", True):
        udp_sender = UdpSender(udp_cfg["host"], int(udp_cfg["port"]), logger=logger)

    # TCP JSON setup
    tcp_cfg = config["output"].get("tcp", {})
    tcp_sender = None
    if tcp_cfg.get("enabled", False):
        tcp_sender = TcpSender(
            tcp_cfg.get("host", "127.0.0.1"),
            int(tcp_cfg.get("port", 6000)),
            logger=logger,
            send_newline=bool(tcp_cfg.get("newline", True)),
        )

    # KUKA EKI XML setup
    eki_cfg = config["output"].get("eki", {})
    eki_sender = None
    if eki_cfg.get("enabled", False):
        eki_sender = EkiXmlSender(
            eki_cfg.get("host", "127.0.0.1"),
            int(eki_cfg.get("port", 7000)),
            logger=logger,
            root_tag=str(eki_cfg.get("root_tag", "EKI")),
            only_first_detection=bool(eki_cfg.get("only_first_detection", True)),
            use_robot_xyz=bool(eki_cfg.get("use_robot_xyz", True)),
            pretty=bool(eki_cfg.get("pretty", False)),
        )

    preview_window = config["output"].get("preview_window", True)
    if preview_window and not os.environ.get("DISPLAY"):
        logger.warning("No DISPLAY detected; disabling preview window")
        preview_window = False
    draw_overlay = run_cfg.get("draw", True)
    send_xyz = udp_cfg.get("send_depth_xyz", True)
    T_cam_to_robot = config.get("calibration", {}).get("T_cam_to_robot")
    max_det = int(udp_cfg.get("max_detections", 20))
    max_fps = float(run_cfg.get("max_fps", 30))

    # Latest JPEG output for UI
    latest_jpeg_cfg = (config.get("output", {}).get("latest_jpeg", {}) if isinstance(config.get("output"), dict) else {})
    save_latest = bool(latest_jpeg_cfg.get("enabled", False))
    latest_path = str(latest_jpeg_cfg.get("path", Path(__file__).resolve().parents[1] / "output" / "latest.jpg"))
    os.makedirs(os.path.dirname(latest_path), exist_ok=True)

    def handle_sigint(signum, frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGINT, handle_sigint)

    camera.start()
    detector.load()

    try:
        last_time = 0.0
        warm_count = 0
        for frame in camera.frames():
            # Warm-up for single-shot mode to let auto-exposure/streams stabilize
            if mode == "single" and warm_count < warmup_frames:
                warm_count += 1
                continue

            # Throttle only in realtime mode
            if mode == "realtime" and max_fps > 0:
                now = time.time()
                if now - last_time < 1.0 / max_fps:
                    continue
                last_time = now

            color = frame.color
            detections = detector.infer(color)

            # depth + XYZ
            if send_xyz and frame.depth is not None and frame.intrinsics is not None:
                depth = frame.depth
                intr = frame.intrinsics
                for det in detections:
                    x1, y1, x2, y2 = det["bbox"]
                    cx = int((x1 + x2) / 2)
                    cy = int((y1 + y2) / 2)
                    depth_value = float(depth[cy, cx]) if 0 <= cy < depth.shape[0] and 0 <= cx < depth.shape[1] else 0.0
                    xyz_cam = RealSenseCamera.depth_to_xyz(cx, cy, depth_value, intr)
                    det["xyz"] = xyz_cam
                    if T_cam_to_robot is not None:
                        try:
                            det["xyz_robot"] = transform_point_homogeneous(T_cam_to_robot, xyz_cam)
                        except Exception:
                            det["xyz_robot"] = None

            # build payload once and send over enabled outputs
            payload = None
            if udp_sender is not None or tcp_sender is not None or eki_sender is not None:
                payload = {
                    "ts": time.time(),
                    "detections": [
                        {
                            "bbox": d["bbox"],
                            "score": d["score"],
                            "class_id": d["class_id"],
                            "class_name": d.get("class_name"),
                            "xyz": d.get("xyz"),
                            "xyz_robot": d.get("xyz_robot"),
                        }
                        for d in detections[:max_det]
                    ],
                    "frame": {
                        "w": int(color.shape[1]),
                        "h": int(color.shape[0]),
                    },
                }
                if udp_sender is not None:
                    udp_sender.send(payload)
                if tcp_sender is not None:
                    tcp_sender.send(payload)
                if eki_sender is not None:
                    eki_sender.send(payload)

            # save latest jpeg for UI
            if save_latest:
                try:
                    vis = color.copy()
                    if draw_overlay:
                        vis = draw_detections(vis, detections, show_depth=send_xyz)
                    cv2.imwrite(latest_path, vis)
                except Exception:
                    pass

            # preview
            if preview_window:
                try:
                    vis = color.copy()
                    if draw_overlay:
                        vis = draw_detections(vis, detections, show_depth=send_xyz)
                    cv2.imshow("YOLOv8 + RealSense", vis)
                    if cv2.waitKey(1) & 0xFF == 27:
                        break
                except cv2.error:
                    logger.warning("OpenCV GUI not available; disabling preview window")
                    preview_window = False

            # In single-shot mode, process once and exit
            if mode == "single":
                if payload is not None:
                    try:
                        print(json.dumps(payload))
                    except Exception:
                        pass
                break

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        camera.stop()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()


