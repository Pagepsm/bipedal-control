"""Dependency-free, versioned 2D terrain geometry contract.

This is *not* a physics engine. Conversion to actual Box2D bodies is performed
by the separate (as-yet unverified) custom environment adapter.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import math
from typing import Iterable, Mapping

SCHEMA_VERSION = "terrain.heightfield.v1"
SAMPLES = 200
START_PAD = 20
WORLD_STEP_M = 14.0 / 30.0
BASE_HEIGHT_M = (400.0 / 30.0) / 4.0
MAX_ABS_OFFSET_M = 2.0
MAX_ADJACENT_CHANGE_M = 1.3
ROUND_DIGITS = 6


def _as_number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a real number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


@dataclass(frozen=True)
class TerrainProfile:
    """Height offsets in physical meters relative to Gymnasium's base ground.

    Sample count and spatial resolution are fixed to avoid changing the
    reference walker spawn and goal interpretation in version v1.
    """

    height_offsets_m: tuple[float, ...]

    def __post_init__(self) -> None:
        if len(self.height_offsets_m) != SAMPLES:
            raise ValueError(f"expected {SAMPLES} height samples")
        normalized: list[float] = []
        for idx, value in enumerate(self.height_offsets_m):
            x = round(_as_number(value, f"height_offsets_m[{idx}]"), ROUND_DIGITS)
            if abs(x) > MAX_ABS_OFFSET_M:
                raise ValueError(f"height sample {idx} exceeds permitted height")
            if idx < START_PAD and x != 0.0:
                raise ValueError(f"sample {idx} must be flat at the spawn pad")
            if idx > 0 and abs(x - normalized[idx - 1]) > MAX_ADJACENT_CHANGE_M:
                raise ValueError(f"adjacent ground height change exceeds cap at {idx}")
            normalized.append(0.0 if x == 0 else x)
        object.__setattr__(self, "height_offsets_m", tuple(normalized))

    @classmethod
    def from_data(cls, raw: Mapping[str, object]) -> "TerrainProfile":
        if set(raw.keys()) != {"schema_version", "height_offsets_m"}:
            raise ValueError("unexpected or missing terrain fields")
        if raw["schema_version"] != SCHEMA_VERSION:
            raise ValueError("unsupported terrain schema version")
        offsets = raw["height_offsets_m"]
        if not isinstance(offsets, list):
            raise ValueError("height_offsets_m must be a JSON array")
        return cls(tuple(offsets))

    def to_data(self) -> dict[str, object]:
        return {"schema_version": SCHEMA_VERSION, "height_offsets_m": list(self.height_offsets_m)}

    def canonical_json(self) -> str:
        return json.dumps(self.to_data(), sort_keys=True, separators=(",", ":"), allow_nan=False)

    @property
    def terrain_sha256(self) -> str:
        return sha256(self.canonical_json().encode("utf-8")).hexdigest()

    def world_points(self) -> tuple[tuple[float, float], ...]:
        return tuple((idx * WORLD_STEP_M, BASE_HEIGHT_M + value)
                     for idx, value in enumerate(self.height_offsets_m))


def from_normalized_stroke(stroke: Iterable[tuple[float, float]], amplitude_m: float = 2.0) -> TerrainProfile:
    """Resample a left-to-right screen-space stroke into physical terrain.

    Input coordinate convention: x=0..1 from left to right, y=0..1 from
    top to bottom. The reference flat-ground baseline is y=0.5.

    This function deliberately REJECTS non-monotonic x instead of silently
    converting complex arbitrary shapes into misleading single-valued ground.
    The first 20 samples are fixed flat for the original walker spawn.
    """
    points = [(_as_number(x, "stroke.x"), _as_number(y, "stroke.y")) for x, y in stroke]
    if len(points) < 2:
        raise ValueError("at least two stroke points required")
    if len(points) > 4096:
        raise ValueError("too many input points")
    a = _as_number(amplitude_m, "amplitude_m")
    if a <= 0 or a > 4:
        raise ValueError("unsupported amplitude_m")
    for idx, (x, y) in enumerate(points):
        if x < 0 or x > 1 or y < 0 or y > 1:
            raise ValueError("stroke points must be in [0,1]")
        if idx > 0 and x <= points[idx - 1][0]:
            raise ValueError("stroke x must increase strictly")
    if points[0][0] != 0.0 or points[-1][0] != 1.0:
        raise ValueError("stroke must span the full x=0..1 domain")
    result = []
    segment_idx = 0
    for i in range(SAMPLES):
        x = i / (SAMPLES - 1)
        while segment_idx + 1 < len(points) - 1 and points[segment_idx + 1][0] < x:
            segment_idx += 1
        left, right = points[segment_idx], points[segment_idx + 1]
        frac = (x - left[0]) / (right[0] - left[0])
        y = left[1] + frac * (right[1] - left[1])
        result.append(0.0 if i < START_PAD else a * (0.5 - y))
    return TerrainProfile(tuple(result))
