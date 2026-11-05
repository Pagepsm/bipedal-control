# Evaluation Protocol — three separate domains

> 2026年10月14日時点の設計・検証記録です。現在の制作物と実験結果は[作品紹介](../README.md)からご覧ください。

## Track O: unmodified official benchmark

- Evaluate `BipedalWalker-v3` and `BipedalWalkerHardcore-v3` using **unmodified** Gymnasium environments, with exact environment and dependency versions recorded.
- Track baseline source/license, architecture, observation/action shape, preprocessors and normalizers, and checkpoint SHA.
- Candidate policies: attributed public Zoo baseline where compatible, PPO-Standard, PPO-Robust; optional SAC.
- Proposed training seeds: 101–105. Development evaluation seeds: 10000–10049. Final evaluation seeds: 20000–20099. Freeze before final testing after the runtime pilot.
- Record episode return, goal, fall, timeout, progress, and action statistics. `terminated` alone **does not mean success**; validate the terminal predicate in the installed runtime.

## Track R: robustness stress tests (not official)

- Independently examine observation noise, action delay, and approved procedural terrain perturbations.
- Standard and Robust PPO use controlled hyperparameters, architecture and environment-step budgets. Track wall-clock and compute resources separately.
- Separate new in-distribution seeds, shifted test intensities and genuine out-of-training-distribution scenarios.
- Independent **training seeds** provide statistical replication, while repeated evaluation rollouts estimate per-policy performance. Show uncertainty and failures.

## Track U: user-drawn terrain comparison (exploratory)

- Each frozen controller runs on the **same canonical terrain SHA** and the same authoritative Python/Box2D dynamics.
- A single run is an **illustrative comparison**, not evidence that a controller is generally best for a terrain class.
- Report goal, fall, time limit, progress and controls. For performance claims, run independent paired trials with fixed protocol and confidence intervals.
- Do not mix Track U results with official Gymnasium benchmark results.
- User maps that influenced design or model tuning are not held-out tests.

## Model compatibility conditions

For each controller, retain model ID, origin, license, training domain, environment build, observation/action contract, preprocessing/normalization, checkpoint SHA and deterministic/stochastic policy setting. Refuse incompatible models rather than implicitly adapting them.

## Evaluation integrity

Preserve raw per-episode records, exact configuration, git commit, release identity and software versions. Select models without peeking at Final outcomes. Both successes and failures remain visible.
