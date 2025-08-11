from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Iterator, Optional, Tuple

import numpy as np


@dataclass
class FrameData:
    color: np.ndarray
    depth: Optional[np.ndarray]
    intrinsics: Optional[dict]


class RealSenseCamera:
    def __init__(
        self,
        serial: str | None,
        color_width: int,
        color_height: int,
        color_fps: int,
        depth_width: int,
        depth_height: int,
        depth_fps: int,
        align_to_color: bool = True,
        logger=None,
    ) -> None:
        self.serial = serial or ""
        self.color_width = color_width
        self.color_height = color_height
        self.color_fps = color_fps
        self.depth_width = depth_width
        self.depth_height = depth_height
        self.depth_fps = depth_fps
        self.align_to_color = align_to_color
        self.logger = logger

        self._pipeline = None
        self._align = None
        self._colorizer = None
        self._depth_scale = None
        self._profile = None

    def start(self) -> None:
        rs = self._import_pyrealsense2()

        pipeline = rs.pipeline()
        config = rs.config()
        if self.serial:
            config.enable_device(self.serial)
        config.enable_stream(rs.stream.color, self.color_width, self.color_height, rs.format.bgr8, self.color_fps)
        config.enable_stream(rs.stream.depth, self.depth_width, self.depth_height, rs.format.z16, self.depth_fps)

        self._profile = pipeline.start(config)
        depth_sensor = self._profile.get_device().first_depth_sensor()
        self._depth_scale = float(depth_sensor.get_depth_scale())

        self._pipeline = pipeline
        if self.align_to_color:
            self._align = rs.align(rs.stream.color)

        if self.logger:
            self.logger.info(
                f"RealSense started (serial={self.serial or 'auto'}) color={self.color_width}x{self.color_height}@{self.color_fps} depth={self.depth_width}x{self.depth_height}@{self.depth_fps} scale={self._depth_scale}"
            )

    @staticmethod
    def _import_pyrealsense2():
        try:
            import pyrealsense2 as rs  # type: ignore
            return rs
        except ModuleNotFoundError:
            pass

        # Attempt to add common locations to sys.path
        import sys
        from pathlib import Path

        project_root = Path(__file__).resolve().parents[2]
        py_major = sys.version_info.major
        py_minor = sys.version_info.minor

        candidate_paths = [
            project_root / ".venv" / "lib" / f"python{py_major}.{py_minor}" / "site-packages",
            "/usr/local/lib/python3.10/dist-packages",
            "/usr/local/lib/python3/dist-packages",
            "/usr/lib/python3/dist-packages",
        ]
        for cp in candidate_paths:
            p = str(cp)
            if p not in sys.path:
                sys.path.append(p)
            try:
                import pyrealsense2 as rs  # type: ignore
                return rs
            except ModuleNotFoundError:
                continue
        raise ModuleNotFoundError("pyrealsense2 not found. Ensure librealsense Python bindings are installed.")

    def stop(self) -> None:
        if self._pipeline is not None:
            self._pipeline.stop()
            self._pipeline = None

    def frames(self) -> Iterator[FrameData]:
        import pyrealsense2 as rs

        if self._pipeline is None:
            raise RuntimeError("Camera not started")

        while True:
            frames = self._pipeline.wait_for_frames()
            if self._align is not None:
                frames = self._align.process(frames)

            depth_frame = frames.get_depth_frame()
            color_frame = frames.get_color_frame()
            if not depth_frame or not color_frame:
                continue

            color = np.asanyarray(color_frame.get_data())
            depth = np.asanyarray(depth_frame.get_data())

            intr = color_frame.profile.as_video_stream_profile().intrinsics
            intrinsics = {
                "fx": float(intr.fx),
                "fy": float(intr.fy),
                "ppx": float(intr.ppx),
                "ppy": float(intr.ppy),
                "width": int(intr.width),
                "height": int(intr.height),
                "depth_scale": float(self._depth_scale),
            }

            yield FrameData(color=color, depth=depth, intrinsics=intrinsics)

    @staticmethod
    def depth_to_xyz(
        u: int,
        v: int,
        depth_value: float,
        intrinsics: dict,
    ) -> Tuple[float, float, float]:
        fx = intrinsics["fx"]
        fy = intrinsics["fy"]
        ppx = intrinsics["ppx"]
        ppy = intrinsics["ppy"]
        scale = intrinsics.get("depth_scale", 0.001)
        z = depth_value * scale
        x = (u - ppx) / fx * z
        y = (v - ppy) / fy * z
        return x, y, z


