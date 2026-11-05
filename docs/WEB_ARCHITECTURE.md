# Browser application architecture — Draw / Simulate / Compare

> 2026年10月14日時点の設計・検証記録です。現在の制作物と実験結果は[作品紹介](../README.md)からご覧ください。

## Decision: Python Box2D is authoritative in v1

**Browser:** TypeScript + a lightweight SVG/Canvas editor; mouse/touch drawing, full-course overview + zoomed physically scaled profile (to avoid misleading slope depiction), terrain visual validation, controller selection, progress indicators, timeline, side-by-side replay, result table. Frontend framework (React or plain TS) is an implementation choice.

**Backend:** Python API (candidate: FastAPI) with Gymnasium + PyBox2D + loaded PPO/other policies. Runs authoritative deterministic simulation per model, records robot pose/joints/contacts, action, cumulative reward and termination cause. Sends compressed *trajectory data*, not a continuous video stream, to browser for synchronized local replay. This keeps the physical source of truth consistent with the scientific evaluations and decouples rendering FPS from stepping.

**Job pattern:** Submit immutable `terrain_id` and selected model IDs -> server validates limits -> enqueues a short, capped simulation bundle -> runs model A/B/C under identical terrain and controlled initial conditions -> returns trajectory bundles and metrics -> client replays at configurable speed. Optional live streaming only after this works reliably.

**Why not JS Box2D immediately?** A separate browser physics implementation would require a port of the same articulated walker (mass/inertia, hip/knee joints, contacts, motors, lidar and reset) and action/observation conversion. Differences could invalidate the benchmark-trained policy's claimed performance. Future alternative: validated Planck.js or WASM port, with step-by-step parity trials on identical state/action traces; until then, **never state numerical parity**.

**Hosting:** GitHub Pages can host a static frontend but **cannot run this Python/Box2D backend**. A separately deployed Python process is needed for public interactive access; record provider, resource quotas, startup time and cost once chosen. If no public Python hosting is available, offer a local full-stack run command plus a public prerecorded demo, not a misleading static page that pretends to execute real physics.

## Concrete logical API (design, not deployed)

- `GET /api/v1/models`: IDs, training method, policy SHA, normalizer SHA, compatible env schema/version, licence.
- `POST /api/v1/terrains/validate`: `terrain.heightfield.v1` -> normalized, checked canonical geometry; returns immutable `terrain_sha256`, preview, warnings.
- `POST /api/v1/evaluations`: immutable terrain + model IDs + repeat count + repeat seeds; responds with job ID.
- `GET /api/v1/evaluations/{job_id}`: state, progress, error code, metric pointers.
- `GET /api/v1/evaluations/{job_id}/traces`: bounded output of authoritative state snapshots and per-episode metrics.

No user-supplied Python/scripts/checkpoints are accepted. Do not evaluate user-imported arbitrary pickled models on a public server.

## Fair comparison mechanics

- Every model receives identical `terrain_sha256` and world geometry; attach it to each trace. Freeze environment version and observation preprocessing.
- Use identical initial-condition parameters where supported, and avoid pretending equal seed numbers guarantee precisely equal stochastic events. Record actual initial-state fingerprints and terrain coordinates.
- Replay visualization is synchronized by simulation step and consistent `dt` (not server completion time). If policies terminate early, freeze the final marker at fall/goal and report truncated duration.
- Offer a clear per-terrain comparison: reached goal?, progress, episode return (custom-only), elapsed simulation steps, falls, action-effort proxy. 'Best' means **under a disclosed ranking rule**, not universal suitability.
- For repeated stochastic trials, show win frequencies / spread and distinguish a single demonstrative run from statistically replicated results.
- Custom user maps are **demo/exploratory data** and cannot silently be used as formal unseen Final OOS after viewing results; maintain sealed science evaluation sets separately.

## Operational constraints

- Enforce finite numeric payload and JSON schema, vertex/samples cap, height/slope cap, size cap, deterministic terrain hash.
- Limit model count, concurrent sessions, rollouts, steps, CPU wall-clock, output trace size and retention. Place a bounded queue and cancellation/expiration behavior between web inputs and Python simulation.
- Isolate session objects and seeds; a model inference error must not terminate the whole server. Instrument CPU/RAM, latency and request failure rates.
- No uploads of external code or untrusted binary checkpoints; only server-side approved, hash-pinned policy files.
- Record library versions, model IDs and scenario hashes in downloadable result summaries; user maps should not be retained indefinitely without clear consent.