"""PROVISIONAL Gymnasium adapter for user-authored heightfields.

Not executed here with real Box2D. Before using for scientific claims,
complete the real integration and regression gates in docs/TERRAIN_FEASIBILITY.md.
The _generate_terrain method is an upstream semi-private implementation hook.
"""

from __future__ import annotations

from gymnasium.envs.box2d.bipedal_walker import (
    BipedalWalker,
    TERRAIN_GRASS,
    TERRAIN_HEIGHT,
    TERRAIN_LENGTH,
    TERRAIN_STEP,
)

from robust_bipedal.terrain_geometry import (
    BASE_HEIGHT_M,
    SAMPLES,
    TerrainProfile,
    WORLD_STEP_M,
)


class UserTerrainBipedalWalker(BipedalWalker):
    """Reuse authoritative Box2D dynamics; substitute only ground geometry."""

    def __init__(self, terrain_profile: TerrainProfile, render_mode: str | None = None):
        if TERRAIN_LENGTH != SAMPLES or abs(TERRAIN_STEP - WORLD_STEP_M) > 1e-9:
            raise RuntimeError("Gymnasium terrain geometry changed; review adapter")
        if abs(TERRAIN_HEIGHT - BASE_HEIGHT_M) > 1e-9:
            raise RuntimeError("Gymnasium base ground height changed; review adapter")
        self.terrain_profile = terrain_profile
        super().__init__(render_mode=render_mode, hardcore=False)

    def _generate_terrain(self, hardcore: bool):
        if hardcore:
            raise ValueError("Custom terrain must not be presented as official Hardcore")
        points = self.terrain_profile.world_points()
        self.terrain_x = [point[0] for point in points]
        self.terrain_y = [point[1] for point in points]
        self.terrain = []
        self.terrain_poly = []
        for i in range(len(points) - 1):
            a, b = points[i], points[i + 1]
            self.fd_edge.shape.vertices = [a, b]
            ground = self.world.CreateStaticBody(fixtures=self.fd_edge)
            color = (76, 255 if i % 2 == 0 else 204, 76)
            ground.color1 = color
            ground.color2 = color
            self.terrain.append(ground)
            self.terrain_poly.append(([a, b, (b[0], 0), (a[0], 0)], (102, 153, 76)))
        self.terrain.reverse()

    def step(self, action):
        obs, reward, terminated, truncated, info = super().step(action)
        info = dict(info)
        info["custom_terrain_sha256"] = self.terrain_profile.terrain_sha256
        if terminated:
            x = float(self.hull.position.x)
            info["goal_reached"] = (not bool(self.game_over)) and x > (
                TERRAIN_LENGTH - TERRAIN_GRASS
            ) * TERRAIN_STEP
            info["fell"] = bool(self.game_over) or x < 0
            info["outcome"] = ("goal" if info["goal_reached"] else
                               "fall" if info["fell"] else "other_terminal")
        return obs, reward, terminated, truncated, info
