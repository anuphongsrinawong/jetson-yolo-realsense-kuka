from __future__ import annotations

import cv2
import numpy as np


def draw_detections(
    image: np.ndarray,
    detections: list[dict],
    color: tuple[int, int, int] = (0, 255, 0),
    thickness: int = 2,
    show_depth: bool = True,
) -> np.ndarray:
    for det in detections:
        x1, y1, x2, y2 = det["bbox"]
        cls = det.get("class_name", str(det.get("class_id", "?")))
        conf = det.get("score", 0.0)
        xyz = det.get("xyz")

        cv2.rectangle(image, (x1, y1), (x2, y2), color, thickness)
        label = f"{cls} {conf:.2f}"
        if show_depth and xyz is not None:
            label += f" z={xyz[2]:.2f}m"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(image, (x1, y1 - th - 6), (x1 + tw + 4, y1), color, -1)
        cv2.putText(
            image,
            label,
            (x1 + 2, y1 - 4),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 0, 0),
            1,
            cv2.LINE_AA,
        )
    return image


