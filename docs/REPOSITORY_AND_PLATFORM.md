# GitHub and FX Platform — authority and responsibility

> 2026年10月14日時点の設計・検証記録です。現在の制作物と実験結果は[作品紹介](../README.md)からご覧ください。

## Repository policy

**Historical proposal (2026-10-14):** `Pagepsm/robust-bipedal-control` was the planned repository name, with Private visibility proposed until a working Box2D preview was available. This section records that earlier plan, not a current repository setting. **Current repository (checked 2026-11-05):** `Pagepsm/bipedal-control` is Public. The published code and demonstrated functionality are described in [README](../README.md).

- `main` holds reviewable, tested work; use feature branches and PRs for meaningful changes.
- Milestones: `v0.1` verified terrain adapter, `v0.2` official benchmark, `v0.3` frozen controllers and simulation service, `v0.4` browser editor/replay, `v1.0` publicly hosted portfolio demonstration.
- CI runs lightweight tests and static checks; long reinforcement-learning jobs remain outside CI.
- Publish real demonstrations, carefully labeled results, reproducibility instructions and model cards.
- Do not push secrets, internal FX Platform source or release artifacts, Drive internal paths, private evidence, large training outputs or unreleased model binaries into Git.

## FX Platform responsibility

Current supplied authoritative specification: `FX_PLATFORM_EA_DEVELOPMENT_SPEC_v8.md`, Platform 1.7.2; **live registry and active release are not verified**.

- Project-local physics, policies, ML code, configs and evaluation metrics stay in the Project.
- FX Platform handles supported `local_workflow`, `colab_workflow`, logical jobs and evidence/artifacts, and conditional model registration.
- Do not invent Platform stage names, create hidden local modifications to Platform, or assume that new Project identity/release exists.
- Python/Box2D remains the physical-simulation authority for web inference; browser renders genuine recorded trajectories. Hosting is an external delivery concern.
- Project lineage: Git commit → Project source hash → Platform release and run → checkpoint SHA → public model identifier. Public documentation must omit private paths and credentials.

## Open prerequisites

Confirm live runtime version, Project registration, applicable Python environment and dependency build. Pin Python/Gymnasium/Box2D/SB3 wheels before G1/G2. Verify model provenance and redistributability before any public release.
