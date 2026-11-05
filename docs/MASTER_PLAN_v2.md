# Robust Bipedal Control — Master Plan v2.0

> 2026年10月14日時点の設計・検証記録です。現在の制作物と実験結果は[作品紹介](../README.md)からご覧ください。

**Date:** 2026-10-14  
**Status:** DRAFT FOR EXECUTION (reviewed architecture; not a Platform Release)  
**Decision:** 2D BipedalWalker × Box2D × multiple learned/benchmark controls × browser user-drawn heightfield  
**Prior plan:** `ROBUST_BIPEDAL_CONTROL_MASTER_PLAN_v1.md` (replaces its earlier 'browser out of scope' boundary)  
**Provided Platform specification:** `FX_PLATFORM_EA_DEVELOPMENT_SPEC_v8.md`, ISSUED 2026-10-13, Platform 1.7.2. Its runtime state is not established by this document.

## 0. Executive decision and deliverables

**Product objective:** A person sketches a side-on 2D ground profile in a browser. An actual physics-based two-legged robot, controlled by multiple **pre-trained and frozen** feedback policies, traverses **that exact same** ground in comparable simulations. Side-by-side synchronized playback shows the outcome and quantitative metrics. The visitor can investigate whether different controllers perform differently across terrains and test conditions; no promise that AI will solve arbitrary terrain.

**Engineering/research objective:** Independently build and rigorously evaluate robust deep-RL policies on unmodified Gymnasium BipedalWalker benchmarks, separately measure distribution shifts, then expose *those proven and frozen policies* through a repeatable custom-terrain evaluation engine. The web app is a scientific demonstration, not a replacement for the controlled benchmark.

### Two project pillars (must remain connected but separable)

1. **Pillar I — Benchmark and methods**: official baseline reproduction → PPO-Standard → PPO-Robust and candidate terrain-curriculum PPO / independent SAC → defined seed-based evaluation → published model/provenance package.
2. **Pillar II — Interactive deployment**: 2D drawing → validated immutable heightfield → authoritative Python Box2D simulation for every selected controller → synchronized browser playback → transparent per-terrain comparison.

Formal completion requires both pillars; a partially deployed editor or an RL reward chart alone does **not** constitute v1.0.

## 1. Strict scope / terminology

- **Robot and physics**: Existing Gymnasium BipedalWalker; articulated planar rigid bodies, joints, collision contacts and LiDAR from Box2D. The world is physically **2D**; optional extruded/2.5D drawing is visual only.
- **Action**: Four normalized joint motor commands. The current upstream code's active branch uses **sign for target motor speed direction and magnitude for maximum motor torque**; exact installed source is authoritative. Earlier phrasing 'just motor-speed commands' was incomplete.
- **AI**: A learned feedback policy, typically PPO or SAC, maps 24D observation to 4D action; it acts on every simulation step. AI's value is demonstrated through a defensible baseline and matched changed conditions, not a cinematic animation.
- **Terrain v1**: A single-valued 2D height function `y=h(x)` sampled at a fixed 200-point grid. A drawing can describe a nontrivial slope/roughness but **not** arbitrary closed polygons, tunnels, bridges or suspended objects; holes/gaps are v2 with separate collision geometry.
- **Official**: Upstream `BipedalWalker-v3` Normal/Hardcore with unchanged physics, reward, terrain, settings and wrapper configuration. **Never call custom terrain an official benchmark.**
- **Interactive**: Browser edits a shape and requests genuine physics evaluations; animation is a replay of authoritative recorded state, not an AI-generated illustration.

### Hard non-goals for v1.0

No physical humanoid or sim-to-real claim, no 3D physics, no training a new model on each browser request, no unbounded uploads of code/model checkpoints, no arbitrary mouse-created floating objects, no guarantees for physically impossible slopes, no full JavaScript Box2D physics port, no requirement for genuine formal Lyapunov guarantee.

## 2. Detailed architecture and decisions

### 2.1 Physics decision: keep Python Box2D

Source-confirmed upstream properties:
- Terrain constructor `_generate_terrain()` is invoked from `reset()` before robot instantiation.
- It translates `terrain_x`, `terrain_y` into `CreateStaticBody` edge fixtures and `terrain_poly` display polygons.
- LiDAR and contact depend on fixture category and consistent collision bodies.
- Spawn and goal coordinates depend on fixed original terrain constants, so v1 fixes exact sample count/spacing and start-pad elevation.

**Implementation:** `UserTerrainBipedalWalker(BipedalWalker)` overrides `_generate_terrain` in a Project-owned adapter, while retaining the robot, 24D observation, 4D action, contacts, reward shaping and render. Use a pinned Gymnasium version and regression tests because method is not a public stable terrain API. The included adapter is a **source-aligned draft; real Box2D runtime smoke not yet passed**.

**Alternatives rejected:** Building the full physics engine unnecessarily creates a distinct, non-benchmarkable simulator. JavaScript Planck.js is plausible for a future backend-free web version but requires validating equivalence of robot/contacts/lidar/controller IO; sharing Box2D concepts is not mathematical equivalence.

### 2.2 Terrain authoring: canonical model first

Pipeline:

```
Browser pointer stroke or control points (overview + physical-scale zoom)
     ↓ enforce one y for each x; display exact processed line
Normalized points (x in [0,1], y down [0,1])
     ↓ resample and map pixels to SI units
200 fixed-spaced height offsets; start-pad remains zero
     ↓ finite/range/slope checks; preserve requested geometry or reject
canonical `terrain.heightfield.v1` JSON + SHA-256
     ↓ authoritative backend parsing + version/shape validation
Box2D static edge fixtures / 2D renderer ground polygons
     ↓ reset walkers under controlled initial conditions
multi-controller episodes and trace capture
```

- Initial numerical contract is implemented in `terrain_geometry.py`: 200 samples, 20-sample flat spawn pad, 14/30 m horizontal step, nominal base ground `(400/30)/4` m, offsets within ±2.0 m, adjacent vertical difference ≤1.3 m. **These are provisional interface constraints, not measured passability limits**, and they must be reconciled with the exact installed Gymnasium source.
- Preserve edited intent: if smoothing or quantization is performed, show the resolved terrain to the user and require its use as the saved artifact. Never silently turn pits into solid ground.
- Store a short deterministic terrain SHA and the exact JSON. Each model rollout must attach it; compare only if hashes and physics versions match.
- Explicit warning if terrain outside trained range; possible failure is part of the experience.

### 2.3 Authoritative server and browser

**Frontend**: TypeScript Canvas/SVG drawing surface, profile preview, model picker, `Run comparison`, progress, synchronized replay, metrics, model cards, clear error messages. Browser must not invent result or calculate authoritative robot dynamics.

**Backend**: Python (FastAPI proposed), Gymnasium+Box2D, approved pretrained PPO/SAC models with versioned normalizers. Submitting a terrain creates a bounded job. Server simulates each policy with the same immutable terrain, captures per-step pose and outputs, then sends **compact state trajectories** for local client playback. This is simpler, more repeatable and less hosting-demanding than rendering live video or stepping one server RPC per animation frame.

- Client replays at a fixed simulation `dt`; renderer frame rate is independent. Models stop at different simulation steps; freeze final pose and label fail/goal/timecap.
- Server can queue or return progressive job status. Web API and worker quotas are Project code, not FX Platform core capabilities.
- GitHub Pages can host static UI, but **cannot run the Python simulator**. A separate Python deployment is needed for a public URL. Plan hosting after profiling; no provider, cost or response-time guarantee is made before testing.
- Offline fallback: downloadable repo launches frontend + backend locally, while the public README embeds **actual** recorded demonstrations.

## 3. Pillar I — Official benchmark first

### 3.1 Policies and external references

| Identifier | Type | Role in science | Role in browser |
|---|---|---|---|
| `ppo_standard` | Own PPO; standard training | Primary reference for proposed robust learning | Required controller |
| `ppo_robust` | Own PPO; observation/delay-randomized training | Primary proposed comparison | Required controller |
| `ppo_terrain` | Own PPO trained across a **predeclared procedural heightfield curriculum** | Tests learned terrain generalization (custom Track R only) | Strong candidate for visually meaningful hand-drawn comparisons |
| `zoo_reference` | Attributed RL Baselines3 Zoo checkpoint, PPO/SAC **after availability + license + preprocessing checks** | External anchored reference, not same-compute primary treatment | Candidate controller |
| `sac_standard` | Own SAC or legally usable reference | Distinct learning algorithm / architecture comparison | Preferred third **distinct** algorithm controller |
| `heuristic` | Official heuristic only if API and behavior are verified | Weak nonlearned diagnostic, not necessarily a fair champion | Optional educational comparison |

**Minimum web release gate:** ≥3 verified usable controllers/policies and **≥2 substantively distinct learning setups** (preferably ≥2 algorithms). PPO-Standard and PPO-Robust use the same algorithm but different training distributions; do not market them as different algorithms. If no compatible third controller exists, delay full comparison release rather than relabeling the same model.

### 3.2 Benchmark protocol (Track O)

- Freeze Gymnasium/Box2D/Python/SB3/PyTorch versions and source identity. Confirm Normal (`BipedalWalker-v3`) and Hardcore registered mode in installed version.
- Reproduce an externally documented checkpoint with its matching observation/return normalization. Third-party reference performance stays separately attributed.
- Independently train PPO Standard and PPO Robust, initially 5 seeds `[101..105]`. PPO network and update budget are matched; robust change is the announced randomized training distribution.
- For hand-drawn hills, **observation-noise/actuator-delay randomization alone may offer little terrain generalization**. After the first official methods are established, train a `ppo_terrain` candidate on controlled procedural slopes and ridges using the verified custom adapter; retain disjoint procedural generators/parameter bands for held-out evaluation. This is a distinct policy treatment, with its own training provenance.
- Evaluate Normal and Hardcore official unchanged with development seed set `[10000..10049]`; freeze model selection before final `[20000..20099]`. Numeric sets and count are preregistration **candidates** to adjust based on pilot throughput **before freezing**, not retroactive after seeing final.
- Baseline group vs robust group also evaluated on *Track R*, with calibrated observation noise, actuation delay and a separate, declared procedural-heightfield curriculum. A terrain-trained policy is evaluated on **unmodified** official Normal/Hardcore too, but custom training must never be misrepresented as official-environment-only learning.
- Report per-episode reward, goal, fall, timelimit, forward progress and action-effort proxy; separate evaluation of within-distribution and distribution-shift. Do not use `reward>=300` as a goal flag or `terminated` as equivalent to fall.
- Equal training environment steps alone do not imply equal wall-clock or energy cost. Report compute consumed. If robust effects are absent or negative, preserve them.

### 3.3 Scientific criteria

Success is **reproduced benchmark results, correctly matched comparisons and a faithful explanatory visualization**, NOT a requirement that PPO-Robust wins. Stable model weights and normalization must be frozen before incorporation in the public game. Save source/commit, config, seeds, package versions, checkpoint SHA and evidence linking Git to formal Platform runs.

## 4. Pillar II — User-drawn terrain comparison

### 4.1 Minimum demo screen

1. **Draw**: edit a continuous landscape with a mouse/touch stroke in a 2D view, with a fixed safe start and visible finish line; may edit control points after drawing. The curve preview is the **actual validated** geometry.
2. **Pick policies**: choose at least three pinned compatible policies; see source/training type in a small legend.
3. **Compare**: start an actual Box2D evaluation job for each policy, all using the exact `terrain_sha256` and bounded repeat seeds.
4. **Watch**: side-by-side synchronized 2D animation, controls for speed/pause/restart and timeline; show status when a walker falls or reaches goal.
5. **Understand**: leaderboard lists outcomes/progress/simulation steps/custom-scenario episode return and uncertainty when repeated trials exist. Winner labelled **according to specified scoring rule**, not generally optimal.
6. **Share**: export/import terrain JSON, screenshot/result summary. Replay manifests record versions, model SHAs and terrain SHA. Shared URL or session persistence are optional later.

### 4.2 What 'best controller for this terrain' actually means

Formalize ranking before showing badges, e.g. **first** completion proportion over configured trials, **second** median progress, **third** median simulation steps *among successful episodes*; choose an explicit tie rule. This is an application-level descriptive ranking, not a theoretical optimal controller.

A single run is a qualitative side-by-side. Repeated trials under controlled stochastic initial forces produce confidence/supporting uncertainty bands. Matching seed values alone may not produce identical physical starts unless the backend records and enforces equal initial states; test with actual initial-state fingerprint. The terrain hash must match exactly for all policies. Rollout source physics remains the same.

**No feedback leakage:** user-created maps are exploratory and cannot be treated as sealed official unseen Final examples after being used interactively. If the application later gathers maps for retraining, consent, versioning and new held-out maps are needed; not part of v1.

### 4.3 User experience and boundaries

Do not confuse user drawing arbitrary 2D shapes with full physics support. v1 supports landscape surfaces `h(x)` and hills. Later `terrain.geometry.v2` may add holes via disjoint segments, platforms as static polygons and other objects, separately tested for LiDAR/raycast, collisions, spawn and outcome semantics. Optional extruded 2.5D background is cosmetic; the actual physics remains 2D.

## 5. FX Platform allocation and project workflow

See `docs/REPOSITORY_AND_PLATFORM.md` for the authoritative boundary. The provided v8 spec defines `local_workflow`, `colab_workflow`, isolation, artifact collection and model registration; it **does not** establish that an active new Bipedal Project exists or that a Web deploy stage is supported.

| Workstream | FX Platform? | Mechanism |
|---|---|---|
| Pin env + real Box2D smoke | Yes | Project `local_workflow` |
| External benchmark replay and baselines | Yes | Project `local_workflow`; durable source/config evidence |
| PPO/SAC training, seed sweeps | Yes | Project `colab_workflow` logical jobs as resource appropriate |
| Formal offline evaluation and checkpoint registration | Yes | Project workflows / validated `model_register` |
| Terrain geometry conversion and adapter tests | Partly | Project source + `local_workflow`; public portable tests in GitHub |
| Browser editor / API / trace replay / deployment | No standard web stage | **External Project-owned app** deployed independently |
| Source/CI/docs/model cards/GitHub Releases | No | GitHub portable source and provenance |

Project release creation requires current registry, active source and environment evidence on the user's machine. Do not forge a `PROJECT Release` or insert unofficial stage fields. Distinguish git commit from Platform Release SHA, producer Run ID, checkpoint SHA and public model ID. The web server loads only approved exported model artifacts with a stable compatibility contract; it does not mount FX Platform protected paths.

### 5.1 4-Colab deployment

Independently train `(method,training_seed)` logical jobs after local and worker smoke. Record step throughput, CPU/GPU environment stepping vs policy update times before deciding T4 assignment. A GPU may not speed up Box2D stepping. Declare required dependencies/capabilities and checkpoint/normalizer artifact sizes before actual distribution. Preserve run receipts and worker timing under Platform contract, not in GitHub source history.

## 6. Execution gates (release order)

**Ordering principle:** A *tiny feasibility spike* for terrain goes first to retire integration risk. Full scientific development remains Pillar I; the browser/interaction comes after frozen policies. No reversed dependency on UI for training.

| Gate | Stage | Required delivery | Blocking pass condition |
|---|---|---|---|
| G0 | Identity/environment/Git | verified current Project registry and Release, independent private repo, pinned env plan | Current IDs are real, no Platform core edits, repo matches allowed source boundary |
| G1 | Custom terrain feasibility spike | valid input JSON → actual Box2D ground, independent terrain SHA, smoke traces | Repeated reset, lidar, 24D/4D, contacts, renderer, spawn, outcome and timeout checks PASS on real pinned runtime |
| G2 | Official baseline reproduction | documented Zoo or other published model (if compatible), heuristic diagnostics, episode CSV | Unmodified official env and correct normalizer, reproducible results, clear source credits |
| G3 | PPO training pilot | standard/robust minimal training, checkpoint save/reload, timing | Both policies run, stable IO, measurable runtime, eval independent of training RNG |
| G4 | Protocol freeze | tagged evaluation specification, budgets, stop rules and seed arrays | No Final results examined; configs, model selection and statistics defined |
| G5 | Full learning | matched PPO-Standard/Robust independent seeds, optional SAC | Checkpoints/normalizers/SHA/job evidence valid, failures accounted for |
| G6 | Official and stress evaluation | separately reported Track O/R CSV, plots, model cards, frozen model registry | Blind Final once per frozen protocol; independent recomputation of primary summaries; no favorable video-only selection |
| G7 | Browser engine | Python API, capped simulation service, terrain validator, per-step trace serialization | Same terrain yields identical fixture coordinates; model IO and outcome labels verified; repeat session isolation |
| G8 | Browser UI | drawing/editor, 3+ model selection, side-by-side replay, result explanation | Clean local browser test, synchronized simulated time, failure/timeout UI, no bogus rankings |
| G9 | Public portfolio release | hosted or documented local full-stack app, real clips, GitHub README/CI/release | Third-party clean-checkout reproduction, licensing, manifest/SHA, transparent limitations |

**Milestone fallback:** If official/robust comparison is valid but one model cannot meet usable browser performance, document failure and withhold the claimed full 3-model release, instead of silently substituting weak demonstration clips. If hosted Python runtime is unavailable, publish source + local run + genuine recorded videos, explicitly labelled as not a remotely executable demo.

## 7. GitHub work and publication

- **Start Git from day one, not a final dump.** Private remote first, public once real terrain smoke and reproducible README exist. GitHub can then show construction history, tests, investigations and negative results.
- Repository `Pagepsm/robust-bipedal-control` (candidate) is independent of old GRU project.
- Top-level README should answer in under 30 seconds: what the problem is, how AI controls joints, what is official vs user-drawn, and what viewer can try. Feature actual working side-by-side GIF only when produced. English summary, Japanese technical detail.
- Provide a linked quantitative evidence trail: model cards, normalizers, science config, training/eval seeds, source revision, environment tags, public aggregates/plots, rerun scripts. Avoid huge checkpoints or movies inside Git history; use releases or external host, checksum and redistribution/license clearance.
- Place API, UI, portable physics adapter in repo. **Do not copy FX Platform internals or the whole Platform specification to public GitHub.** The repo can document its abstract execution interfaces and experimental provenance without exposing private operational paths.
- CI: fast geometry/schema tests immediately; add headless Box2D smoke, backend tests, frontend build and browser end-to-end tests only after actual env dependency setup and evidence.
- GitHub private history becomes visible upon publication; no secrets or private Drive/worker/market-data paths in any commits.

## 8. Underestimated risks and mitigations

1. **Semi-private Gymnasium hook breaks:** version pin, precise source SHA, smoke/fallback Project-specific adapter. Don't modify core shared Platform code.
2. **Hand-drawn profile not physically passable:** distinguish numerical validity from physical feasibility. Let model fail honestly; warn for steep segments and out-of-training range.
3. **Action semantic mismatch:** active branch uses action sign and motor torque magnitude; verify installed source and checkpoint assumptions. Keep same source between train and infer.
4. **Different hidden observations across custom maps:** LiDAR must hit intended fixtures; no privileged future terrain map to just one agent. If extra map features are added, they become a separate model family and may invalidate a fair comparison.
5. **Scientific selection leakage:** freeze and separate official/robust/interactive scenarios; don't tune based on sealed Final or repeated demos then call it generalization proof.
6. **Hosting resource exhaustion:** bound payloads, job count/length, queue concurrency, results retention; test latency with actual model roster. A public game needs an operating budget.
7. **Model formats/deserialization:** load approved server-side SB3 artifacts only; never accept arbitrary client-provided serialized checkpoints.
8. **Browser versus simulator divergence:** emit server-authoritative step traces and replay positions, rather than re-running divergent physics in Canvas.
9. **Fair starts and stochastic physics:** compare exact terrain and recorded initial-state fingerprints, multiple paired trials, transparent interpretation of one-off runs.
10. **License/provenance:** attribute official environments and pretrained external checkpoints, verify redistributable weights, avoid copying third-party code blindly.
11. **Project scope explosion:** 2D heightfield first, official baseline first, no AR/3D/real-time networked multiplayer before v1.0.
12. **Training does not win:** a negative or mixed robustness result remains a publishable engineering experiment, but performance promises must not be invented.

## 9. Audit matrix and acceptance evidence

### Independent review 1 — compliance/source/quantities/contract

- Checked the provided FX Platform v8 Project/Platform responsibilities; this is a project plan, not a Release.
- Read actual upstream Gymnasium terrain reset/build, collision fixture, lidar, spawn, goal and action semantics; adopted original geometry domain and version guard.
- Official vs custom scoring is explicitly separated, as are train/dev/final and policy provenance.
- Numeric interface example 200 samples, 20 flat samples, spacing 14/30 m and base ground 400/30/4 m originates from inspected Gymnasium constants (must recheck pinned env). User-specific height/slope caps are provisional design parameters and **not** documented as upstream constraints.
- Adapter draft remains unverified with real Box2D, so no claim of working browser/AI physics is made.

### Independent review 2 — from first principles / failure analysis

- A heightfield editor cannot represent arbitrary 2D closed figures, tunnels or gaps. Scope reduced explicitly to continuous single-valued ground to avoid misleading physics.
- Browser does not need to reproduce Box2D; state-replay approach avoids uncontrolled physics divergence and reduces serving complexity.
- ≥3 validated, compatible controller checkpoints are required; PPO Standard vs Robust are distinct trained policies but not distinct algorithms.
- Same seed does not imply identical realized initial force/contact without verifying snapshots; use actual trace metadata and repeats.
- Hosting plan distinguishes static GitHub frontend and independently hosted Python backend; no 'GitHub Pages only' false deployment promise.
- No architectural contradiction identified in planned interfaces. **End-to-end feasibility still depends on real Gymnasium smoke, a working backend, available model weights and deployment profiling**.

## 10. Primary references

- Gymnasium official BipedalWalker environment: https://gymnasium.farama.org/environments/box2d/bipedal_walker/
- Source of robot, terrain and action semantics: https://github.com/Farama-Foundation/Gymnasium/blob/main/gymnasium/envs/box2d/bipedal_walker.py
- Independent override precedent: https://github.com/nicklashansen/newt/blob/main/tdmpc2/envs/tasks/bipedal_walker.py
- Stable-Baselines3: https://stable-baselines3.readthedocs.io/
- RL Baselines3 Zoo: https://github.com/DLR-RM/rl-baselines3-zoo
- Planck.js (deferred alternative browser 2D physics): https://piqnt.com/planck.js/
- GitHub Pages publication documentation: https://docs.github.com/en/pages
- Internal-only FX Platform provided spec: `FX_PLATFORM_EA_DEVELOPMENT_SPEC_v8.md` (do not publish its full text)