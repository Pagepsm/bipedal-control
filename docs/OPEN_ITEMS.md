# Open integration items

> 2026年10月14日時点の未解決項目を保存した記録です。公開状態や実装状況は当時の計画から変わっています。現在の収録内容は[作品紹介](../README.md)で確認してください。

1. **FX runtime identity:** actual Project ID, current Platform/Project releases, active pointer, registered Python environments and cache/wheel evidence remain unverified.
2. **Real Box2D adapter:** `custom_bipedal_env.py` is provisional. Fix upstream version, run an actual integration smoke and compare physics, raycasts, resets, contacts and spawn/goal semantics.
3. **Metrics:** independently validate success/fall/timeout classification, deterministic resets, action ranges, and recorded trajectory equality.
4. **Learning:** no trained PPO, SAC or downloaded benchmark checkpoints are included. Validate baseline versions, model license and normalizer state.
5. **Computation:** measure CPU/GPU execution throughput and compute budgets; freeze model selection and Final evaluation protocol before running Final tests.
6. **Web:** implement editor, canonicalization, bounded simulation jobs, model execution and replay; evaluate hosting costs and concurrent CPU load.
7. **Terrain features:** v1 supports a single-valued heightfield only. Gaps, overhangs, true vertical cliffs, bridges and complex closed 2D objects remain out of scope.
8. **Public claims:** never label prototype tests as learned-controller performance. Verify licensing and all history before switching GitHub Public.
