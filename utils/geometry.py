from __future__ import annotations

from typing import Iterable, Tuple

import numpy as np


def transform_point_homogeneous(T_4x4: Iterable[Iterable[float]], xyz_m: Iterable[float]) -> Tuple[float, float, float]:
    T = np.asarray(T_4x4, dtype=float).reshape(4, 4)
    p = np.array([xyz_m[0], xyz_m[1], xyz_m[2], 1.0], dtype=float)
    pr = T @ p
    return float(pr[0]), float(pr[1]), float(pr[2])


