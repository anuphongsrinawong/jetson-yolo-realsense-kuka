from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

import numpy as np


class YoloV8Detector:
    def __init__(
        self,
        model_path: str,
        device: str = "auto",
        half: bool = True,
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45,
        classes: Optional[list[int]] = None,
        logger=None,
    ) -> None:
        self.model_path = model_path
        self.device = device
        self.half = half
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.classes = classes
        self.logger = logger

        self._model = None
        self._class_names = None

    def load(self) -> None:
        import torch
        from ultralytics import YOLO

        # Workaround for PyTorch 2.6+ safe unpickling (weights_only=True default)
        try:
            from torch.serialization import add_safe_globals  # type: ignore[attr-defined]
            try:
                from ultralytics.nn.tasks import DetectionModel  # type: ignore
                add_safe_globals([DetectionModel])  # allowlist Ultralytics model class
            except Exception:
                pass
        except Exception:
            pass

        # Force torch.load to use weights_only=False unless explicitly provided
        try:
            _orig_torch_load = torch.load

            def _patched_torch_load(*args, **kwargs):
                if "weights_only" not in kwargs:
                    kwargs["weights_only"] = False
                return _orig_torch_load(*args, **kwargs)

            torch.load = _patched_torch_load  # type: ignore[assignment]
        except Exception:
            pass

        device = self._resolve_device()
        self._model = YOLO(self.model_path)

        if device.type == "cuda":
            try:
                self._model.to(device)
            except Exception:
                pass
        if device.type == "cuda" and self.half:
            try:
                self._model.model.half()
                if self.logger:
                    self.logger.info("YOLO model set to FP16")
            except Exception:
                if self.logger:
                    self.logger.warning("FP16 not supported; continuing in FP32")

        self._class_names = self._model.model.names
        if self.logger:
            self.logger.info(f"Loaded YOLO model: {self.model_path} on {device}")

    def _resolve_device(self):
        import torch

        if self.device == "auto":
            device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        elif self.device == "cpu":
            device = torch.device("cpu")
        else:
            device = torch.device(f"cuda:{self.device}")
        return device

    def infer(self, image_bgr: np.ndarray) -> List[Dict[str, Any]]:
        if self._model is None:
            raise RuntimeError("Detector not loaded")

        results = self._model.predict(
            source=image_bgr,
            conf=self.conf_threshold,
            iou=self.iou_threshold,
            imgsz=max(image_bgr.shape[0], image_bgr.shape[1]),
            classes=self.classes,
            verbose=False,
            device=0 if self._resolve_device().type == "cuda" else "cpu",
        )

        detections: List[Dict[str, Any]] = []
        r = results[0]
        if r.boxes is None or len(r.boxes) == 0:
            return detections

        for b in r.boxes:
            xyxy = b.xyxy[0].tolist()
            x1, y1, x2, y2 = [int(v) for v in xyxy]
            conf = float(b.conf[0].item()) if hasattr(b, "conf") else float(b.confidence)
            cls_id = int(b.cls[0].item()) if hasattr(b, "cls") else int(b.class_id)

            class_name = (
                self._class_names[cls_id]
                if self._class_names and cls_id in self._class_names
                else str(cls_id)
            )

            detections.append(
                {
                    "bbox": [x1, y1, x2, y2],
                    "score": conf,
                    "class_id": cls_id,
                    "class_name": class_name,
                }
            )
        return detections


