"""REAL Box2D smoke script. Dependencies must be provisioned first.

Use: PYTHONPATH=src python -m robust_bipedal.smoke_real_env
"""

from __future__ import annotations

import json


def main():
    from gymnasium.wrappers import TimeLimit
    import gymnasium as gym
    import numpy as np

    from robust_bipedal.custom_bipedal_env import UserTerrainBipedalWalker
    from robust_bipedal.terrain_geometry import TerrainProfile, SAMPLES

    profile = TerrainProfile((0.0,) * SAMPLES)
    env = TimeLimit(UserTerrainBipedalWalker(profile, render_mode="rgb_array"), max_episode_steps=1600)
    evidence = {"terrain_sha256": profile.terrain_sha256, "gymnasium": gym.__version__}
    try:
        for episode_seed in (42, 42, 43):
            observation, _ = env.reset(seed=episode_seed)
            assert observation.shape == (24,), observation.shape
            assert env.action_space.shape == (4,)
            assert len(env.unwrapped.terrain) == SAMPLES - 1
            assert len(env.unwrapped.terrain_poly) == SAMPLES - 1
            assert np.allclose(np.array(env.unwrapped.terrain_y),
                               np.array([p[1] for p in profile.world_points()]))
            frame = env.render()
            assert frame is not None and frame.ndim == 3 and frame.shape[2] == 3
            first_observation = observation.copy()
            for _ in range(8):
                observation, reward, terminated, truncated, info = env.step(np.zeros(4, dtype=np.float32))
                assert info.get("custom_terrain_sha256") == profile.terrain_sha256
                if terminated or truncated:
                    break
            evidence.setdefault("first_observations", []).append(first_observation.tolist())
        assert np.allclose(evidence["first_observations"][0], evidence["first_observations"][1])
        evidence["status"] = "PASS_SMOKE_ONLY"
    finally:
        env.close()
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
