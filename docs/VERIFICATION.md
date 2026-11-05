# Verification and current limitations

> 2026年10月14日時点の設計・検証記録です。現在の制作物と実験結果は[作品紹介](../README.md)からご覧ください。

## Checked in the starter preparation (2026-10-14)

- Geometry conversion, canonicalization and SHA-256 validation: 16 Python unit tests passed in the earlier isolated starter verification.
- Syntax/static inspection completed for the provisional Box2D adapter.
- The project structure, benchmark separation, user-terrain format and platform boundaries were reviewed.

## Not yet demonstrated

- Real Gymnasium/Box2D dependency installation and custom environment smoke.
- Runtime fidelity of terrain collisions, LiDAR, leg contacts, reset behavior, replay and terminal labels.
- PPO/SAC training, external checkpoint compatibility, GPU/CPU performance, and model advantage.
- Browser simulator, hosted inference, independent user drawing and public deployment.

## GitHub initial commit status

This repository is initialized with the planned documents and prototype sources. A passing CI geometry test demonstrates only the dependency-free terrain contract, **not** a validated simulator or functional AI controller. Update this record with exact run/commit IDs and evidence after each executed gate.
