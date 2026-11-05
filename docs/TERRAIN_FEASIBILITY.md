# Technical investigation: handwritten terrain and the existing BipedalWalker

> 2026年10月14日時点の設計・検証記録です。現在の制作物と実験結果は[作品紹介](../README.md)からご覧ください。

Research date: 2026-10-14. This is source-code-level feasibility, not a confirmed execution in a working Box2D environment.

## A. Verified mechanisms in official source

Source: https://github.com/Farama-Foundation/Gymnasium/blob/main/gymnasium/envs/box2d/bipedal_walker.py (upstream main viewed 2026-10-14; pin an actual package tag/commit before implementing).

1. `reset()` invokes `self._generate_terrain(self.hardcore)` before constructing the robot bodies. Thus a subclass can substitute this method without reimplementing the robot.
2. `_generate_terrain()` builds `terrain_x`, `terrain_y`, `terrain_poly`, `terrain`, then uses `self.fd_edge.shape.vertices` and `world.CreateStaticBody(fixtures=self.fd_edge)` for ground collision segments.
3. Rendering uses `terrain_poly` and `drawlist`; the latter is built after terrain generation. Lidar filters raycast fixtures by ground category bits, so the overridden ground must use the existing `fd_edge` fixture.
4. Initial hull position is tied to constant `TERRAIN_HEIGHT`, not any arbitrary drawn initial floor. Hence first `TERRAIN_STARTPAD` samples must remain at that base height, or the spawn logic must also be explicitly updated/tested.
5. Original environment's goal check depends on `TERRAIN_LENGTH`, `TERRAIN_GRASS`, `TERRAIN_STEP`. Consequently keep the exact original horizontal domain for `v1`, and record goal success via the actual coordinate/termination logic. No arbitrary drawing-length goals without an explicit custom rule.
6. Action values `[-1,1]^4` are **not simply continuous requested motor speeds** in the current code: the active `control_speed=False` branch uses action sign to set motor-speed direction, and its absolute magnitude to set max motor torque. Previous plan calling them only 'velocity commands' is insufficient; document actual behavior for the installed pinned source.
7. Normal and Hardcore benchmarks must remain untouched. Custom terrain may require a registered custom `Env`/`TimeLimit` wrapper, but must never be presented as `BipedalWalker-v3` official scoring.

Independent engineering precedent: https://github.com/nicklashansen/newt/blob/main/tdmpc2/envs/tasks/bipedal_walker.py extends `BipedalWalker` and overrides `_generate_terrain`. Do not copy third-party code; maintain independent implementation and attribution.

## B. Three implementation options

| Option | Suitable? | Tradeoff |
|---|---|---|
| Rebuild robot physics from scratch | No | High effort and scientific benchmark divergence |
| **Subclass official Python Gymnasium BipedalWalker and replace terrain** | **Preferred** | Preserves Box2D robot/joint/contact dynamics, but depends on semi-private method and needs version/fixture regression tests |
| Run a JavaScript physics engine (Planck.js) in-browser | Phase-2 alternative only | Client-only hosting, but reproducing joint constraints/collisions/observations/control and validating Python equivalence is a separate substantial engineering project |

Planck.js official project: https://piqnt.com/planck.js/ . Shared '2D Box2D lineage' is not proof of numerical identity.

## C. Input scope: a terrain profile, not arbitrary 2D artwork

`terrain.heightfield.v1` represents a single-valued height profile `y=h(x)`: one ground elevation for each horizontal x, with 200 evenly spaced samples at the original benchmark's horizontal resolution.

Supported first release: hills, slopes, smooth/steep ridges and drops within an explicitly validated vertical range.

Excluded first release: loops, caves, ceilings, overhangs, arbitrary closed shapes, bridges, and floating platforms. Gaps/pits require a later version with **multiple disjoint collision segments**; forcing holes into a continuous height function incorrectly creates a walkable floor.

The canvas drawing is constrained to one height for each x. Conversion: (screen stroke) -> sampled normalized y-values -> vertical offsets in Box2D meters -> validated fixed-length immutable JSON -> `terrain_sha256` -> Box2D static collision edges + display polygons.

Contract basics for initial prototype:
- 200 samples; same horizontal spacing and starting position as pinned Gymnasium version.
- First 20 ground samples unmodified so the initial robot spawn remains physically meaningful. This constant must be verified against the pinned implementation.
- Absolute y is `TERRAIN_HEIGHT + height_offset_m`, where positive is up.
- Every offset finite, within +/-2.0 m; adjacent-sample vertical difference <=1.3 m. These are **prototype UX/collision bounds, not proven physical reachability**.
- Browser shows the exact post-quantization/validation ground curve; never silently change the original drawing or claim every accepted path is traversable.
- User can choose difficult or impossible terrain within legal bounds. Display failure honestly; no 'AI can solve all terrains' claim.
- Saved geometry includes schema version and SHA-256 over canonical JSON. Visual-only cosmetic 2.5D extrusion is permissible and does not change physics.

## D. Two distinct smoke gates

**Geometry-only (testable without Box2D):** stroke quantization, dimension, finiteness, bounds, start pad, deterministic hash, JSON roundtrip, same points produce same world geometry.

**Real physics (not yet run):** fresh process with pinned Gymnasium/PyBox2D, instantiate custom env, reset/step, observe (24,) / action (4,), ensure lidar hits terrain, contact callbacks work, renderer works, floor matches drawing, goal/fall/timeout separate, repeated reset removes old fixture bodies, no memory leak, no spawn penetration.

Regression contract: compare unmodified official env output to official env on same versions, validate robot/leg/joint fixture parameters and reward were not modified; custom env differs only by geometry, scenario and separate labelling.

## E. Remaining uncertainties and fallbacks

- Gymnasium terrain construction is not a documented stable extension API. If pinning or subclass regression fails, maintain a small **Project-local adapter** tied to a specific upstream version rather than patching shared Platform code.
- Reusing old checkpoint assumes identical observation semantics, action meaning, normalization, lidar filters and reward shaping; assert all before loading.
- Severe slopes and discontinuities can be unstable or impossible; validate numeric stability, not universal traversability.
- Custom environment must implement its own definitive outcomes; `terminated=True` alone cannot distinguish fall from goal.